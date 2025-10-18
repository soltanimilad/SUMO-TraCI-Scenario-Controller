import subprocess
import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import platform
import glob # New import for file pattern matching

# --- Configuration ---
LOG_BASE_DIR = "scenario_logs" 
SUMO_BINARY = "sumo" 

def find_sumo_and_add_path():
    """Checks if $SUMO_HOME is set and adds the tools directory to sys.path."""
    if 'SUMO_HOME' in os.environ:
        print("✅ SUMO_HOME found and 'tools' path added to sys.path.")
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        if tools not in sys.path:
            sys.path.append(tools)
        return True
    else:
        print("⚠️ SUMO_HOME environment variable not set.")
        print("Please ensure SUMO is installed and added to your system PATH.")
        return False

def get_user_inputs():
    """
    Gathers user inputs for the map and trip configuration.
    Prioritizes automatic detection of a single existing .osm file.
    """
    print("\n--- SUMO Pipeline Setup ---")
    print("NOTE: You must have a working SUMO installation to run this.")
    
    # 1. Check for existing .osm files
    osm_files = glob.glob("*.osm")
    
    # Default Coordinates (used if no file is detected or as prompt defaults)
    default_filename = "Washington"
    dc_min_lat = "38.8920"
    dc_min_lon = "-77.0420"
    dc_max_lat = "38.9050"
    dc_max_lon = "-77.0200"

    # --- AUTO-DETECTION LOGIC ---
    if len(osm_files) == 1:
        # Found exactly one file, use it automatically
        osm_file_name = osm_files[0]
        filename = os.path.splitext(osm_file_name)[0]
        bbox = (dc_min_lat, dc_min_lon, dc_max_lat, dc_max_lon) # Placeholder, download will be skipped
        
        print("-" * 50)
        print(f"🌟 Found single OSM file: '{osm_file_name}'.")
        print(f"    Auto-configuring pipeline with Base Filename: '{filename}'")
        print("-" * 50)
        
    else:
        # Prompt user if zero or multiple files found
        if len(osm_files) == 0:
            print("⚠️ No existing .osm files found. Proceeding with manual download via BBOX.")
        else:
            print(f"⚠️ Found {len(osm_files)} .osm files. Cannot auto-select. Proceeding with manual BBOX/filename input.")
            
        min_lat = input(f"Enter Minimum Latitude (min_lat) [Default: {dc_min_lat} (D.C.)]: ") or dc_min_lat
        min_lon = input(f"Enter Minimum Longitude (min_lon) [Default: {dc_min_lon} (D.C.)]: ") or dc_min_lon
        max_lat = input(f"Enter Maximum Latitude (max_lat) [Default: {dc_max_lat} (D.C.)]: ") or dc_max_lat
        max_lon = input(f"Enter Maximum Longitude (max_lon) [Default: {dc_max_lon} (D.C.)]: ") or dc_max_lon
        bbox = (min_lat, min_lon, max_lat, max_lon)
        
        filename = input(f"Enter Base Filename [Default: {default_filename}]: ") or default_filename
        
    # --- Shared Trip Prompts ---
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
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Finished successfully.")
        if result.stdout and len(result.stdout.strip()) < 100 and result.stdout.strip():
             print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}.")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Ensure '{command[0]}' is in your system PATH.")
        return False

def download_osm_file(filename, bbox):
    """Downloads OSM data using the Overpass API based on the bounding box (includes existence check)."""
    osm_file = f"{filename}.osm"
    
    if os.path.exists(osm_file):
        print(f"✅ OSM file '{osm_file}' already exists. Skipping download.")
        return True

    print(f"\n🌐 Downloading OSM data for BBOX: {', '.join(bbox)}")
    
    min_lat, min_lon, max_lat, max_lon = bbox
    overpass_query = f"""
        [out:xml][timeout:180];
        (
          node({min_lat},{min_lon},{max_lat},{max_lon});
          way({min_lat},{min_lon},{max_lat},{max_lon});
          relation({min_lat},{min_lon},{max_lat},{max_lon});
        );
        (._;>;);
        out meta;
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    try:
        data = overpass_query.encode('utf-8')
        req = urllib.request.Request(overpass_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        with urllib.request.urlopen(req) as response:
            with open(osm_file, 'wb') as f:
                f.write(response.read())
        
        print(f"✅ Successfully downloaded OSM data to '{osm_file}'.")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading OSM file from Overpass API: {e}")
        print("   Check your internet connection or the area size.")
        return False


def creating_required_files(filename, bbox, end_time, period):
    """Downloads OSM data (if needed) and converts it into SUMO network files."""
    if not find_sumo_and_add_path():
        return False
        
    print("\n\n#############################################")
    print("# Starting OSM Download and SUMO Conversion #")
    print("#############################################")
    
    # 1. Download OSM file (includes existence check)
    if not download_osm_file(filename, bbox):
        return False
        
    osm_file = f"{filename}.osm"
    
    # 2. Netconvert (Network generation)
    net_file = f"{filename}.net.xml"
    if not run_command(["netconvert", "--osm-files", osm_file, "-o", net_file], "Netconvert"):
        return False

    # 3. Polyconvert (Polygons for GUI backgrounds)
    typemap_path = os.path.join(os.environ.get('SUMO_HOME', ''), 'data', 'typemap', 'osmPolyconvert.typ.xml')
    if not os.path.exists(typemap_path):
         print(f"⚠️ Warning: Typemap not found at default path. Using generic fallback.")
         typemap_path = os.path.join("/usr/share/sumo/data/typemap", 'osmPolyconvert.typ.xml')
    
    poly_file = f"{filename}.poly.xml"
    if not run_command(["polyconvert", "--osm-files", osm_file, "--type-file", typemap_path, "-o", poly_file], "Polyconvert"):
        return False

    # 4. RandomTrips Generation
    trip_file = f"{filename}.trip.xml"
    if 'SUMO_HOME' not in os.environ:
        print("❌ Cannot run randomTrips.py: SUMO_HOME not set.")
        return False
        
    random_trips_script = os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py')
    
    if not run_command([
        "python3", random_trips_script,
        "-n", net_file, "-o", trip_file, "-e", end_time, "-p", period, "--validate"
    ], "randomTrips"):
        return False

    # 5. Duarouter (Route calculation)
    route_file = f"{filename}.rou.xml"
    if not run_command(["duarouter", "-n", net_file, "-t", trip_file, "-o", route_file, "--ignore-errors"], "Duarouter"):
        return False
        
    print("\nPipeline File Generation Complete!")
    return True

def suggest_blocking_edge(filename):
    """
    Parses the SUMO .net.xml file and lists major road edges.
    Strips the trailing index (like '_0') from edge IDs for safe TraCI use.
    """
    net_file = f"{filename}.net.xml"
    
    if not os.path.exists(net_file):
        print(f"❌ Error: Network file '{net_file}' not found. Cannot suggest edges.")
        return None

    MAJOR_ROAD_KEYWORDS = [
        "motorway", "trunk", "primary", "secondary", "link",
    ]
    
    major_edge_ids = set()
    
    try:
        tree = ET.parse(net_file)
        root = tree.getroot()
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'): continue
            
            edge_function = edge.get('function', '').lower()
            
            is_major = False
            road_type = edge_function 
            for lane in edge.findall('lane'):
                lane_type = lane.get('type', '').lower()
                if any(keyword in lane_type for keyword in MAJOR_ROAD_KEYWORDS):
                    is_major = True
                    road_type = lane_type
                    break
            
            if is_major or any(keyword in edge_function for keyword in MAJOR_ROAD_KEYWORDS):
                
                # Strip the _index part if it exists (e.g., 10013807254_0 -> 10013807254)
                clean_edge_id = edge_id
                if "_" in edge_id and not edge_id.startswith("-"):
                    parts = edge_id.rsplit('_', 1)
                    try:
                        int(parts[-1])
                        clean_edge_id = parts[0]
                    except ValueError:
                        pass

                major_edge_ids.add((clean_edge_id, road_type if road_type else edge_function))
        
        return sorted(list(major_edge_ids))

    except ET.ParseError as e:
        print(f"❌ XML Parsing Error: Could not read {net_file}: {e}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred while parsing the network file: {e}")
        return None

def generate_sumo_config(filename, log_path, scenario_label, end_time_int):
    """Creates a .sumocfg file with dynamic log paths and simulation time."""
    config_file = f"{filename}_{scenario_label}.sumocfg"
    
    os.makedirs(log_path, exist_ok=True)
    
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
    config_file, _ = generate_sumo_config(filename, log_path, "unblocked", end_time_int) 
    
    print("\n--- Starting SCENARIO 1: UNBLOCKED BASELINE (TraCI NOT Connected) ---")
    print(f"All logs will be saved to: {log_path}")
    
    command = [SUMO_BINARY, "-c", config_file, "--step-length", "1", "--quit-on-end", "--no-warnings", "--no-step-log"]
    
    try:
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
    """Runs the simulation with TraCI, blocking a lane dynamically."""
    try:
        import traci
    except ImportError:
        print("❌ Fatal Error: Could not import 'traci'. Ensure SUMO_HOME is set and the 'tools' folder is accessible.")
        return False

    print("\n--- Starting SCENARIO 2: TRACI CONTROLLED LANE BLOCK (TraCI Connected) ---")

    edge_id = input("Enter a CLEAN Edge ID to block (e.g., '123456'): ")
    try:
        lane_index = int(input("Enter Lane Index to block (e.g., 0 for rightmost lane): "))
        start_time = int(input(f"Enter Simulation Time (sec) to start block (max {end_time_int}): "))
        duration = int(input("Enter Duration (sec) for the block: "))
    except ValueError:
        print("❌ Invalid input for time or index. Aborting TraCI run.")
        return False
    
    block_end_time = start_time + duration
    
    log_path = os.path.join(LOG_BASE_DIR, filename, "blocked")
    config_file, _ = generate_sumo_config(filename, log_path, "blocked", end_time_int) 
    
    # TraCI requires the Lane ID format: EdgeID_LaneIndex (e.g., "123456_0")
    lane_to_block = f"{edge_id}_{lane_index}" 

    print(f"\n🚧 Scheduled Block: Edge '{edge_id}', Lane Index {lane_index}")
    print(f"   Target Lane ID: {lane_to_block}")
    print(f"   Action: Block at t={start_time}, Unblock at t={block_end_time}")
    print(f"   Logs saved to: {log_path}")

    sumo_cmd = [SUMO_BINARY, "-c", config_file, "--step-length", "1", "--no-warnings", "--quit-on-end"]
    
    try:
        traci.start(sumo_cmd)
        step = 0
        is_blocked = False
        
        while traci.simulation.getMinExpectedNumber() > 0 or step < end_time_int:
            traci.simulationStep()
            
            if step == start_time and not is_blocked:
                try:
                    traci.lane.setAllowed(lane_to_block, [])
                    print(f"-> Lane {lane_to_block} BLOCKED at step {step}.")
                    is_blocked = True
                except traci.exceptions.TraCIException as e:
                    print(f"❌ TraCI Error: Could not block lane {lane_to_block}. Check Edge ID and Lane Index.")
                    print(f"Error detail: {e}")
                    traci.close()
                    return False
            
            if step == block_end_time and is_blocked:
                traci.lane.setAllowed(lane_to_block, ['passenger'])
                print(f"-> Lane {lane_to_block} UNBLOCKED at step {step}.")
                is_blocked = False
            
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


# --- Comparison Functions (Unchanged) ---

def extract_metrics(filepath):
    """Parses a tripinfo XML file and returns key aggregated metrics."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: Log file not found at {filepath}")
        return None
        
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        total_trips = 0
        total_travel_time = 0.0
        total_route_length = 0.0
        
        for trip in root.findall('tripinfo'):
            total_trips += 1
            try:
                duration = float(trip.get('duration'))
                route_length = float(trip.get('routeLength'))
                total_travel_time += duration
                total_route_length += route_length
            except (TypeError, ValueError):
                continue

        if total_trips == 0:
            return None

        avg_travel_time = total_travel_time / total_trips
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

    metrics_unblocked = extract_metrics(unblocked_path)
    metrics_blocked = extract_metrics(blocked_path)
    
    if not metrics_unblocked or not metrics_blocked:
        print("❌ Cannot perform comparison: one or both log files could not be read or were empty.")
        return

    def get_diff(blocked_val, unblocked_val):
        if unblocked_val == 0:
            return "N/A"
        diff = blocked_val - unblocked_val
        percent = (diff / unblocked_val) * 100
        return f"{diff:+.2f} ({percent:+.2f}%)"

    print(f"Comparison Report for Map: {filename}")
    print("-" * 50)
    
    print(f"Total Trips Completed: ")
    print(f"  Unblocked: {metrics_unblocked['total_trips']}")
    print(f"  Blocked:   {metrics_blocked['total_trips']}")
    
    print(f"\nAverage Trip Travel Time (sec): ")
    print(f"  Unblocked: {metrics_unblocked['avg_travel_time']:.2f}")
    print(f"  Blocked:   {metrics_blocked['avg_travel_time']:.2f}")
    
    diff_time = get_diff(metrics_blocked['avg_travel_time'], metrics_unblocked['avg_travel_time'])
    print(f"  Difference: {diff_time} (A positive change means **more time**)")
    
    print(f"\nAverage Network Speed (m/s): ")
    print(f"  Unblocked: {metrics_unblocked['avg_speed_mps']:.2f}")
    print(f"  Blocked:   {metrics_blocked['avg_speed_mps']:.2f}")

    diff_speed = get_diff(metrics_blocked['avg_speed_mps'], metrics_unblocked['avg_travel_time'])
    print(f"  Difference: {diff_speed} (A negative change means **slower speed**)")
    
    print("-" * 50)
    print("Summary:")
    print("A positive difference in Travel Time or a negative difference in Speed indicates the lane blockage caused **congestion**.")


# --- Main Execution Flow ---
if __name__ == "__main__":
    
    try:
        filename, bbox, end_time_str, period = get_user_inputs()
        end_time_int = int(end_time_str)
    except Exception:
        print("\n❌ Failed to parse inputs. Exiting.")
        sys.exit(1)
        
    if not creating_required_files(filename, bbox, end_time_str, period):
        print("\nFATAL ERROR: Could not generate all required SUMO input files. Check console output for details.")
        sys.exit(1)

    suggested_edges = suggest_blocking_edge(filename)
    if suggested_edges:
        print("\n" + "="*50)
        print("✅ SUGGESTED EDGE IDs FOR TRAFFIC BLOCKING (Use the first column)")
        print("="*50)
        print("The following major road edges were found in your network:")
        print("\nTOP 5 SUGGESTIONS:")
        
        printed_ids = set()
        count = 0
        
        for edge_id, road_type in suggested_edges: 
            if edge_id not in printed_ids:
                print(f"- **Clean Edge ID:** {edge_id} (Type: {road_type}) -> Suggested Lane Index: 0")
                printed_ids.add(edge_id)
                count += 1
                if count >= 5:
                    break
            
        if len(suggested_edges) > 5:
            print(f"\n... and more.")
        
        print("\n**Crucial Note:** When prompted, enter only the **Clean Edge ID** (e.g., '10013807254') and the **Lane Index** (usually 0, 1, or 2).")
        print("="*50)

    if not run_unblocked_simulation(filename, end_time_int):
        print("\nBaseline simulation failed. Skipping TraCI run.")
        sys.exit(1)

    if not run_blocked_simulation_traci(filename, end_time_int):
         print("\nBlocked simulation failed. Skipping comparison.")
         sys.exit(1)
         
    compare_simulation_results(filename)

    print("\nAll scenarios and analysis complete.")
    print(f"Final logs are located under the '{LOG_BASE_DIR}/{filename}/' directory.")
