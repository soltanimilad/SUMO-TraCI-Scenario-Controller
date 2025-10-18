# 🚦 Automated SUMO–TraCI Scenario Controller

A **robust command-line tool** to automate the full workflow of creating, running, and analyzing **traffic simulations** using **SUMO (Simulation of Urban MObility)** and the **TraCI (Traffic Control Interface)** library.

This tool is designed to **analyze disruption impacts** by comparing a **baseline traffic scenario** with another scenario where a **major road is dynamically blocked** using TraCI.

---

## 🚀 Key Features

* **Full Pipeline Automation**
  Automatically handles every step — map download (via BBOX), network conversion (`netconvert`), trip generation (`randomTrips`), routing (`duarouter`), and simulation execution.

* **Intelligent Edge Suggestion**
  Parses the SUMO network XML file to automatically suggest major road segments (`motorway`, `primary`, `busway`, etc.) suitable for disruption testing.

* **Dynamic Road Blocking**
  Uses TraCI to dynamically block specified lanes at a defined simulation time and for a chosen duration.

* **Performance Comparison**
  Generates a detailed summary comparing **Total Travel Time**, **Average Speed**, and other metrics between baseline and blocked scenarios.

* **Cross-Platform Compatibility**
  Works seamlessly on **Windows** and **Linux**.

---

## 🛠️ Requirements & Setup

### 1. Prerequisites

Make sure the following are installed and accessible from your terminal:

* **Python 3.x** – to run the controller script
* **SUMO (Simulation of Urban MObility)** – including `sumo`, `netconvert`, `randomTrips`, `duarouter`, etc. (must be added to your system `PATH`)

### 2. Install Dependencies

Install Python dependencies using:

```bash
pip install -r requirements.txt
```

> 💡 Make sure `requirements.txt` includes:
>
> ```
> lxml
> ```

**Linux users:**
Ensure the `libxml2-dev` package is installed for robust XML handling — it’s required by SUMO’s tools.

---

## 🏁 How to Run the Simulation

The main entry point is the script **`SimulationRunner.py`**.

### 1. Execute the Script

Run it from your terminal:

```bash
python3 SimulationRunner.py
```

### 2. Follow the Interactive Prompts

The script guides you step-by-step through configuration:

| Prompt                   | Description                                                                                                                                              |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Filename Auto-Detect** | If a single `.osm` file exists (e.g., `tehran.osm`), it will be automatically selected.                                                                  |
| **BBOX Coordinates**     | If no map is found, you’ll be asked to enter boundary coordinates (`min_lat`, `min_lon`, `max_lat`, `max_lon`) to download a new map from OpenStreetMap. |
| **Simulation Settings**  | Define simulation end time and trip generation parameters.                                                                                               |

---

## 🚧 Selecting the Edge for Disruption

After the baseline simulation is generated, the tool outputs a list of **suggested edges** for testing:

```
✅ SUGGESTED EDGE IDs FOR TRAFFIC BLOCKING
(Use the first column)

- 123456789  (Type: highway.primary)
- 987654321  (Type: highway.busway)
...
```

When prompted, enter:

* **Edge ID** → e.g., `123456789`
* **Lane Index** → e.g., `0`

---

## 📊 Output & Analysis

After running both **Baseline** and **Blocked** simulations, a **summary report** is generated containing:

* Total Travel Time
* Average Speed
* Network Performance Comparison

This helps quantify the **impact of road closures** on overall traffic efficiency.

---

### 🧭 Example Workflow Overview

```text
[1] Map Download → [2] Network Conversion → [3] Trip Generation
       ↓
[4] Routing → [5] Baseline Simulation → [6] Dynamic Blocking → [7] Report Generation
```

---

### 🧩 Folder Structure

```
├── SimulationRunner.py
├── requirements.txt
├── /maps
│   └── tehran.osm
├── /networks
├── /trips
├── /routes
└── /outputs
    ├── baseline_summary.xml
    ├── blocked_summary.xml
    └── comparison_report.txt
```

---

### 📘 License

This project is released under the **MIT License** — free for personal and academic use.

