🚦 SUMO TraCI Scenario Controller: Congestion Modeling for Machine Learning

A robust Python pipeline designed to create high-quality, comparative traffic datasets using SUMO (Simulation of Urban MObility). This tool simulates "stealth" congestion events via TraCI to train machine learning models for real-world incident detection.

💡 The A/B Test Concept

Two identical simulations are run: the first serves as a baseline (A), and the second introduces a "stealth" lane blockage via TraCI (B). This generates two clean datasets where the only meaningful difference is the congestion event.

Scenario

Mode

Purpose

Status

Scenario A

Unblocked Baseline

Standard SUMO run generating normal traffic flow data.

Normal Performance

Scenario B

Blocked Event

TraCI dynamically blocks a lane mid-simulation, simulating an incident.

Congestion Generated

🚀 Project Workflow Steps

The automated Python pipeline is executed in four sequential steps to produce the final, usable machine learning dataset.

1. Get OSM Data

Start by obtaining raw map data from OpenStreetMap for your area of interest (AOI). This file acts as the geographical foundation for the entire simulation network.

Required Action: Save your map data as {filename}.osm in the project directory.

2. Generate SUMO Files

The script automatically converts the raw .osm file into all necessary SUMO components using internal tools like netconvert, polyconvert, and duarouter to create the network, polygons, and vehicle routes.

Generated Assets:

.net.xml (Road Network)

.rou.xml (Vehicle Routes)

.poly.xml (Visual Data)

3. Run A/B Simulations

Two separate simulations are executed sequentially using the same network and traffic demand. The first is a standard run (Baseline), and the second is controlled by TraCI to dynamically introduce the lane blockage at a specified time and location (Congestion).

Simulation Mode 1: Standard SUMO (Baseline)

Simulation Mode 2: SUMO + TraCI Control (Congestion)

4. Analyze & Compare

The script automatically parses the simulation output files (tripinfo_output.xml) from both runs. It calculates and compares key performance metrics to quantify the exact traffic impact caused by the congestion event.

Metrics Calculated: Total Trips, Average Trip Travel Time, Average Network Speed.

🛠️ Setup Guide

Prepare your environment by following these three essential steps.

1. Installation

Download and install SUMO from the official website. Ensure the command-line tools (sumo, netconvert, etc.) are correctly added to your system's PATH.

Official SUMO Downloads →

2. Configuration

Set the $SUMO_HOME environment variable to point to your main SUMO installation directory. This is crucial for locating internal Python scripts.

export SUMO_HOME="/usr/share/sumo"


3. Dependencies

Install the necessary Python dependencies, primarily the traci library, which facilitates the simulation control.

pip install traci


📊 Results and Output Structure

The lane blockage results in a measurable increase in travel time and a decrease in average speed across the network, confirming the efficacy of the simulated congestion event.

Quantified Impact Visualization (Example Data)

Metric

Unblocked (Baseline)

Blocked (Congestion)

Impact

Avg. Travel Time

56.22 sec

61.55 sec

+9.48%

Avg. Network Speed

12.50 m/s

11.42 m/s

-8.64%

Log Directory Structure

All output files are cleanly organized into scenario-specific directories, ensuring the A/B test logs are immediately comparable.

.
└── scenario_logs/
    └── {your_filename}/
        ├── unblocked/
        │   ├── summary_output.xml
        │   └── tripinfo_output.xml  ← Dataset A (Baseline)
        └── blocked/
            ├── summary_output.xml
            └── tripinfo_output.xml  ← Dataset B (Congestion)


The tripinfo_output.xml files from the unblocked and blocked folders are the final, ready-to-use datasets for training your machine learning model.
