import xml.etree.ElementTree as ET
import os

def list_major_road_edges(filename):
    """
    Parses the SUMO .net.xml file and lists edges corresponding to major roads.
    
    Major roads are typically mapped from OSM types like motorway, primary, and secondary.
    These types often have high capacity and speed limits.
    """
    net_file = f"{filename}.net.xml"
    
    if not os.path.exists(net_file):
        print(f"❌ Error: Network file '{net_file}' not found.")
        print("Please ensure you have successfully run the full pipeline script first.")
        return

    # Define common SUMO road types that represent large/major streets.
    # The actual types may vary slightly based on your netconvert configuration.
    MAJOR_ROAD_TYPES = [
        "motorway", 
        "primary", 
        "secondary", 
        "primary_link", 
        "secondary_link",
        "trunk", # Often a major highway
    ]

    print(f"\n--- Analyzing Network File: {net_file} ---")
    print("Looking for Edge IDs with function/type matching:", MAJOR_ROAD_TYPES)
    print("-" * 50)

    try:
        tree = ET.parse(net_file)
        root = tree.getroot()
        
        major_edge_ids = set()
        
        # Iterate through all <edge> elements in the network
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            # Skip internal edges (often starting with ':')
            if edge_id.startswith(':'):
                continue

            # Check the 'function' attribute (common in SUMO networks)
            road_type = edge.get('function', '').lower()
            
            # Check the internal <lane> type attribute (less common for edge filtering)
            if not road_type:
                 # Fallback: Sometimes the classification is only visible on the <lane> element
                for lane in edge.findall('lane'):
                    lane_type = lane.get('type', '').lower()
                    for major_type in MAJOR_ROAD_TYPES:
                        if major_type in lane_type:
                            road_type = lane_type
                            break
                    if road_type:
                        break

            # Check if the extracted road_type contains any of the major road identifiers
            is_major = False
            for major_type in MAJOR_ROAD_TYPES:
                if major_type in road_type:
                    is_major = True
                    break

            if is_major:
                major_edge_ids.add((edge_id, road_type))
        
        if not major_edge_ids:
            print("⚠️ No major roads found with the predefined types. You may need to inspect the .net.xml manually.")
            return

        print(f"Found {len(major_edge_ids)} major road segments.")
        print("\nList of Major Edge IDs (ID, Type):")
        
        # Print the results in a readable format
        for edge_id, road_type in sorted(list(major_edge_ids)):
            print(f"- {edge_id} (Type: {road_type})")
            
        print("\nUse any of these Edge IDs (e.g., 'A2345#0') in the blocking scenario.")
        
    except ET.ParseError as e:
        print(f"❌ XML Parsing Error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

# --- Execution ---
if __name__ == "__main__":
    # Assuming your base filename is the same as used in the controller script
    filename = input("Enter the Base Filename (e.g., 'california_test'): ") or "california_test"
    list_major_road_edges(filename)
