Automated SUMO-TraCI Scenario Controller

This project provides a robust, command-line interface (CLI) to automate the entire workflow for creating, running, and analyzing traffic simulations using SUMO (Simulation of Urban MObility) and the TraCI (Traffic Control Interface) library.

The primary goal is to facilitate disruption analysis by comparing a baseline traffic scenario against a scenario where a major road is dynamically closed (blocked) using TraCI calls.

🚀 Key Features

Full Pipeline Automation: Automatically handles map download (via BBOX), network conversion (netconvert), trip generation (randomTrips), routing (duarouter), and simulation execution.

Intelligent Edge Suggestion: Uses XML parsing to automatically identify and suggest major road segments (motorway, primary, busway, etc.) that are ideal for disruption testing.

Dynamic Road Blocking: Uses TraCI to block specified lanes at a specific simulation time and for a defined duration.

Performance Comparison: Generates a final report comparing key metrics (Total Travel Time, Average Speed) between the baseline and blocked scenarios.

Cross-Platform Compatibility: Designed to run seamlessly on both Windows and Linux environments.

🛠️ Requirements & Setup

You must have the following software installed and accessible from your command line:

Python 3.x: Used to run the main controller script.

SUMO (Simulation of Urban MObility): The entire SUMO suite (including sumo, netconvert, randomTrips, duarouter, etc.) must be installed and added to your system's PATH.

Dependencies: Install the required Python libraries.

pip install -r requirements.txt
# (Assuming requirements.txt contains: lxml)


Note: If you are running on Linux, ensure you have the libxml2-dev package installed for robust XML handling, as required by SUMO's tools.

🏁 How to Run the Simulation

The entire workflow is managed by the single executable script, SimulationRunner.py.

1. Execute the Script

Run the main file from your terminal:

python3 SimulationRunner.py


2. User Input & Configuration

The script will guide you through the initial setup:

Prompt

Description

Filename Auto-Detect

The script first checks your directory. If it finds a single .osm file (e.g., tehran.osm), it automatically uses that name and skips the BBOX prompts.

BBOX Coordinates

If no map is found, enter the latitude/longitude boundaries (min_lat, min_lon, max_lat, max_lon) to download a new map from OpenStreetMap.

Simulation Settings

Enter parameters like total simulation end time and trip generation period.

3. Select Edge for Disruption

After generating the baseline simulation files, the script will output a list of suggested roads for blocking:

✅ SUGGESTED EDGE IDs FOR TRAFFIC BLOCKING (Use the first column)

- 123456789 (Type: highway.primary)
- 987654321 (Type: highway.busway)
...


CRITICAL INPUT: When prompted for the blocking parameters, use the clean Clean Edge ID (e.g., 123456789) and the desired Lane Index (e.g., 0).

📊 Output and Analysis

Upon completion, the script will run two simulations (Baseline and Blocked) and generate a summary report comparing the traffic metrics, allowing you to quickly assess the impact of the road closure on the overall network performance.
