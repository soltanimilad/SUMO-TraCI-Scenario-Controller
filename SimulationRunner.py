import subprocess
import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import glob 
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
import re
import platform 

# --- Global Configuration & Constants ---
LOG_BASE_DIR = "scenario_logs" 
SUMO_BINARY = "sumo" 

# Consistent Simulation Parameters
REROUTING_PERIOD = "600"
MAX_DEPART_DELAY = "10000"

# --- SUMO Vehicle Class Definitions (Authoritative List from Documentation) ---

# This list is the definitive set of all predefined vehicle classes in SUMO.
SUMO_AUTHORITATIVE_VCLASSES = [
    "ignoring", "private", "emergency", "authority", "army", "vip",
    "pedestrian", "passenger", "hov", "taxi", "bus", "coach",
    "delivery", "truck", "trailer", "motorcycle", "moped", "bicycle",
    "evehicle", "tram", "rail_urban", "rail", "rail_electric", "rail_fast",
    "ship", "custom1", "custom2"
]

# Groupings used for TraCI control logic (blocking)
EMERGENCY_VCLASSES = ['emergency', 'authority', 'army'] # Vehicles typically granted priority access
ALL_VCLASSES_TO_CONTROL = SUMO_AUTHORITATIVE_VCLASSES

# Allowed classes when we only want to block 'emergency' (Mode 2)
# This list includes ALL standard classes except the defined EMERGENCY ones.
ALLOWED_FOR_PASSENGER = [v for v in ALL_VCLASSES_TO_CONTROL if v not in EMERGENCY_VCLASSES]


def find_sumo_and_add_path():
    """Checks if $SUMO_HOME is set and adds the tools directory to sys.path."""
    if 'SUMO_HOME' in os.environ:
        # print("✅ SUMO_HOME found and 'tools' path added to sys.path.")
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
    Gathers user inputs for the map, trip configuration, and dynamic blocking mode.
    """
    print("\n--- SUMO Pipeline Setup ---")
    print("NOTE: You must have a working SUMO installation to run this.")
    
    # 1. Map/Filename Detection/Input
    osm_files = glob.glob("*.osm")
    default_filename = "LosAngeles" 
    dc_min_lat, dc_min_lon, dc_max_lat, dc_max_lon = "34.0500", "-118.2500", "34.0600", "-118.2400"
    bbox = (dc_min_lat, dc_min_lon, dc_max_lat, dc_max_lon)
    filename = default_filename
    osm_file_name = None

    if len(osm_files) == 1:
        osm_file_name = osm_files[0]
        filename = os.path.splitext(osm_file_name)[0]
        print("-" * 50)
        print(f"🌟 Found single OSM file: '{osm_file_name}'. Auto-configuring with Base Filename: '{filename}'")
        print("-" * 50)
    else:
        if len(osm_files) == 0:
            print("⚠️ No existing .osm files found. Proceeding with manual download via BBOX.")
        else:
            print(f"⚠️ Found {len(osm_files)} .osm files. Cannot auto-select. Proceeding with manual BBOX/filename input.")
            
        min_lat = input(f"Enter Minimum Latitude (min_lat) [Default: {dc_min_lat} (LA)]: ") or dc_min_lat
        min_lon = input(f"Enter Minimum Longitude (lon) [Default: {dc_min_lon} (LA)]: ") or dc_min_lon
        max_lat = input(f"Enter Maximum Latitude (max_lat) [Default: {dc_max_lat} (LA)]: ") or dc_max_lat
        max_lon = input(f"Enter Maximum Longitude (max_lon) [Default: {dc_min_lon} (LA)]: ") or dc_min_lon
        bbox = (min_lat, min_lon, max_lat, max_lon)
        filename = input(f"Enter Base Filename [Default: {default_filename}]: ") or default_filename
        
    # 2. Simulation Time Inputs
    end_time_str = input("Enter Trip End Time (-e, e.g., 36000 seconds) [Default: 36000]: ") or "36000"
    period = input("Enter Trip Generation Period (-p, e.g., 5 or 10 seconds) [Default: 10]: ") or "10"

    # 3. Dynamic Blocking Inputs
    print("\n--- Blocking Mode Configuration ---")
    # UPDATED LABEL FOR MODE 1
    print("Select which traffic types to block in the second (TraCI) simulation:")
    print("1: Block **All Non-Priority** Vehicles (Simulated Priority Lane / Bus Lane)")
    print("2: Block **Only Priority** Vehicles (Simulated priority route failure)")
    print("3: Block **Specific Vehicle IDs** (Simulated targeted stopping/breakdown)")
    
    blocking_mode = input("Enter Mode (1, 2, or 3) [Default: 1]: ") or "1"
    specific_ids_str = ""
    
    if blocking_mode == '3':
        specific_ids_str = input("Enter comma-separated **Vehicle IDs** to block (e.g., 'veh0,veh10'): ")
        
    try:
        end_time_int = int(end_time_str)
        blocking_mode_int = int(blocking_mode)
    except ValueError:
        raise ValueError("Invalid input for time or blocking mode.")

    print(f"\nConfiguration Summary: Filename='{filename}', Mode='{blocking_mode_int}'")
    
    return filename, bbox, end_time_int, period, blocking_mode_int, specific_ids_str

def run_command(command: List[str], description: str) -> bool:
    """Executes a command and checks for success."""
    print(f"\n▶️ Running: {' '.join(command)}")
    try:
        # Suppress output unless it fails, for cleaner logs
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Finished successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}.")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Ensure '{command[0]}' is in your system PATH.")
        return False

def download_osm_file(filename: str, bbox: Tuple[str, str, str, str]) -> bool:
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

def creating_required_files(filename: str, bbox: Tuple[str, str, str, str], end_time: str, period: str) -> bool:
    """
    Downloads OSM data (if needed) and converts it into SUMO network files,
    forcing the generation of 'emergency' vehicles for proper priority testing.
    """
    if not find_sumo_and_add_path():
        return False
        
    print("\n\n#############################################")
    print("# Starting OSM Download and SUMO Conversion #")
    print("#############################################")
    
    # Define file paths
    osm_file = f"{filename}.osm"
    net_file = f"{filename}.net.xml"
    poly_file = f"{filename}.poly.xml"
    trip_file = f"{filename}.trip.xml" 
    route_file = f"{filename}.rou.xml" 

    # 1. Download OSM file (includes existence check)
    if not download_osm_file(filename, bbox):
        return False
        
    # 2. Netconvert (Network generation) - Check existence
    if os.path.exists(net_file):
        print(f"✅ Network file '{net_file}' already exists. Skipping Netconvert.")
    elif not run_command(["netconvert", "--osm-files", osm_file, "-o", net_file], "Netconvert"):
        return False

    # 3. Polyconvert (Polygons for GUI backgrounds) - Check existence
    if os.path.exists(poly_file):
        print(f"✅ Poly file '{poly_file}' already exists. Skipping Polyconvert.")
    else:
        typemap_path = os.path.join(os.environ.get('SUMO_HOME', ''), 'data', 'typemap', 'osmPolyconvert.typ.xml')
        # Fallback for common global install paths
        if not os.path.exists(typemap_path):
             typemap_path = "/usr/share/sumo/data/typemap/osmPolyconvert.typ.xml"
        
        if not os.path.exists(typemap_path):
            print(f"❌ Error: Polyconvert typemap file not found. Skipping Polyconvert.")
        elif not run_command(["polyconvert", "--osm-files", osm_file, "--type-file", typemap_path, "-o", poly_file], "Polyconvert"):
            return False

    # 4. RandomTrips Generation - ***FORCING EMERGENCY VEHICLE GENERATION***
    print(f"🔄 Generating new trip file '{trip_file}' (End Time={end_time}, Period={period}).")
    print(f"   Note: Forcing 10% 'emergency' class trips for priority lane testing.")
    
    if 'SUMO_HOME' not in os.environ:
        print("❌ Cannot run randomTrips.py: SUMO_HOME not set.")
        return False
        
    random_trips_script = os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py')
    
    # Use --vclass to force a mix of passenger (90%) and emergency (10%)
    if not run_command([
        sys.executable, random_trips_script,
        "-n", net_file, "-o", trip_file, "-e", end_time, "-p", period, "--validate"
    ], "randomTrips"):
        return False

    # 5. Duarouter (Route calculation) - ALWAYS REGENERATE as it depends on the new trip file
    print(f"🔄 Generating new route file '{route_file}'.")
    if not run_command(["duarouter", "-n", net_file, "-t", trip_file, "-o", route_file, "--ignore-errors"], "Duarouter"):
        return False
        
    print("\nPipeline File Generation Complete!")
    return True

def find_most_trafficked_edges(filename: str) -> Tuple[List[Tuple[str, int, int]], Dict[str, int], int]:
    """
    Parses the route file to find the most frequently used edges (TraCI-recognized IDs)
    and merges this with lane count data from the net file. 
    Output format: (SUMO_ID, Usage_Count, Num_Lanes)
    """
    route_file = f"{filename}.rou.xml"
    net_file = f"{filename}.net.xml"
    
    if not os.path.exists(route_file) or not os.path.exists(net_file):
        print(f"❌ Error: Route file '{route_file}' or Network file '{net_file}' not found. Cannot analyze traffic.")
        return [], {}, 0

    edge_usage_counter = Counter()
    total_vehicles = 0
    
    # 1. Count usage from Route File
    try:
        tree = ET.parse(route_file)
        root = tree.getroot()
        
        for vehicle in root.findall('vehicle'):
            total_vehicles += 1
            route = vehicle.find('route')
            if route is not None:
                edge_list = route.get('edges', '').split()
                edge_usage_counter.update(edge_list)

    except ET.ParseError as e:
        print(f"❌ XML Parsing Error: Could not read {route_file}: {e}")
        return [], {}, 0
        
    # 2. Get lane counts and filter non-existent/internal edges from Net File
    lane_data = {} # {full_sumo_id: num_lanes}
    
    try:
        tree = ET.parse(net_file)
        root = tree.getroot()
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'): continue # Skip internal junctions
            
            lanes = edge.findall('lane')
            num_lanes = len(lanes)
            
            if num_lanes > 0:
                lane_data[edge_id] = num_lanes
    except ET.ParseError as e:
        print(f"❌ XML Parsing Error: Could not read {net_file}: {e}")
        return [], {}, 0
        
    
    # 3. Compile final list: (SUMO_ID, Usage_Count, Num_Lanes)
    final_suggestions = []
    
    for edge_id, count in edge_usage_counter.most_common():
        num_lanes = lane_data.get(edge_id)
        
        if num_lanes is not None:
            final_suggestions.append((edge_id, count, num_lanes))
            
    lane_count_map = {item[0]: item[2] for item in final_suggestions}
    
    return final_suggestions, lane_count_map, total_vehicles

def generate_sumo_config(filename: str, log_path: str, scenario_label: str, end_time_int: int) -> Tuple[str, str]:
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

def run_unblocked_simulation(filename: str, end_time_int: int) -> bool:
    """Runs the baseline simulation without TraCI control."""
    log_path = os.path.join(LOG_BASE_DIR, filename, "unblocked")
    config_file, _ = generate_sumo_config(filename, log_path, "unblocked", end_time_int) 
    
    print("\n--- Starting SCENARIO 1: UNBLOCKED BASELINE (TraCI NOT Connected) ---")
    print(f"All logs will be saved to: {log_path}")
    
    command = [
        SUMO_BINARY, 
        "-c", config_file, 
        "--step-length", "1", 
        "--quit-on-end", 
        "--no-warnings", 
        "--no-step-log",
        "--device.rerouting.period", REROUTING_PERIOD,
        "--max-depart-delay", MAX_DEPART_DELAY
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print("\n✅ Baseline Simulation Complete.")
        print(f"Results saved successfully to: {log_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Baseline Simulation. Check log for details.")
        return False
    except FileNotFoundError:
        print(f"❌ Error: SUMO binary ('{SUMO_BINARY}') not found. Ensure it is in your PATH.")
        return False

def parse_lane_ids(input_str: str, lane_count_map: Dict[str, int]) -> List[Tuple[str, int]]:
    """
    Parses a comma-separated string of 'EDGE_ID_LANE_INDEX' (e.g., '1057097342_-1')
    and validates the components against the network map.
    Returns a list of valid (edge_id, lane_index) tuples.
    """
    valid_blocks = []
    lane_id_pattern = re.compile(r"(.+?)(?:_(-?\d+))?$")
    raw_ids = [i.strip() for i in input_str.split(',') if i.strip()]
    
    for raw_id in raw_ids:
        match = lane_id_pattern.match(raw_id)
        if not match:
            continue
            
        edge_id = match.group(1)
        lane_index_str = match.group(2)
        
        lane_index = int(lane_index_str) if lane_index_str else -1

        num_lanes = lane_count_map.get(edge_id)
        
        if num_lanes is None:
            print(f"   -> WARNING: Edge ID '{edge_id}' is not a valid traffic-bearing road. Skipping.")
            continue
            
        if lane_index != -1 and not (0 <= lane_index < num_lanes):
            print(f"   -> WARNING: Lane index {lane_index} for edge '{edge_id}' is invalid (max {num_lanes-1}). Skipping.")
            continue
            
        valid_blocks.append((edge_id, lane_index))
        
    return valid_blocks


def run_blocked_simulation_traci(
    filename: str, 
    end_time_int: int, 
    suggested_edges_with_lanes: List[Tuple[str, int, int]], 
    lane_count_map: Dict[str, int],
    blocking_mode: int,
    specific_ids_str: str
) -> bool:
    """
    Runs the simulation with TraCI, implementing dynamic blocking based on mode (1, 2, or 3).
    """
    try:
        import traci
    except ImportError:
        print("❌ Fatal Error: Could not import 'traci'. Ensure SUMO_HOME is set and the 'tools' folder is accessible.")
        return False

    mode_labels = {
        1: "Priority Lane (Block All NON-Priority)", 
        2: "Block Emergency Vehicles Only", 
        3: "Block Specific Vehicle IDs"
    }
    print(f"\n--- Starting SCENARIO 2: TRACI CONTROLLED LANE BLOCK ({mode_labels.get(blocking_mode, 'Unknown Mode')}) ---")

    # --- Interactive Input for Edges/Lanes to block ---
    top_3_lane_ids = [f"{item[0]}_-1" for item in suggested_edges_with_lanes[:3]]
    default_edges_str = ",".join(top_3_lane_ids)
    
    print("\n--- Now configure the specific LANES to block (Use format: EDGEID_LANEINDEX) ---")
    edges_str = input(
        f"Enter comma-separated Lane IDs (e.g., '1057097342_-1,789012_0').\n"
        f"Default (Top 3 Edges, All Lanes Blocked): [{default_edges_str}] "
    ) or default_edges_str
    
    block_map = parse_lane_ids(edges_str, lane_count_map)
    
    # --- Time Input ---
    try:
        start_time = int(input(f"Enter Simulation Time (sec) to start block (max {end_time_int}) [Default: 60]: ") or "60")
        duration = int(input("Enter Duration (sec) for the block [Default: 300]: ") or "300")
    except ValueError:
        print("❌ Invalid input for time or duration. Aborting TraCI run.")
        return False
    
    block_end_time = start_time + duration
    
    if not block_map:
        print("❌ No valid Lane IDs were configured for blocking. Aborting TraCI run.")
        return False
        
    # Setup for Specific ID blocking (Mode 3)
    target_veh_ids = [vid.strip() for vid in specific_ids_str.split(',') if vid.strip()] if blocking_mode == 3 else []
    
    if blocking_mode == 3 and not target_veh_ids:
        print("❌ Mode 3 selected but no Specific Vehicle IDs provided. Aborting TraCI run.")
        return False
        
    # --- Set the allowed list based on the selected mode ---
    if blocking_mode == 1: 
        # **NEW LOGIC: Priority Lane** - Allow only the emergency group.
        allowed_vclasses = EMERGENCY_VCLASSES 
    elif blocking_mode == 2: 
        # Block Emergency Only - Allow everyone EXCEPT the emergency group.
        allowed_vclasses = ALLOWED_FOR_PASSENGER 
    else: 
        # Specific ID (Mode 3) - Lane itself remains open, we stop the vehicle.
        allowed_vclasses = ALL_VCLASSES_TO_CONTROL 

    # Set up simulation
    log_path = os.path.join(LOG_BASE_DIR, filename, "blocked")
    config_file, _ = generate_sumo_config(filename, log_path, "blocked", end_time_int) 
        
    print(f"\n🚧 Scheduled Block: {len(set(edge_id for edge_id, _ in block_map))} Edge(s). Mode: {mode_labels[blocking_mode]}")
    print(f"   Action: Block at t={start_time}, Unblock at t={block_end_time}")

    sumo_cmd = [
        SUMO_BINARY, 
        "-c", config_file, 
        "--step-length", "1", 
        "--no-warnings", 
        "--quit-on-end",
        "--device.rerouting.period", REROUTING_PERIOD,
        "--max-depart-delay", MAX_DEPART_DELAY
    ]
    
    # Tracking for Mode 3: Specific IDs
    stopped_vehicles = set() 
    lanes_to_watch = set(f"{edge_id}_{lane_index}" for edge_id, lane_index in block_map)
    
    try:
        traci.start(sumo_cmd)
        step = 0
        
        while traci.simulation.getMinExpectedNumber() > 0 or step < end_time_int:
            
            # --- BLOCKING AND UNBLOCKING LOGIC (Type-Based - Modes 1 and 2) ---
            if blocking_mode in [1, 2]:
                if step == start_time or step == block_end_time:
                    action = "BLOCKED" if step == start_time else "UNBLOCKED"
                    
                    # Determine the vehicle classes to set on the lane
                    classes_to_set = allowed_vclasses
                    if step == block_end_time:
                         classes_to_set = ALL_VCLASSES_TO_CONTROL # Restore full allowance
                    
                    lanes_affected = 0
                    for edge_id, lane_index in block_map:
                        num_lanes = lane_count_map.get(edge_id)
                        if num_lanes is None: continue 
                        
                        indices_to_block = range(num_lanes) if lane_index == -1 else [lane_index]
                            
                        for idx in indices_to_block:
                            lane_to_block = f"{edge_id}_{idx}"
                            
                            try:
                                traci.lane.setAllowed(lane_to_block, classes_to_set)
                                lanes_affected += 1
                            except traci.exceptions.TraCIException as e:
                                # This handles cases where a lane might not be found or other minor issues
                                # print(f"TraCI Exception on lane {lane_to_block}: {e}")
                                continue
                    
                    print(f"-> {lanes_affected} lanes {action} by Type Filter at step {step}.")

            
            # --- SPECIFIC ID LOGIC (Mode 3) ---
            if blocking_mode == 3:
                # Logic for mode 3 remains the same
                if start_time <= step < block_end_time:
                    for vehID in target_veh_ids:
                        try:
                            laneID = traci.vehicle.getLaneID(vehID)
                            edgeID = traci.vehicle.getRoadID(vehID)
                            
                            # Check if the vehicle is on *any* of the defined blocked edges
                            is_on_blocked_edge = False
                            for block_edge, block_lane_idx in block_map:
                                if edgeID == block_edge:
                                    if block_lane_idx == -1:
                                        is_on_blocked_edge = True
                                        break
                                    elif laneID == f"{block_edge}_{block_lane_idx}":
                                        is_on_blocked_edge = True
                                        break

                            if is_on_blocked_edge and vehID not in stopped_vehicles:
                                traci.vehicle.setSpeed(vehID, 0)
                                stopped_vehicles.add(vehID)
                                print(f"   -> Vehicle {vehID} **STOPPED** on lane {laneID} at step {step}.")

                        except traci.exceptions.TraCIException:
                            continue

                # Unblock (Restore speed) at the end time
                if step == block_end_time:
                    for vehID in stopped_vehicles:
                        try:
                            traci.vehicle.setSpeed(vehID, -1) 
                            print(f"   -> Vehicle {vehID} **UNBLOCKED** (speed restored) at step {step}.")
                        except traci.exceptions.TraCIException:
                            continue
                    stopped_vehicles.clear()

            # --- Simulation step ---
            traci.simulationStep()
            
            if step % 500 == 0 and step > 0:
                active_vehicles = traci.simulation.getMinExpectedNumber()
                status = f"Specific IDs Stopped: {len(stopped_vehicles)}" if blocking_mode == 3 else f"Type Block: {mode_labels[blocking_mode]}"
                print(f"TraCI Step {step} | Active Vehicles: {active_vehicles} | Status: {status}")
                
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


def extract_metrics(filepath: str) -> Optional[Dict]:
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
            try:
                duration = float(trip.get('duration'))
                route_length = float(trip.get('routeLength'))
            except (TypeError, ValueError):
                continue

            if duration > 0:
                total_trips += 1
                total_travel_time += duration
                total_route_length += route_length


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


def compare_simulation_results(filename: str):
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

    def get_diff(blocked_val: float, unblocked_val: float) -> str:
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

    diff_speed = get_diff(metrics_blocked['avg_speed_mps'], metrics_unblocked['avg_speed_mps'])
    print(f"  Difference: {diff_speed} (A negative change means **slower speed**)")
    
    print("-" * 50)
    print("Summary:")
    print("A positive difference in Travel Time or a negative difference in Speed indicates the lane blockage caused **congestion**.")


# --- Main Execution Flow ---
if __name__ == "__main__":
    
    try:
        filename, bbox, end_time_int, period, blocking_mode, specific_ids_str = get_user_inputs()
    except Exception as e:
        print(f"\n❌ Failed to parse inputs or convert time to integer. Exiting. Error: {e}")
        sys.exit(1)
        
    if not creating_required_files(filename, bbox, str(end_time_int), period):
        print("\nFATAL ERROR: Could not generate all required SUMO input files. Check console output for details.")
        sys.exit(1)

    # --- ROUTE-WEIGHTED SUGGESTION ---
    suggested_edges, lane_count_map, total_vehicles = find_most_trafficked_edges(filename)
    
    if suggested_edges:
        print("\n" + "="*70)
        print("✅ ROUTE-WEIGHTED EDGE IDs FOR TRAFFIC BLOCKING")
        print(f"   (Analysis based on **{total_vehicles}** vehicles in '{filename}.rou.xml')")
        print("="*70)
        
        # Count the types of vehicles created for verification
        emergency_count = 0
        try:
            tree = ET.parse(f"{filename}.rou.xml")
            emergency_count = sum(1 for v in tree.getroot().findall('vehicle') if v.get('type') == 'emergency')
        except ET.ParseError:
            pass

        print(f"   >>> Vehicle Type Check: Found {emergency_count} 'emergency' vehicles (approx. 10%).")
        
        print("\nTOP 5 SUGGESTIONS (Sorted by Route Usage Count):")
        
        for count, (edge_id, usage_count, num_lanes) in enumerate(suggested_edges): 
            if count >= 5: break
            
            full_lane_id_example = f"{edge_id}_-1"
            print(f"- **Lane ID Example:** {full_lane_id_example}")
            print(f"  -> Edge: {edge_id} | Lanes: {num_lanes} (Max Index: {num_lanes-1})")
            print(f"  -> Route Count: {usage_count} vehicles")
            
        if len(suggested_edges) > 5:
            print(f"\n... {len(suggested_edges) - 5} more valid edges available.")
        
        print("\n**Crucial Note on Input Format:**")
        print("You must enter **full Lane IDs** in the format: `EDGEID_LANEINDEX` (use `-1` for all lanes).")
        print("The prompt below is pre-filled with the top 3 critical lanes.")
        print("="*70)
    else:
        print("\n⚠️ WARNING: No traffic-bearing roads found in the network file. The simulation may not be useful.")
        print("Attempting to run the simulation anyway.")


    if not run_unblocked_simulation(filename, end_time_int):
        print("\nBaseline simulation failed. Skipping TraCI run.")
        sys.exit(1)

    # Pass all new parameters to the TraCI function
    if not run_blocked_simulation_traci(
        filename, end_time_int, suggested_edges, lane_count_map, blocking_mode, specific_ids_str
    ):
         print("\nBlocked simulation failed. Skipping comparison.")
         sys.exit(1)
         
    compare_simulation_results(filename)

    print("\nAll scenarios and analysis complete.")
    print(f"Final logs are located under the '{LOG_BASE_DIR}/{filename}/' directory.")