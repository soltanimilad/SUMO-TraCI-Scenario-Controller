import subprocess
import os
import sys
import traci
import xml.etree.ElementTree as ET # New: Required for parsing XML log files

# --- Configuration ---
# Set the base directory name for logs.
LOG_BASE_DIR = "scenario_logs" 
# Use the default SUMO executable name
SUMO_BINARY = "sumo"

def find_sumo_and_add_path():
    """
    Checks if $SUMO_HOME is set and adds the tools directory to sys.path.
    If not, attempts to use the SUMO binary name for execution.
    """
    if 'SUMO_HOME' in os.environ:
        print("✅ SUMO_HOME found and 'tools' path added to sys.path.")
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
        return True
    else:
        print("⚠️ SUMO_HOME environment variable not set.")
        print("Please ensure SUMO is installed and added to your system PATH.")
        return False

def get_user_inputs():
    """Gathers user inputs for the map and trip configuration."""
    print("\n--- SUMO Pipeline Setup ---")
    print("NOTE: You must have a working SUMO installation to run this.")
    
    # Bounding Box Coordinates (Dallas area from your last run)
    min_lat = input("Enter Minimum Latitude (min_lat) [32.67132]: ") or "32.67132"
    min_lon = input("Enter Minimum Longitude (min_lon) [-96.89014]: ") or "-96.89014"
    max_lat = input("Enter Maximum Latitude (max_lat) [32.71892]: ") or "32.71892"
    max_lon = input("Enter Maximum Longitude (max_lon) [-96.78835]: ") or "-96.78835"
    bbox = (min_lat, min_lon, max_lat, max_lon)
    
    filename = input("Enter Base Filename (e.g., 'California'): ") or "california_test"
    end_time = input("Enter Trip End Time (-e, e.g., 36000 seconds) [Default: 36000]: ") or "36000"
    period = input("Enter Trip Generation Period (-p, e.g., 10 seconds) [Default: 10]: ") or "10"
    
    print(f"\nConfiguration: Filename='{filename}'")
    print(f"BBOX=({', '.join(bbox)})")
    print(f"Trip Parameters: End Time (-e)={end_time}, Period (-p)={period}")
    
    return filename, bbox, end_time, period

def run_command(command, description):
    """Executes a command and checks for success."""
    print(f"\n▶️ Running: {' '.join(command)}")
    try:
        # Use subprocess.run for simple command execution
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Finished successfully.")
        # Optionally print useful output, but keep it concise
        if result.stdout and len(result.stdout) < 100:
             print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}.")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Ensure '{command[0]}' is in your PATH.")
        return False

def creating_required_files(filename, bbox, end_time, period):
    """
    Downloads OSM data and converts it into SUMO network files.
    """
    if not find_sumo_and_add_path():
        return False
        
    print("\n\n#############################################")
    print("# Starting OSM Download and SUMO Conversion #")
    print("#############################################")

    # We assume 'filename.osm' is present from a prior run or manual download.
    osm_file = f"{filename}.osm"
    if not os.path.exists(osm_file):
        print(f"⚠️ Warning: '{osm_file}' not found. Continuing if files exist, otherwise Netconvert will fail.")
    
    # 1. Netconvert (Network generation)
    net_file = f"{filename}.net.xml"
    if not run_command(["netconvert", "--osm-files", osm_file, "-o", net_file], "Netconvert"):
        return False

    # 2. Polyconvert (Polygons for GUI backgrounds)
    # Assumes standard path to typemap file (adjust if necessary)
    if 'SUMO_HOME' in os.environ:
        typemap_path = os.path.join(os.environ['SUMO_HOME'], 'data', 'typemap', 'osmPolyconvert.typ.xml')
    else:
        # Fallback path (may need manual adjustment)
        typemap_path = "/usr/share/sumo/data/typemap/osmPolyconvert.typ.xml" 
    
    poly_file = f"{filename}.poly.xml"
    if not run_command(["polyconvert", "--osm-files", osm_file, "--type-file", typemap_path, "-o", poly_file], "Polyconvert"):
        return False

    # 3. RandomTrips Generation
    trip_file = f"{filename}.trip.xml"
    # Use python3 to call randomTrips.py from tools
    if 'SUMO_HOME' not in os.environ:
        print("❌ Cannot run randomTrips.py: SUMO_HOME not set.")
        return False
        
    if not run_command([
        "python3", os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py'),
        "-n", net_file, "-o", trip_file, "-e", end_time, "-p", period, "--validate"
    ], "randomTrips"):
        return False

    # 4. Duarouter (Route calculation)
    route_file = f"{filename}.rou.xml"
    if not run_command(["duarouter", "-n", net_file, "-t", trip_file, "-o", route_file, "--ignore-errors"], "Duarouter"):
        return False
        
    print("\nPipeline File Generation Complete!")
    return True

def generate_sumo_config(filename, log_path, scenario_label, end_time_int):
    """Creates a .sumocfg file with dynamic log paths and simulation time."""
    config_file = f"{filename}_{scenario_label}.sumocfg"
    
    # Ensure the specific log directory exists
    os.makedirs(log_path, exist_ok=True)
    
    # Define log files inside the specific scenario log folder
    summary_output = os.path.join(log_path, "summary_output.xml")
    tripinfo_output = os.path.join(log_path, "tripinfo_output.xml")
    
    config_content = f"""
<configuration>
    <input>
        <net-file value="{filename}.net.xml"/>
        <route-files value="{filename}.rou.xml"/>
        <additional-files value="{filename}.poly.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{end_time_int}"/>
    </time>
    <output>
        <summary-output value="{summary_output}"/>
        <tripinfo-output value="{tripinfo_output}"/>
    </output>
</configuration>
    """
    with open(config_file, 'w') as f:
        f.write(config_content.strip())
        
    print(f"\n✅ Config file '{config_file}' created for '{scenario_label}' scenario.")
    return config_file, log_path

def run_unblocked_simulation(filename, end_time_int):
    """Runs the baseline simulation without TraCI control."""
    log_path = os.path.join(LOG_BASE_DIR, filename, "unblocked")
    # Pass end_time_int explicitly
    config_file, _ = generate_sumo_config(filename, log_path, "unblocked", end_time_int) 
    
    print("\n--- Starting SCENARIO 1: UNBLOCKED BASELINE (TraCI NOT Connected) ---")
    print(f"All logs will be saved to: {log_path}")
    
    # Command to run SUMO headless
    command = [SUMO_BINARY, "-c", config_file, "--step-length", "1", "--quit-on-end", "--no-warnings", "--no-step-log"]
    
    try:
        # Use subprocess.run to execute the simulation
        subprocess.run(command, check=True, capture_output=True)
        print("\n✅ Baseline Simulation Complete.")
        print(f"Results saved successfully to: {log_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Baseline Simulation.")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: SUMO binary ('{SUMO_BINARY}') not found. Ensure it is in your PATH.")
        return False


def run_blocked_simulation_traci(filename, end_time_int):
    """Runs the simulation with TraCI, blocking a lane dynamically, without logging the event."""
    
    print("\n--- Starting SCENARIO 2: TRACI CONTROLLED LANE BLOCK (TraCI Connected) ---")

    # Get blocking parameters from the user
    try:
        # Note: Edge IDs can be found by opening the .net.xml in a text editor or using SUMO-GUI.
        edge_id = input("Enter Edge ID to block (e.g., 'E1'): ")
        lane_index = int(input("Enter Lane Index to block (e.g., 0 for rightmost lane): "))
        start_time = int(input(f"Enter Simulation Time (sec) to start block (max {end_time_int}): "))
        duration = int(input("Enter Duration (sec) for the block: "))
    except ValueError:
        print("❌ Invalid input for time or index. Aborting TraCI run.")
        return False

    block_end_time = start_time + duration
    
    # Setup logging directory and config file
    log_path = os.path.join(LOG_BASE_DIR, filename, "blocked")
    # Pass end_time_int explicitly
    config_file, _ = generate_sumo_config(filename, log_path, "blocked", end_time_int) 
    
    # The only pre-simulation message confirming the action scheduling
    print(f"\n🚧 Scheduled Block: Edge '{edge_id}', Lane Index {lane_index}")
    print(f"   Action: Block at t={start_time}, Unblock at t={block_end_time}")
    print(f"   Logs saved to: {log_path} (Output logs will contain NO explicit reference to blocking.)")

    # Start SUMO via TraCI
    sumo_cmd = [SUMO_BINARY, "-c", config_file, "--step-length", "1", "--no-warnings", "--quit-on-end"]
    
    try:
        # The TraCI library handles launching and connecting
        traci.start(sumo_cmd)
        step = 0
        lane_to_block = f"{edge_id}_{lane_index}"
        is_blocked = False
        
        while traci.simulation.getMinExpectedNumber() > 0 or step < end_time_int:
            # 1. TraCI Step
            traci.simulationStep()
            
            # 2. Blocking Logic (Silence all console output here)
            if step == start_time and not is_blocked:
                # Block the lane by setting the allowed vehicle classes to none (empty list)
                traci.lane.setAllowed(lane_to_block, [])
                is_blocked = True
            
            # 3. Unblocking Logic (Silence all console output here)
            if step == block_end_time and is_blocked:
                # Unblock the lane by resetting the allowed vehicle classes (standard 'passenger')
                traci.lane.setAllowed(lane_to_block, ['passenger'])
                is_blocked = False
            
            # Optional Status Update (Keeping this for general progress indication)
            if step % 5000 == 0 and step > 0:
                active_vehicles = traci.simulation.getMinExpectedNumber()
                print(f"TraCI Step {step} | Active Vehicles: {active_vehicles} | Blocked: {is_blocked}")
                
            step += 1
            
        traci.close()
        print("\n✅ TraCI Simulation Complete.")
        print(f"Results saved successfully to: {log_path}")
        return True

    except traci.TraCIException as e:
        print(f"❌ TraCI Error: Could not connect to SUMO or invalid command used: {e}")
        print("Ensure the SUMO binary is correctly configured.")
        return False
    except FileNotFoundError:
        print(f"❌ Error: SUMO binary ('{SUMO_BINARY}') not found. Ensure it is in your PATH.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False


# --- New Comparison Function ---

def extract_metrics(filepath):
    """Parses a tripinfo XML file and returns key aggregated metrics."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: Log file not found at {filepath}")
        return None
        
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        total_trips = 0
        total_travel_time = 0.0 # Sum of duration
        total_route_length = 0.0 # Sum of routeLength
        
        for trip in root.findall('tripinfo'):
            total_trips += 1
            # SUMO output attributes are strings, need conversion
            try:
                duration = float(trip.get('duration'))
                route_length = float(trip.get('routeLength'))
                total_travel_time += duration
                total_route_length += route_length
            except (TypeError, ValueError):
                # Ignore trips that might be corrupted or lack data
                continue

        if total_trips == 0:
            return None

        # Calculate averages
        avg_travel_time = total_travel_time / total_trips
        # Speed in m/s (Total Distance / Total Time)
        avg_speed_mps = total_route_length / total_travel_time if total_travel_time > 0 else 0.0

        return {
            "total_trips": total_trips,
            "avg_travel_time": avg_travel_time,
            "avg_speed_mps": avg_speed_mps
        }

    except ET.ParseError as e:
        print(f"❌ Error parsing XML file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ An error occurred during metric extraction: {e}")
        return None


def compare_simulation_results(filename):
    """Compares metrics from the unblocked and blocked scenarios."""
    
    print("\n" + "="*50)
    print("STARTING SCENARIO COMPARISON REPORT")
    print("="*50)
    
    unblocked_path = os.path.join(LOG_BASE_DIR, filename, "unblocked", "tripinfo_output.xml")
    blocked_path = os.path.join(LOG_BASE_DIR, filename, "blocked", "tripinfo_output.xml")

    # Extract metrics
    metrics_unblocked = extract_metrics(unblocked_path)
    metrics_blocked = extract_metrics(blocked_path)
    
    if not metrics_unblocked or not metrics_blocked:
        print("❌ Cannot perform comparison: one or both log files could not be read or were empty.")
        return

    # Helper for comparison and percentage calculation
    def get_diff(blocked_val, unblocked_val):
        if unblocked_val == 0:
            return "N/A"
        diff = blocked_val - unblocked_val
        percent = (diff / unblocked_val) * 100
        # Format difference and percentage change
        return f"{diff:+.2f} ({percent:+.2f}%)"

    print(f"Comparison Report for Map: {filename}")
    print("-" * 50)
    
    # 1. Trips Completed
    print(f"Total Trips Completed: ")
    print(f"  Unblocked: {metrics_unblocked['total_trips']}")
    print(f"  Blocked:   {metrics_blocked['total_trips']}")
    
    # 2. Average Travel Time
    print(f"\nAverage Trip Travel Time (sec): ")
    print(f"  Unblocked: {metrics_unblocked['avg_travel_time']:.2f}")
    print(f"  Blocked:   {metrics_blocked['avg_travel_time']:.2f}")
    
    diff_time = get_diff(metrics_blocked['avg_travel_time'], metrics_unblocked['avg_travel_time'])
    print(f"  Difference: {diff_time} (A positive change means more time)")
    
    # 3. Average Speed
    print(f"\nAverage Network Speed (m/s): ")
    print(f"  Unblocked: {metrics_unblocked['avg_speed_mps']:.2f}")
    print(f"  Blocked:   {metrics_blocked['avg_speed_mps']:.2f}")

    diff_speed = get_diff(metrics_blocked['avg_speed_mps'], metrics_unblocked['avg_speed_mps'])
    print(f"  Difference: {diff_speed} (A negative change means slower speed)")
    
    print("-" * 50)
    print("Summary:")
    print("A positive difference in Travel Time or a negative difference in Speed indicates the lane blockage caused **congestion**.")


# --- Main Execution Flow ---
if __name__ == "__main__":
    
    # 1. Get Initial Setup Inputs
    try:
        filename, bbox, end_time_str, period = get_user_inputs()
        end_time_int = int(end_time_str) # Convert to integer now
    except Exception:
        print("\n❌ Failed to parse inputs. Exiting.")
        sys.exit(1)
        
    # 2. Generate all required input files (if not already done)
    if not creating_required_files(filename, bbox, end_time_str, period):
        print("\nFATAL ERROR: Could not generate all required SUMO input files. Check console output for details.")
        sys.exit(1)

    # 3. Run Unblocked Simulation (Baseline)
    if not run_unblocked_simulation(filename, end_time_int):
        print("\nBaseline simulation failed. Skipping TraCI run.")
        sys.exit(1)

    # 4. Run Blocked Simulation (TraCI Control)
    if not run_blocked_simulation_traci(filename, end_time_int):
         print("\nBlocked simulation failed. Skipping comparison.")
         sys.exit(1)
         
    # 5. Compare Results
    compare_simulation_results(filename)

    print("\nAll scenarios and analysis complete.")
    print(f"Final logs are located under the '{LOG_BASE_DIR}/{filename}/' directory.")
