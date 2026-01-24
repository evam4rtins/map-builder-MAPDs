# Map Builder – Research Tool

A web-based tool for creating and managing grid-based maps with agents, obstacles, and task locations. Designed to support research workflows (e.g., MAPF, MAPD, task allocation) and export structured map definitions in YAML format.

Built with **Flask** and **vanilla JavaScript**.

---

## Features

- **Interactive Map Grid**  
  Create and edit 2D grid maps with customizable dimensions.

- **Multiple Editing Tools**  
  Place obstacles, non-task endpoints, pickup locations, delivery locations, and agent start positions.

- **Visual Encoding of Map Elements**  
  Distinct geometric shapes and colors are used to clearly differentiate map elements 

- **Real-time Validation**  
  Validate map constraints before export to ensure consistency and correctness.

- **YAML Export**  
  Export maps in YAML format for use in downstream planners, simulators, or benchmarks.

- **Agent Management**  
  Add, remove, and manage multiple agents with unique identifiers and start positions.


## Visual Legend

| Element               | Representation   |
|----------------------|------------------|
| Empty cell            | White square     |
| Obstacle              | Black square     |
| Agent start           | Orange circle    |
| Non-task endpoint     | Green circle     |
| Pickup location       | Red square       |
| Delivery location     | Blue triangle    |

## Project Structure

```text
map-builder-MAPDs/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── setup.html         # Map setup page
│   └── index.html         # Main map builder page
└── static/
    ├── style.css          # Stylesheets
    ├── setup.js           # Setup page JavaScript
    └── script.js          # Main application JavaScript
```
## Installation

### Step 1: Navigate to Project Directory

```bash
cd /path/to/map-builder-MAPDs
```

### Step 2: Set Up Virtual Environment
```bash
python3 -m venv venv
```
Activate:
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```






