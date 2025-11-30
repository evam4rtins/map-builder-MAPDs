# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import yaml
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SESSION_PERMANENT'] = False

@app.route('/')
def index():
    return redirect(url_for('setup'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        try:
            width = int(request.form.get('width', 20))
            height = int(request.form.get('height', 20))
            session['width'] = width
            session['height'] = height
            session.modified = True  
            return redirect(url_for('builder'))
        except Exception as e:
            return render_template('setup.html', error=str(e))
    
    return render_template('setup.html')

@app.route('/builder')
def builder():
    if not session.get('width') or not session.get('height'):
        return redirect(url_for('setup'))
    return render_template('index.html')

@app.route('/api/get_dimensions')
def get_dimensions():
    width = session.get('width', 20)
    height = session.get('height', 20)
    return jsonify({
        'width': width,
        'height': height
    })

@app.route('/api/resize_dimensions', methods=['POST'])
def resize_dimensions():
    """Resize the map dimensions"""
    try:
        data = request.json
        new_width = int(data.get('width', 20))
        new_height = int(data.get('height', 20))
        
        session['width'] = new_width
        session['height'] = new_height
        session.modified = True
        
        return jsonify({
            'status': 'success', 
            'message': f'Map resized to {new_width}x{new_height}',
            'width': new_width,
            'height': new_height
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
                       
@app.route('/api/reset_dimensions', methods=['POST'])
def reset_dimensions():
    """Reset dimensions and clear session"""
    session.pop('width', None)
    session.pop('height', None)
    return jsonify({'status': 'success'})

@app.route('/api/save_map', methods=['POST'])
def save_map():
    try:
        data = request.json
        errors = validate_map(data)
        if errors:
            return jsonify({"status": "error", "errors": errors})
        
        # Convert to YAML format with specific structure
        yaml_data = {
            "agents": [
                {"start": agent["start"], "name": agent["name"]} 
                for agent in data["agents"]
            ],
            "map": {
                "dimensions": [session['height'], session['width']],  # [rows, columns]
                "obstacles": [[row, col] for row, col in data["map"]["obstacles"]],
                "non_task_endpoints": [[row, col] for row, col in data["map"]["non_task_endpoints"]],
                "pickup_locations": [[row, col] for row, col in data["map"]["pickup_locations"]],
                "delivery_locations": [[row, col] for row, col in data["map"]["delivery_locations"]]
            }
        }
        
        # Custom YAML formatting to match the desired structure
        yaml_output = format_yaml_output(yaml_data)
        
        return jsonify({
            "status": "success", 
            "yaml": yaml_output,
            "filename": f"map_{session['height']}r_{session['width']}c.yaml"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "errors": [str(e)]})

def format_yaml_output(data):
    """Format YAML output to match the desired structure"""
    lines = []
    
    # Format agents section
    lines.append("agents:")
    for agent in data["agents"]:
        lines.append(f"-   start: [{agent['start'][0]}, {agent['start'][1]}]")
        lines.append(f"    name: {agent['name']}")
    
    # Format map section
    lines.append("")
    lines.append("map:")
    lines.append("    dimensions: [{}, {}]".format(data["map"]["dimensions"][0], data["map"]["dimensions"][1]))
    
    # Format obstacles with !!python/tuple
    lines.append("    obstacles:")
    for obstacle in data["map"]["obstacles"]:
        lines.append("    - !!python/tuple [{}, {}]".format(obstacle[0], obstacle[1]))
    
    # Format non_task_endpoints with !!python/tuple
    lines.append("")
    lines.append("    non_task_endpoints:")
    for endpoint in data["map"]["non_task_endpoints"]:
        lines.append("    - !!python/tuple [{}, {}]".format(endpoint[0], endpoint[1]))
    
    # Format pickup_locations with regular lists
    lines.append("")
    lines.append("    pickup_locations:")
    for pickup in data["map"]["pickup_locations"]:
        lines.append("    - [{}, {}]".format(pickup[0], pickup[1]))
    
    # Format delivery_locations with regular lists
    lines.append("")
    lines.append("    delivery_locations:")
    for delivery in data["map"]["delivery_locations"]:
        lines.append("    - [{}, {}]".format(delivery[0], delivery[1]))
    
    return "\n".join(lines)

@app.route('/api/load_example', methods=['GET'])
def load_example():
    """Load the example map structure"""
    example_data = {
        "agents": [{"name": "agent1", "start": [0, 0]}],
        "map": {
            "obstacles": [],
            "non_task_endpoints": [[0, 0]],
            "pickup_locations": [],
            "delivery_locations": []
        }
    }
    return jsonify(example_data)

def validate_map(data):
    errors = []
    width = session.get('width', 20)
    height = session.get('height', 20)
    
    # Check if we have at least one non-task endpoint per agent
    if len(data['map']['non_task_endpoints']) < len(data['agents']):
        errors.append(f"Not enough non-task endpoints: {len(data['map']['non_task_endpoints'])} endpoints for {len(data['agents'])} agents")
    
    # Check if all agent positions are valid (coordinates already in logical system)
    for agent in data['agents']:
        x, y = agent['start']
        if y < 0 or y >= width or x < 0 or x >= height:
            errors.append(f"Agent {agent['name']} at ({x}, {y}) is outside map boundaries (0-{width-1}, 0-{height-1})")
    
    # Check if all special locations are within map
    for loc_type in ['obstacles', 'non_task_endpoints', 'pickup_locations', 'delivery_locations']:
        for x, y in data['map'][loc_type]:
            if y < 0 or y >= width or x < 0 or x >= height:
                errors.append(f"{loc_type} location ({x}, {y}) is outside map boundaries (0-{width-1}, 0-{height-1})")
    
    return errors

if __name__ == '__main__':
    app.run(debug=True)