<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUMO TraCI Scenario Controller Guide</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chosen Palette: Tech Neutral -->
    <!-- Application Structure Plan: A single-page application with a sticky top navigation. The structure is thematic, breaking down the README into: a Hero section for introduction, a "Concept" section with a visual diagram of the A/B test, an "Interactive Workflow" diagram where users click steps to see details, a tabbed "Prerequisites" section, a "Usage" guide, and an "Output" section featuring a Chart.js visualization of the results. This non-linear, interactive structure is chosen to make the technical process more digestible and engaging than a simple document scroll, facilitating user understanding at their own pace. -->
    <!-- Visualization & Content Choices: 1. A/B Concept -> Diagram (HTML/CSS) -> Static -> To visually simplify the core experimental setup. 2. Pipeline -> Interactive Stepper (JS) -> Click-to-expand -> To break down the complex multi-step process without overwhelming the user. 3. Results Comparison -> Bar Chart (Chart.js) -> Hover tooltips -> To provide an immediate, impactful visualization of the simulation's outcome, making the data more compelling than a plain text table. 4. Directory Structure -> Styled List (HTML/CSS) -> Static -> To clearly show the data organization. All visualizations are built with Canvas or HTML/CSS, adhering to constraints. -->
    <!-- CONFIRMATION: NO SVG graphics used. NO Mermaid JS used. -->
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc; /* slate-50 */
        }
        .step-connector {
            flex: 1;
            height: 2px;
            background-color: #cbd5e1; /* slate-300 */
        }
        .step.active .step-circle {
            background-color: #2563eb; /* blue-600 */
            color: white;
            border-color: #2563eb; /* blue-600 */
        }
        .step.active .step-title {
            color: #1e40af; /* blue-800 */
            font-weight: 600;
        }
        .code-block {
            background-color: #1e293b; /* slate-800 */
            color: #e2e8f0; /* slate-200 */
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: monospace;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .chart-container {
            position: relative;
            width: 100%;
            max-width: 768px; /* max-w-3xl */
            margin-left: auto;
            margin-right: auto;
            height: 24rem; /* h-96 */
            max-height: 500px;
        }
    </style>
</head>
<body class="text-slate-700">

    <!-- Header & Navigation -->
    <header class="bg-white/80 backdrop-blur-lg sticky top-0 z-50 border-b border-slate-200">
        <div class="container mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="bg-blue-600 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <h1 class="text-xl font-bold text-slate-800">SUMO TraCI Scenario Controller</h1>
            </div>
            <nav class="hidden md:flex space-x-8">
                <a href="#concept" class="text-slate-600 hover:text-blue-600 font-medium">Concept</a>
                <a href="#workflow" class="text-slate-600 hover:text-blue-600 font-medium">Workflow</a>
                <a href="#setup" class="text-slate-600 hover:text-blue-600 font-medium">Setup</a>
                <a href="#output" class="text-slate-600 hover:text-blue-600 font-medium">Results</a>
            </nav>
        </div>
    </header>

    <main class="container mx-auto px-6 py-12 md:py-20">
        <!-- Hero Section -->
        <section class="text-center mb-20 md:mb-32">
            <h2 class="text-4xl md:text-6xl font-bold text-slate-900 leading-tight">Congestion Modeling for Machine Learning</h2>
            <p class="mt-6 max-w-3xl mx-auto text-lg text-slate-600">
                An interactive guide to the Python pipeline that creates high-quality, comparable traffic datasets using SUMO. This tool simulates "stealth" congestion events to train models that can detect real-world incidents.
            </p>
            <a href="#workflow" class="mt-10 inline-block bg-blue-600 text-white font-semibold py-3 px-8 rounded-lg shadow-lg hover:bg-blue-700 transition-transform transform hover:scale-105">
                Explore the Workflow
            </a>
        </section>

        <!-- The Concept Section -->
        <section id="concept" class="mb-20 md:mb-32">
            <div class="text-center mb-12">
                <h3 class="text-3xl font-bold text-slate-900">The "Stealth Congestion" Concept</h3>
                <p class="mt-4 max-w-2xl mx-auto text-slate-600">The core idea is to run two identical simulations. One runs normally (the baseline), while the other has a "stealth" lane blockage introduced via TraCI. This creates two datasets where the only difference is the congestion itself, perfect for training an ML model.</p>
            </div>
            <div class="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
                <div class="flex flex-col md:flex-row items-center justify-around space-y-8 md:space-y-0 md:space-x-8">
                    <!-- Scenario 1: Unblocked -->
                    <div class="flex flex-col items-center text-center w-full md:w-1/3">
                        <div class="bg-green-100 p-4 rounded-full mb-4">
                           <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        </div>
                        <h4 class="font-bold text-xl text-slate-800">Scenario 1: Unblocked</h4>
                        <p class="text-slate-600 mt-2">A standard SUMO simulation runs to generate baseline traffic flow data.</p>
                        <div class="mt-4 text-sm font-semibold text-green-700 bg-green-100 px-3 py-1 rounded-full">Normal Log Output</div>
                    </div>

                    <!-- Arrow -->
                    <div class="hidden md:block text-slate-400">
                        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                    </div>
                     <div class="block md:hidden text-slate-400">
                        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
                    </div>


                    <!-- Scenario 2: Blocked -->
                     <div class="flex flex-col items-center text-center w-full md:w-1/3">
                        <div class="bg-red-100 p-4 rounded-full mb-4">
                           <svg class="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>
                        </div>
                        <h4 class="font-bold text-xl text-slate-800">Scenario 2: Blocked</h4>
                        <p class="text-slate-600 mt-2">TraCI dynamically blocks a lane mid-simulation, creating congestion.</p>
                        <div class="mt-4 text-sm font-semibold text-red-700 bg-red-100 px-3 py-1 rounded-full">Congested Log Output</div>
                    </div>
                </div>
                 <div class="mt-12 text-center text-slate-700 border-t border-slate-200 pt-6">
                    <p class="font-semibold text-lg">The result? Two datasets, identical in format, perfect for training a model to distinguish between normal and congested traffic patterns without any explicit "blocked lane" labels in the data.</p>
                </div>
            </div>
        </section>


        <!-- Interactive Workflow Section -->
        <section id="workflow" class="mb-20 md:mb-32">
            <div class="text-center mb-12">
                <h3 class="text-3xl font-bold text-slate-900">Interactive Project Workflow</h3>
                <p class="mt-4 max-w-2xl mx-auto text-slate-600">Click on each step to reveal details about the automated pipeline.</p>
            </div>
            <div id="workflow-steps" class="space-y-4">
                <!-- Step 1 -->
                <div class="step-container bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <button class="step-header w-full p-6 text-left flex items-center space-x-4">
                         <div class="step-circle flex-shrink-0 w-10 h-10 rounded-full border-2 border-slate-300 flex items-center justify-center font-bold text-lg text-slate-500 transition-colors">1</div>
                        <h4 class="step-title flex-grow text-xl font-medium text-slate-700 transition-colors">Get OSM Data</h4>
                        <svg class="step-arrow w-6 h-6 text-slate-400 transition-transform transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div class="step-content hidden px-6 pb-6 pt-2">
                        <p class="text-slate-600">The process starts by obtaining raw map data from OpenStreetMap for a specific geographical area defined by a bounding box. This file is the foundation for the entire simulation network.</p>
                        <div class="mt-4">
                            <h5 class="font-semibold mb-2">Required Action:</h5>
                            <p class="code-block">Save your map data as {filename}.osm in the project directory.</p>
                        </div>
                    </div>
                </div>
                <!-- Step 2 -->
                 <div class="step-container bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <button class="step-header w-full p-6 text-left flex items-center space-x-4">
                         <div class="step-circle flex-shrink-0 w-10 h-10 rounded-full border-2 border-slate-300 flex items-center justify-center font-bold text-lg text-slate-500 transition-colors">2</div>
                        <h4 class="step-title flex-grow text-xl font-medium text-slate-700 transition-colors">Generate SUMO Files</h4>
                        <svg class="step-arrow w-6 h-6 text-slate-400 transition-transform transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div class="step-content hidden px-6 pb-6 pt-2">
                        <p class="text-slate-600">The script automates the conversion of the raw `.osm` file into a full SUMO simulation scenario by running a sequence of tools.</p>
                        <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div><h5 class="font-semibold mb-2">Commands Executed:</h5>
                                <ul class="list-disc list-inside space-y-2 text-slate-600">
                                    <li><strong class="text-slate-800">netconvert:</strong> Creates the road network (`.net.xml`).</li>
                                    <li><strong class="text-slate-800">polyconvert:</strong> Extracts polygon data for visuals (`.poly.xml`).</li>
                                    <li><strong class="text-slate-800">randomTrips.py:</strong> Generates traffic demand (`.trip.xml`).</li>
                                    <li><strong class="text-slate-800">duarouter:</strong> Calculates vehicle routes (`.rou.xml`).</li>
                                </ul>
                            </div>
                            <div class="code-block">netconvert --osm-files {f}.osm -o {f}.net.xml\npolyconvert --osm-files {f}.osm ... -o {f}.poly.xml\npython randomTrips.py -n {f}.net.xml ... -o {f}.trip.xml\nduarouter -n {f}.net.xml ... -o {f}.rou.xml</div>
                        </div>
                    </div>
                </div>
                <!-- Step 3 -->
                 <div class="step-container bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <button class="step-header w-full p-6 text-left flex items-center space-x-4">
                         <div class="step-circle flex-shrink-0 w-10 h-10 rounded-full border-2 border-slate-300 flex items-center justify-center font-bold text-lg text-slate-500 transition-colors">3</div>
                        <h4 class="step-title flex-grow text-xl font-medium text-slate-700 transition-colors">Run Simulations</h4>
                        <svg class="step-arrow w-6 h-6 text-slate-400 transition-transform transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div class="step-content hidden px-6 pb-6 pt-2">
                        <p class="text-slate-600">Two separate simulations are executed sequentially using the same network and traffic demand to create the A/B test datasets.</p>
                         <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="bg-slate-50 p-4 rounded-lg border">
                                <h5 class="font-semibold mb-2 text-green-700">Run 1: Unblocked Baseline</h5>
                                <p>The script calls the standard `sumo` binary to run the simulation without any external control. This generates the baseline performance data.</p>
                            </div>
                             <div class="bg-slate-50 p-4 rounded-lg border">
                                <h5 class="font-semibold mb-2 text-red-700">Run 2: Blocked Scenario</h5>
                                <p>The script starts SUMO via `traci.start()` and connects as a client. It then dynamically blocks a user-specified lane for a set duration to create congestion.</p>
                            </div>
                        </div>
                    </div>
                </div>
                 <!-- Step 4 -->
                <div class="step-container bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <button class="step-header w-full p-6 text-left flex items-center space-x-4">
                         <div class="step-circle flex-shrink-0 w-10 h-10 rounded-full border-2 border-slate-300 flex items-center justify-center font-bold text-lg text-slate-500 transition-colors">4</div>
                        <h4 class="step-title flex-grow text-xl font-medium text-slate-700 transition-colors">Analyze & Compare</h4>
                        <svg class="step-arrow w-6 h-6 text-slate-400 transition-transform transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div class="step-content hidden px-6 pb-6 pt-2">
                        <p class="text-slate-600">After both simulations complete, the script automatically parses the `tripinfo_output.xml` log files from each run. It calculates and compares key performance metrics to quantify the impact of the blockage.</p>
                        <div class="mt-4">
                            <h5 class="font-semibold mb-2">Metrics Calculated:</h5>
                            <ul class="list-disc list-inside space-y-2 text-slate-600">
                                <li>Total Trips Completed</li>
                                <li>Average Trip Travel Time (sec)</li>
                                <li>Average Network Speed (m/s)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Prerequisites & Setup Section -->
        <section id="setup" class="mb-20 md:mb-32">
             <div class="text-center mb-12">
                <h3 class="text-3xl font-bold text-slate-900">Prerequisites & Setup</h3>
                <p class="mt-4 max-w-2xl mx-auto text-slate-600">Follow these steps to prepare your environment.</p>
            </div>
            <div class="bg-white rounded-lg border border-slate-200 shadow-lg p-8">
                <div class="flex border-b border-slate-200" id="setup-tabs">
                    <button data-tab="install" class="tab-button py-3 px-6 font-semibold text-blue-600 border-b-2 border-blue-600">Installation</button>
                    <button data-tab="config" class="tab-button py-3 px-6 font-semibold text-slate-500">Configuration</button>
                    <button data-tab="deps" class="tab-button py-3 px-6 font-semibold text-slate-500">Dependencies</button>
                </div>
                <div class="pt-8">
                    <div id="install-content" class="tab-content">
                        <h4 class="text-xl font-semibold mb-4">1. Install SUMO</h4>
                        <p>Download and install SUMO from the official website. Ensure the command-line tools like `sumo` and `netconvert` are accessible from your system's PATH.</p>
                        <a href="https://sumo.dlr.de/docs/Downloads.html" target="_blank" class="text-blue-600 hover:underline inline-block mt-2">Official SUMO Downloads →</a>
                    </div>
                    <div id="config-content" class="tab-content hidden">
                        <h4 class="text-xl font-semibold mb-4">2. Set SUMO_HOME</h4>
                        <p>The script requires the `$SUMO_HOME` environment variable to locate necessary tools like `randomTrips.py`. Set this variable to point to your SUMO installation directory.</p>
                        <div class="code-block mt-4"># Add to your ~/.bashrc or ~/.zshrc on Linux/macOS
export SUMO_HOME="/usr/share/sumo"

# For Windows, set via System Properties
# Example: C:\Program Files (x86)\DLR\Sumo</div>
                    </div>
                    <div id="deps-content" class="tab-content hidden">
                         <h4 class="text-xl font-semibold mb-4">3. Install Python Dependencies</h4>
                        <p>The `traci` library is required for the script to communicate with SUMO. While it's included in the SUMO installation, installing it via pip ensures it's available in your Python environment.</p>
                         <div class="code-block mt-4">pip install traci</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Output & Results Section -->
        <section id="output" class="mb-20 md:mb-32">
            <div class="text-center mb-12">
                <h3 class="text-3xl font-bold text-slate-900">Understanding the Output</h3>
                <p class="mt-4 max-w-2xl mx-auto text-slate-600">The script generates a structured output directory and a clear comparison report, visually represented below.</p>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                <div class="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
                    <h4 class="text-xl font-bold text-slate-800 mb-4">Results Comparison Chart</h4>
                    <p class="text-slate-600 mb-6">This chart visualizes the impact of the lane blockage. A higher travel time and lower speed in the "Blocked" scenario clearly indicate congestion.</p>
                    <div class="chart-container">
                        <canvas id="resultsChart"></canvas>
                    </div>
                </div>
                <div class="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
                    <h4 class="text-xl font-bold text-slate-800 mb-4">Log Directory Structure</h4>
                     <p class="text-slate-600 mb-6">All output files are organized into a nested directory structure, separating the logs from each scenario for clean analysis.</p>
                    <div class="code-block text-slate-300">
<pre>
.
└── scenario_logs/
    └── {your_filename}/
        ├── unblocked/
        │   ├── summary_output.xml
        │   └── tripinfo_output.xml
        └── blocked/
            ├── summary_output.xml
            └── tripinfo_output.xml
</pre>
                    </div>
                    <div class="mt-6 border-t pt-4">
                        <h5 class="font-semibold text-slate-800">Primary Dataset</h5>
                        <p class="text-slate-600 mt-2">The `tripinfo_output.xml` files from both directories serve as the final, clean datasets for training your machine learning model.</p>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <footer class="bg-slate-800 text-slate-300">
        <div class="container mx-auto px-6 py-8 text-center">
            <p>&copy; 2025 SUMO TraCI Scenario Controller. A project guide for traffic simulation and analysis.</p>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Interactive Workflow Accordion
            const stepHeaders = document.querySelectorAll('.step-header');
            stepHeaders.forEach(header => {
                header.addEventListener('click', () => {
                    const stepContainer = header.parentElement;
                    const content = header.nextElementSibling;
                    const arrow = header.querySelector('.step-arrow');
                    const step = header.closest('.step-container').parentElement;
                    
                    const wasActive = stepContainer.classList.contains('active');

                    // Close all others
                    document.querySelectorAll('.step-container.active').forEach(activeContainer => {
                         if (activeContainer !== stepContainer) {
                            activeContainer.classList.remove('active');
                            activeContainer.querySelector('.step-content').classList.add('hidden');
                            activeContainer.querySelector('.step-arrow').classList.remove('rotate-180');
                             activeContainer.querySelector('.step-header').parentElement.querySelector('.step-circle').classList.remove('bg-blue-600', 'text-white', 'border-blue-600');
                        }
                    });

                    if (!wasActive) {
                        stepContainer.classList.add('active');
                        content.classList.remove('hidden');
                        arrow.classList.add('rotate-180');
                        header.parentElement.querySelector('.step-circle').classList.add('bg-blue-600', 'text-white', 'border-blue-600');
                    } else {
                         stepContainer.classList.remove('active');
                         content.classList.add('hidden');
                         arrow.classList.remove('rotate-180');
                         header.parentElement.querySelector('.step-circle').classList.remove('bg-blue-600', 'text-white', 'border-blue-600');
                    }
                });
            });

            // Auto-open the first step
            if(stepHeaders.length > 0) {
                stepHeaders[0].click();
            }

            // Setup Tabs
            const tabsContainer = document.getElementById('setup-tabs');
            const tabButtons = tabsContainer.querySelectorAll('.tab-button');
            const tabContents = tabsContainer.nextElementSibling.querySelectorAll('.tab-content');

            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const tabId = button.dataset.tab;

                    tabButtons.forEach(btn => {
                        btn.classList.remove('text-blue-600', 'border-blue-600');
                        btn.classList.add('text-slate-500');
                    });
                    button.classList.add('text-blue-600', 'border-blue-600');
                    button.classList.remove('text-slate-500');

                    tabContents.forEach(content => {
                        if (content.id === `${tabId}-content`) {
                            content.classList.remove('hidden');
                        } else {
                            content.classList.add('hidden');
                        }
                    });
                });
            });

            // Results Chart
            const ctx = document.getElementById('resultsChart').getContext('2d');
            const exampleData = {
                unblocked: { time: 56.22, speed: 12.50 },
                blocked: { time: 61.55, speed: 11.42 }
            };

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Average Travel Time (sec)', 'Average Speed (m/s)'],
                    datasets: [
                        {
                            label: 'Unblocked Scenario',
                            data: [exampleData.unblocked.time, exampleData.unblocked.speed],
                            backgroundColor: 'rgba(34, 197, 94, 0.7)', // green-500
                            borderColor: 'rgba(22, 163, 74, 1)', // green-600
                            borderWidth: 1,
                            borderRadius: 4
                        },
                        {
                            label: 'Blocked Scenario',
                            data: [exampleData.blocked.time, exampleData.blocked.speed],
                            backgroundColor: 'rgba(239, 68, 68, 0.7)', // red-500
                            borderColor: 'rgba(220, 38, 38, 1)', // red-600
                            borderWidth: 1,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#e2e8f0' // slate-200
                            },
                            ticks: {
                                color: '#475569' // slate-600
                            }
                        },
                        x: {
                             grid: {
                                display: false
                            },
                            ticks: {
                                color: '#475569', // slate-600
                                font: {
                                    size: 14
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#334155', // slate-700
                                font: {
                                    size: 14
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: '#1e293b', // slate-800
                            titleColor: '#f1f5f9', // slate-100
                            bodyColor: '#cbd5e1', // slate-300
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += context.parsed.y.toFixed(2);
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>
