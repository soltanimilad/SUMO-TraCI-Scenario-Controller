🚗 SUMO TraCI Scenario Controller: Congestion Modeling for Machine Learning

This Python script provides a robust pipeline for running two comparative traffic simulations using the SUMO (Simulation of Urban MObility) environment. It is specifically designed to create high-quality, comparable datasets for machine learning models aiming to detect or predict non-recurrent congestion (e.g., unexpected accidents or road closures).

The key feature is the script's ability to introduce a simulated road blockage using the TraCI (Traffic Control Interface) layer without leaving any trace of the intervention in the final simulation log files. This creates a "ground truth" congestion scenario where the logs only reflect the consequences, not the cause.

✨ Features

SUMO Input Generation: Automatically calls netconvert, polyconvert, randomTrips.py, and duarouter to convert OSM data and generate the necessary network (.net.xml), polygon (.poly.xml), trips (.trip.xml), and routes (.rou.xml) files.

Two-Scenario A/B Testing: Runs two distinct simulations based on identical traffic demand:

Unblocked Baseline: Standard SUMO simulation.

Blocked Scenario (TraCI Controlled): Same simulation, but with a dynamically scheduled lane closure via TraCI.

Stealth Congestion: The lane blocking action is performed via the TraCI API and is not logged in the standard SUMO output files, making the datasets clean for ML training.

Automated Comparison: Parses the resulting tripinfo_output.xml files from both scenarios to provide a quantitative comparison of average travel time and network speed, clearly showing the impact of the simulated blockage.

Structured Logging: All simulation outputs are saved into a structured directory under scenario_logs/{filename}/{unblocked|blocked}/.

🛠️ Prerequisites

To run this controller, you need the following:

SUMO: Installed and accessible via your system's PATH.

Python 3: With traci library installed.

Environment Variable: The $SUMO_HOME environment variable must be set and point to your SUMO installation directory for the script to locate the necessary tools/randomTrips.py.

Installation Steps

Install SUMO: Follow the official installation guide for your OS.

Set SUMO_HOME:

# Example for Linux/macOS (add to your .bashrc or .zshrc)
export SUMO_HOME="/usr/share/sumo"
# Example for Windows (set via System Properties or command line)
# setx SUMO_HOME "C:\Program Files (x86)\DLR\Sumo"


Install Python Dependencies:

pip install traci # traci is usually included with SUMO, but this ensures it's available


🚀 Usage

Step 1: Obtain OpenStreetMap (OSM) Data

Before running the script, you must download the OSM data for your desired bounding box and save it as {filename}.osm in the project directory.

Example: If your base filename is dallas, you need dallas.osm.

Step 2: Run the Controller Script

Execute the Python script:

python sumo_scenario_controller.py


Step 3: Input Prompts

The script will guide you through several interactive prompts:

Map Coordinates: Enter the Bounding Box (BBOX) for the area you downloaded.

Base Filename: (e.g., california_test). This name is used for all generated input and output files.

Trip Parameters: End Time and Period for traffic generation.

Blocking Parameters (Scenario 2):

Edge ID: The street segment where the blockage will occur (e.g., E1).

Lane Index: The specific lane on that segment (e.g., 0 for the rightmost lane).

Start Time: The simulation time (in seconds) when the lane is blocked.

Duration: How long (in seconds) the lane remains blocked.

Example Output

The script will print progress for each step (netconvert, duarouter, Scenario 1 run, Scenario 2 run) and conclude with the comparison report:

==================================================
STARTING SCENARIO COMPARISON REPORT
==================================================
Comparison Report for Map: california_test
--------------------------------------------------
Total Trips Completed: 
  Unblocked: 1000
  Blocked:   1000

Average Trip Travel Time (sec): 
  Unblocked: 56.22
  Blocked:   61.55
  Difference: +5.33 (+9.48%) (A positive change means more time)

Average Network Speed (m/s): 
  Unblocked: 12.50
  Blocked:   11.42
  Difference: -1.08 (-8.64%) (A negative change means slower speed)

--------------------------------------------------
Summary:
A positive difference in Travel Time or a negative difference in Speed indicates the lane blockage caused **congestion**.


📂 Output Structure

All simulation logs are stored in the root directory under scenario_logs/.

.
├── scenario_logs/
│   └── {filename}/
│       ├── unblocked/
│       │   ├── summary_output.xml  # Baseline logs
│       │   └── tripinfo_output.xml 
│       └── blocked/
│           ├── summary_output.xml  # Congested logs
│           └── tripinfo_output.xml 
└── sumo_scenario_controller.py
└── {filename}.net.xml
└── {filename}.rou.xml
└── ...


The tripinfo_output.xml files are the primary dataset outputs for training your congestion detection models.
