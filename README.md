# Map Builder – Research Tool

A web-based tool for creating and managing maps with agents, obstacles, and task locations. Built with Flask and vanilla JavaScript.

## Features

- **Interactive Map Grid:** Create maps with customizable dimensions
- **Multiple Tools:** Place obstacles, endpoints, pickup/delivery locations, and agents
- **Real-time Validation:** Validate map constraints before export
- **YAML Export:** Export maps in YAML format for research use
- **Agent Management:** Add and manage multiple agents with unique start positions

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
python3 app.py
`






