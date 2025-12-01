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

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_map(data):
    """Efficiently validate all map constraints"""
    errors = []
    width = session.get('width', 20)
    height = session.get('height', 20)
    
    obstacles = set((x, y) for x, y in data['map']['obstacles'])
    endpoints = set((x, y) for x, y in data['map']['non_task_endpoints'])
    pickups = set((x, y) for x, y in data['map']['pickup_locations'])
    deliveries = set((x, y) for x, y in data['map']['delivery_locations'])
    
    # 1. Boundary checks using vectorized approach
    errors.extend(check_boundaries(data, width, height))
    
    # 2. Overlap checks
    errors.extend(check_overlaps(obstacles, endpoints, pickups, deliveries))
    
    # 3. Agent-specific constraints
    errors.extend(check_agent_constraints(data['agents'], endpoints, width, height))
    
    # 4. Connectivity checks (only if basic constraints pass)
    if not errors:
        # 4a. Check overall map connectivity (no isolated islands)
        if not is_map_connected(obstacles, width, height):
            errors.append("Map is not fully connected - obstacles create isolated areas that cannot be reached")
        
        # 4b. Check all 6 pairwise connectivity constraints from PDF
        errors.extend(check_all_connectivity_constraints(
            obstacles, endpoints, pickups, deliveries, width, height
        ))
    
    return errors

def check_boundaries(data, width, height):
    """Check all coordinates are within map boundaries"""
    errors = []
    all_locations = []
    
    for loc_type in ['obstacles', 'non_task_endpoints', 'pickup_locations', 'delivery_locations']:
        all_locations.extend(data['map'][loc_type])
    
    for x, y in all_locations:
        if not (0 <= x < height and 0 <= y < width):
            errors.append(f"Location ({x}, {y}) is outside map boundaries (0-{height-1}, 0-{width-1})")
    
    for agent in data['agents']:
        x, y = agent['start']
        if not (0 <= x < height and 0 <= y < width):
            errors.append(f"Agent {agent['name']} at ({x}, {y}) is outside map boundaries")
    
    return errors

def check_overlaps(obstacles, endpoints, pickups, deliveries):
    """Check for invalid overlaps between location types"""
    errors = []
    
    for loc_set, name in [(endpoints, "non-task endpoints"), 
                          (pickups, "pickup locations"), 
                          (deliveries, "delivery locations")]:
        overlaps = obstacles.intersection(loc_set)
        if overlaps:
            errors.append(f"Obstacles overlap with {name} at: {list(overlaps)}")
    
    return errors

def check_agent_constraints(agents, endpoints, width, height):
    """Validate agent-specific constraints"""
    errors = []
    agent_names = set()
    
    for agent in agents:
        # Unique names
        if agent['name'] in agent_names:
            errors.append(f"Duplicate agent name: {agent['name']}")
        agent_names.add(agent['name'])
        
        # Start position must be an endpoint
        start_pos = tuple(agent['start'])
        if start_pos not in endpoints:
            errors.append(f"Agent {agent['name']} start position {start_pos} must be a non-task endpoint")
    
    # At least one endpoint per agent
    if len(endpoints) < len(agents):
        errors.append(f"Not enough non-task endpoints: {len(endpoints)} endpoints for {len(agents)} agents")
    
    return errors

# ============================================================================
# CONNECTIVITY CONSTRAINTS 
# ============================================================================

def check_all_connectivity_constraints(obstacles, endpoints, pickups, deliveries, width, height):
    """
    Check ALL 6 connectivity constraints from the PDF.
    For EACH PAIR, path must avoid ALL OTHER special locations.
    """
    errors = []
    
    obstacles_set = set(obstacles)
    endpoints_set = set(endpoints)
    pickups_set = set(pickups)
    deliveries_set = set(deliveries)
    
    all_special_locations = obstacles_set.union(endpoints_set, pickups_set, deliveries_set)
    
    # 1. Endpoint ↔ Endpoint pairs
    errors.extend(check_pairs_strict(
        endpoints_set, "non-task endpoints",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    # 2. Pickup ↔ Pickup pairs
    errors.extend(check_pairs_strict(
        pickups_set, "pickup locations",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    # 3. Delivery ↔ Delivery pairs
    errors.extend(check_pairs_strict(
        deliveries_set, "delivery locations",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    # 4. Pickup ↔ Delivery pairs 
    errors.extend(check_between_sets_strict(
        pickups_set, deliveries_set, "pickup and delivery locations",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    # 5. Pickup ↔ Endpoint pairs 
    errors.extend(check_between_sets_strict(
        pickups_set, endpoints_set, "pickup and endpoint locations",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    # 6. Delivery ↔ Endpoint pairs 
    errors.extend(check_between_sets_strict(
        deliveries_set, endpoints_set, "delivery and endpoint locations",
        all_special_locations, obstacles_set, endpoints_set, pickups_set, deliveries_set,
        width, height
    ))
    
    return errors


def check_pairs_strict(locations_set, location_name, all_special_locations,
                       obstacles_set, endpoints_set, pickups_set, deliveries_set,
                       width, height):
    """
    Check connectivity between all pairs WITHIN the same set.
    Example: endpoint ↔ endpoint, pickup ↔ pickup, delivery ↔ delivery
    """
    errors = []
    locations_list = list(locations_set)
    
    if len(locations_list) < 2:
        return errors
    
    for i in range(len(locations_list)):
        for j in range(i + 1, len(locations_list)):
            start = locations_list[i]
            end = locations_list[j]
            
            # What to avoid: ALL special locations EXCEPT these two
            avoid_set = all_special_locations.copy()
            avoid_set.discard(start)  # Remove start if it's in the set
            avoid_set.discard(end)    # Remove end if it's in the set
            
            # Check if path exists
            if not has_path_avoiding(start, end, avoid_set, width, height):
                errors.append(
                    f"No path between {location_name} {start} and {end} "
                    f"that avoids all other special locations"
                )
    
    return errors


def check_between_sets_strict(set1, set2, location_name, all_special_locations,
                              obstacles_set, endpoints_set, pickups_set, deliveries_set,
                              width, height):
    """
    Check connectivity between ALL pairs from set1 to set2.
    Example: pickup ↔ delivery, pickup ↔ endpoint, delivery ↔ endpoint
    """
    errors = []
    
    # If either set is empty, no pairs to check
    if not set1 or not set2:
        return errors
    
    for start in set1:
        for end in set2:
            # Skip if same location (shouldn't happen between different sets)
            if start == end:
                continue
            
            # What to avoid: ALL special locations EXCEPT these two
            avoid_set = all_special_locations.copy()
            avoid_set.discard(start)  # Remove start if it's in the set
            avoid_set.discard(end)    # Remove end if it's in the set
            
            # Check if path exists
            if not has_path_avoiding(start, end, avoid_set, width, height):
                errors.append(
                    f"No path between {location_name} {start} and {end} "
                    f"that avoids all other special locations"
                )
    
    return errors


def has_path_avoiding(start, end, avoid_set, width, height):
    """
    BFS that finds path avoiding specified cells.
    The path CAN include start and end positions.
    Returns True if path exists, False otherwise.
    """
    # If start or end is itself an avoided cell (shouldn't happen with our logic)
    if start in avoid_set or end in avoid_set:
        return False
    
    # Same cell
    if start == end:
        return True
    
    visited = [[False] * width for _ in range(height)]
    queue = [start]
    visited[start[0]][start[1]] = True
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    
    while queue:
        x, y = queue.pop(0)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check boundaries
            if not (0 <= nx < height and 0 <= ny < width):
                continue
            
            # Check if visited
            if visited[nx][ny]:
                continue
            
            # Check if this is an avoided cell
            if (nx, ny) in avoid_set:
                continue
            
            # Found the destination!
            if (nx, ny) == end:
                return True
            
            # Mark as visited and continue searching
            visited[nx][ny] = True
            queue.append((nx, ny))
    
    return False

def is_map_connected(obstacles, width, height):
    """
    Check if the entire map is connected (no islands created by obstacles).
    Returns True if all non-obstacle cells are reachable from each other.
    """
    # Create visited matrix
    visited = [[False] * width for _ in range(height)]
    
    # Find first non-obstacle cell to start BFS
    start = None
    for x in range(height):
        for y in range(width):
            if (x, y) not in obstacles:
                start = (x, y)
                break
        if start:
            break
    
    if not start:
        return True  # All cells are obstacles, technically "connected" as obstacles
    
    # BFS from start position
    queue = [start]
    visited[start[0]][start[1]] = True
    count = 1  # Count reachable non-obstacle cells
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    while queue:
        x, y = queue.pop(0)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check boundaries
            if not (0 <= nx < height and 0 <= ny < width):
                continue
            
            # Check if visited
            if visited[nx][ny]:
                continue
            
            # Check if obstacle
            if (nx, ny) in obstacles:
                continue
            
            # This is a reachable non-obstacle cell
            visited[nx][ny] = True
            queue.append((nx, ny))
            count += 1
    
    # Count total non-obstacle cells
    total_non_obstacles = (width * height) - len(obstacles)
    return count == total_non_obstacles


if __name__ == '__main__':
    app.run(debug=True)