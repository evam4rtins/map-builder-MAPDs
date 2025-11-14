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
            session.modified = True  # Ensure session is saved
            print(f"✅ Saved dimensions to session: {width}x{height}")
            return redirect(url_for('builder'))
        except Exception as e:
            print(f"❌ Error saving dimensions: {e}")
            return render_template('setup.html', error=str(e))
    
    return render_template('setup.html')

@app.route('/builder')
def builder():
    # Debug: Check what's in session
    print(f"🔍 Session data in /builder: width={session.get('width')}, height={session.get('height')}")
    
    if not session.get('width') or not session.get('height'):
        print("❌ No dimensions found, redirecting to setup")
        return redirect(url_for('setup'))
    
    print(f"✅ Rendering builder with dimensions: {session['width']}x{session['height']}")
    return render_template('index.html')

@app.route('/api/get_dimensions')
def get_dimensions():
    width = session.get('width', 20)
    height = session.get('height', 20)
    print(f"📡 API returning dimensions: {width}x{height}")
    return jsonify({
        'width': width,
        'height': height
    })


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
        
        # Validate the map
        errors = validate_map(data)
        if errors:
            return jsonify({"status": "error", "errors": errors})
        
        # Convert to YAML format
        yaml_data = {
            "agents": data["agents"],
            "map": {
                "dimensions": [session['width'], session['height']],
                "obstacles": [[x, y] for x, y in data["map"]["obstacles"]],
                "non_task_endpoints": [[x, y] for x, y in data["map"]["non_task_endpoints"]],
                "pickup_locations": [[x, y] for x, y in data["map"]["pickup_locations"]],
                "delivery_locations": [[x, y] for x, y in data["map"]["delivery_locations"]]
            }
        }
        
        # Return YAML as downloadable content
        yaml_output = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
        return jsonify({
            "status": "success", 
            "yaml": yaml_output,
            "filename": f"map_{session['width']}x{session['height']}.yaml"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "errors": [str(e)]})

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
    """Validate map against constraints"""
    errors = []
    width = session.get('width', 20)
    height = session.get('height', 20)
    
    # Check if we have at least one non-task endpoint per agent
    if len(data['map']['non_task_endpoints']) < len(data['agents']):
        errors.append(f"Not enough non-task endpoints: {len(data['map']['non_task_endpoints'])} endpoints for {len(data['agents'])} agents")
    
    # Check if all agent positions are valid
    for agent in data['agents']:
        x, y = agent['start']
        if x >= width or y >= height:
            errors.append(f"Agent {agent['name']} is outside map boundaries")
    
    # Check if all special locations are within map
    for loc_type in ['obstacles', 'non_task_endpoints', 'pickup_locations', 'delivery_locations']:
        for x, y in data['map'][loc_type]:
            if x >= width or y >= height:
                errors.append(f"{loc_type} location ({x}, {y}) is outside map boundaries")
    
    return errors

if __name__ == '__main__':
    app.run(debug=True)