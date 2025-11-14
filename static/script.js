class MapBuilder {
    constructor() {
        this.width = 20;
        this.height = 20;
        this.currentTool = 'obstacle';
        this.cellSize = 25;
        this.data = {
            agents: [],
            map: {
                obstacles: [],
                non_task_endpoints: [],
                pickup_locations: [],
                delivery_locations: []
            }
        };
        
        console.log("🔄 MapBuilder constructor called");
        this.init();
    }

    async init() {
        console.log("🚀 MapBuilder initialization started");
        
        try {
            await this.loadDimensions();
            console.log("✅ Dimensions loaded:", this.width, "x", this.height);
            
            this.setupEventListeners();
            console.log("✅ Event listeners setup");
            
            this.createGrid();
            console.log("✅ Grid created");
            
            this.updateDisplay();
            console.log("✅ MapBuilder fully initialized");
            
        } catch (error) {
            console.error("❌ MapBuilder initialization failed:", error);
        }
    }

    async loadDimensions() {
        try {
            console.log("📡 Fetching dimensions from API...");
            const response = await fetch('/api/get_dimensions');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const dimensions = await response.json();
            console.log("📋 Received dimensions:", dimensions);
            
            this.width = dimensions.width;
            this.height = dimensions.height;
            
            const dimensionsElement = document.getElementById('current-dimensions');
            if (dimensionsElement) {
                dimensionsElement.textContent = `${this.width}×${this.height}`;
            } else {
                console.warn("⚠️ current-dimensions element not found");
            }
            
        } catch (error) {
            console.error('❌ Failed to load dimensions:', error);
            // Use default dimensions as fallback
            this.width = 20;
            this.height = 20;
        }
    }

    setupEventListeners() {
        console.log("🔧 Setting up event listeners...");
        
        // Tool buttons
        const toolButtons = document.querySelectorAll('.tool-btn');
        if (toolButtons.length === 0) {
            console.warn("⚠️ No tool buttons found");
        } else {
            toolButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.setTool(e.target.dataset.tool);
                });
            });
        }

        // Action buttons
        this.setupButton('reset-btn', () => this.resetDimensions());
        this.setupButton('validate-btn', () => this.validateMap());
        this.setupButton('export-btn', () => this.exportMap());
        this.setupButton('clear-btn', () => this.clearMap());
        this.setupButton('load-example-btn', () => this.loadExample());
        this.setupButton('add-agent-btn', () => this.showAgentModal());

        // Agent form
        const agentForm = document.getElementById('agent-form');
        if (agentForm) {
            agentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addAgent();
            });
        }

        this.setupButton('cancel-agent-btn', () => this.hideAgentModal());
    }

    setupButton(id, handler) {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', handler);
        } else {
            console.warn(`⚠️ Button with id '${id}' not found`);
        }
    }

    setTool(tool) {
        console.log("🎯 Setting tool to:", tool);
        this.currentTool = tool;
        
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeButton = document.querySelector(`[data-tool="${tool}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        const toolElement = document.getElementById('current-tool');
        if (toolElement) {
            toolElement.textContent = `Current: ${this.getToolName(tool)}`;
        }
    }

    getToolName(tool) {
        const names = {
            'obstacle': 'Obstacle',
            'endpoint': 'Non-task Endpoint',
            'pickup': 'Pickup Location',
            'delivery': 'Delivery Location',
            'agent': 'Agent Start',
            'erase': 'Erase'
        };
        return names[tool] || tool;
    }

    createGrid() {
        const grid = document.getElementById('map-grid');
        if (!grid) {
            console.error('❌ map-grid element not found!');
            return;
        }

        console.log(`🔄 Creating grid: ${this.width} x ${this.height}`);
        
        // Clear existing grid
        grid.innerHTML = '';
        
        // Apply visible styling to grid container
        grid.style.border = '3px solid #007bff';
        grid.style.background = '#f8f9fa';
        grid.style.padding = '10px';
        grid.style.margin = '10px 0';
        grid.style.minHeight = '50px';
        grid.style.overflow = 'auto';
        
        for (let y = 0; y < this.height; y++) {
            const row = document.createElement('div');
            row.className = 'grid-row';
            row.style.display = 'flex';
            row.style.justifyContent = 'center';
            
            for (let x = 0; x < this.width; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell empty';
                cell.dataset.x = x;
                cell.dataset.y = y;
                
                // Apply visible styling to each cell
                cell.style.width = `${this.cellSize}px`;
                cell.style.height = `${this.cellSize}px`;
                cell.style.border = '1px solid #666';
                cell.style.backgroundColor = '#ffffff';
                cell.style.margin = '1px';
                cell.style.display = 'flex';
                cell.style.alignItems = 'center';
                cell.style.justifyContent = 'center';
                cell.style.fontSize = '8px';
                cell.style.cursor = 'pointer';
                cell.style.transition = 'background-color 0.2s';
                
                // Add coordinates for debugging (remove in production)
                cell.textContent = `${x},${y}`;
                
                cell.addEventListener('click', () => this.handleCellClick(x, y));
                cell.addEventListener('mouseenter', (e) => {
                    e.target.style.backgroundColor = '#e9ecef';
                    const coordsElement = document.getElementById('cell-coords');
                    if (coordsElement) {
                        coordsElement.textContent = `(${x}, ${y})`;
                    }
                });
                cell.addEventListener('mouseleave', (e) => {
                    const cellType = this.getCellType(x, y);
                    e.target.style.backgroundColor = this.getCellColor(cellType);
                });
                
                row.appendChild(cell);
            }
            grid.appendChild(row);
        }
        
        console.log(`✅ Grid created with ${this.width * this.height} cells`);
        this.syncGridFromData();
    }

    getCellColor(cellType) {
        const colors = {
            'empty': '#ffffff',
            'obstacle': '#333333',
            'endpoint': '#007bff',
            'pickup': '#28a745',
            'delivery': '#dc3545',
            'agent': '#ffc107'
        };
        return colors[cellType] || '#ffffff';
    }

    handleCellClick(x, y) {
        console.log(`🖱️ Cell clicked: (${x}, ${y}) with tool: ${this.currentTool}`);
        
        if (this.currentTool === 'erase') {
            this.removeCellFromAllTypes(x, y);
        } else if (this.currentTool === 'agent') {
            this.showAgentModal(x, y);
        } else {
            this.removeCellFromAllTypes(x, y);
            
            const typeKey = this.getDataKeyForTool(this.currentTool);
            if (typeKey && !this.data.map[typeKey].some(pos => pos[0] === x && pos[1] === y)) {
                this.data.map[typeKey].push([x, y]);
                console.log(`✅ Added ${this.currentTool} at (${x}, ${y})`);
            }
        }
        
        this.syncGridFromData();
    }

    getDataKeyForTool(tool) {
        const mapping = {
            'obstacle': 'obstacles',
            'endpoint': 'non_task_endpoints',
            'pickup': 'pickup_locations',
            'delivery': 'delivery_locations'
        };
        return mapping[tool];
    }

    removeCellFromAllTypes(x, y) {
        const types = ['obstacles', 'non_task_endpoints', 'pickup_locations', 'delivery_locations'];
        types.forEach(type => {
            const initialLength = this.data.map[type].length;
            this.data.map[type] = this.data.map[type].filter(pos => !(pos[0] === x && pos[1] === y));
            if (this.data.map[type].length !== initialLength) {
                console.log(`🗑️ Removed from ${type} at (${x}, ${y})`);
            }
        });
    }

    getCellType(x, y) {
        if (this.data.map.obstacles.some(pos => pos[0] === x && pos[1] === y)) return 'obstacle';
        if (this.data.map.non_task_endpoints.some(pos => pos[0] === x && pos[1] === y)) return 'endpoint';
        if (this.data.map.pickup_locations.some(pos => pos[0] === x && pos[1] === y)) return 'pickup';
        if (this.data.map.delivery_locations.some(pos => pos[0] === x && pos[1] === y)) return 'delivery';
        if (this.data.agents.some(agent => agent.start[0] === x && agent.start[1] === y)) return 'agent';
        return 'empty';
    }

    syncGridFromData() {
        console.log("🔄 Syncing grid from data...");
        
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
                if (cell) {
                    const cellType = this.getCellType(x, y);
                    cell.className = 'cell ' + cellType;
                    cell.style.backgroundColor = this.getCellColor(cellType);
                    cell.style.color = cellType === 'obstacle' ? '#ffffff' : '#000000';
                }
            }
        }
        this.updateAgentsList();
    }

    showAgentModal(x = null, y = null) {
        console.log("👤 Showing agent modal at:", x, y);
        const modal = document.getElementById('agent-modal');
        if (modal) {
            if (x !== null && y !== null) {
                document.getElementById('agent-x').value = x;
                document.getElementById('agent-y').value = y;
            }
            modal.style.display = 'block';
        } else {
            console.error('❌ Agent modal not found');
        }
    }

    hideAgentModal() {
        console.log("👤 Hiding agent modal");
        const modal = document.getElementById('agent-modal');
        if (modal) {
            modal.style.display = 'none';
            document.getElementById('agent-form').reset();
        }
    }

    addAgent() {
        const name = document.getElementById('agent-name').value;
        const x = parseInt(document.getElementById('agent-x').value);
        const y = parseInt(document.getElementById('agent-y').value);
        
        console.log(`👤 Adding agent: ${name} at (${x}, ${y})`);
        
        if (x >= this.width || y >= this.height) {
            alert('Agent position is outside map boundaries');
            return;
        }
        
        if (this.data.agents.some(agent => agent.name === name)) {
            alert('Agent name must be unique');
            return;
        }
        
        this.data.agents.push({ name: name, start: [x, y] });
        this.hideAgentModal();
        this.syncGridFromData();
    }

    updateAgentsList() {
        const list = document.getElementById('agents-list');
        if (!list) {
            console.warn('⚠️ agents-list element not found');
            return;
        }
        
        list.innerHTML = '';
        
        this.data.agents.forEach(agent => {
            const item = document.createElement('div');
            item.className = 'agent-item';
            item.innerHTML = `
                ${agent.name} (${agent.start[0]}, ${agent.start[1]}) 
                <button onclick="mapBuilder.removeAgent('${agent.name}')">×</button>
            `;
            list.appendChild(item);
        });
    }

    removeAgent(name) {
        console.log(`👤 Removing agent: ${name}`);
        this.data.agents = this.data.agents.filter(agent => agent.name !== name);
        this.syncGridFromData();
    }

    async validateMap() {
        console.log("🔍 Validating map...");
        try {
            const response = await fetch('/api/save_map', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.data)
            });
            const result = await response.json();
            this.showValidationResults(result);
        } catch (error) {
            console.error('❌ Validation error:', error);
            this.showValidationResults({ status: 'error', errors: ['Network error: ' + error.message] });
        }
    }

    async exportMap() {
        console.log("💾 Exporting map...");
        try {
            const response = await fetch('/api/save_map', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.data)
            });
            const result = await response.json();
            
            if (result.status === 'success') {
                this.downloadYAML(result.yaml, result.filename);
                this.showValidationResults({ status: 'success', errors: [] });
            } else {
                this.showValidationResults(result);
            }
        } catch (error) {
            console.error('❌ Export error:', error);
            this.showValidationResults({ status: 'error', errors: ['Export failed: ' + error.message] });
        }
    }

    downloadYAML(yamlContent, filename) {
        console.log(`📥 Downloading: ${filename}`);
        const blob = new Blob([yamlContent], { type: 'application/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showValidationResults(result) {
        const resultsDiv = document.getElementById('validation-results');
        if (!resultsDiv) {
            console.warn('⚠️ validation-results element not found');
            return;
        }
        
        resultsDiv.innerHTML = '';
        
        if (result.status === 'success') {
            resultsDiv.className = 'validation-results success';
            resultsDiv.innerHTML = '<strong>✓ Validation Successful!</strong><br>Map meets all constraints.';
        } else {
            resultsDiv.className = 'validation-results error';
            let html = '<strong>✗ Validation Failed:</strong><ul>';
            result.errors.forEach(error => html += `<li>${error}</li>`);
            html += '</ul>';
            resultsDiv.innerHTML = html;
        }
    }

    clearMap() {
        if (confirm('Are you sure you want to clear the entire map?')) {
            console.log("🗑️ Clearing map...");
            this.data = {
                agents: [],
                map: { obstacles: [], non_task_endpoints: [], pickup_locations: [], delivery_locations: [] }
            };
            this.syncGridFromData();
        }
    }

    async loadExample() {
        console.log("📚 Loading example...");
        try {
            const response = await fetch('/api/load_example');
            const exampleData = await response.json();
            this.data = exampleData;
            this.syncGridFromData();
        } catch (error) {
            console.error('❌ Load example error:', error);
            alert('Failed to load example: ' + error.message);
        }
    }

    async resetDimensions() {
        if (confirm('Are you sure you want to reset map dimensions? This will clear the current map.')) {
            console.log("🔄 Resetting dimensions...");
            try {
                await fetch('/api/reset_dimensions', { method: 'POST' });
                window.location.href = '/setup';
            } catch (error) {
                console.error('❌ Reset dimensions error:', error);
                alert('Failed to reset dimensions: ' + error.message);
            }
        }
    }

    updateDisplay() {
        const dimensionsElement = document.getElementById('current-dimensions');
        if (dimensionsElement) {
            dimensionsElement.textContent = `${this.width}×${this.height}`;
        }
        console.log(`📊 Display updated: ${this.width}x${this.height}`);
    }
}

// Initialize MapBuilder when DOM is fully loaded
let mapBuilder;

document.addEventListener('DOMContentLoaded', () => {
    console.log("📄 DOM fully loaded, initializing MapBuilder...");
    mapBuilder = new MapBuilder();
});

// Additional debug: Check if grid is visible after a short delay
setTimeout(() => {
    const grid = document.getElementById('map-grid');
    if (grid) {
        console.log("🔍 Grid check:", {
            exists: true,
            children: grid.children.length,
            visible: grid.offsetParent !== null,
            dimensions: {
                width: grid.offsetWidth,
                height: grid.offsetHeight
            }
        });
        
        // Force visible styling if grid is empty
        if (grid.children.length === 0) {
            console.warn("⚠️ Grid is empty, applying emergency styling");
            grid.innerHTML = '<div style="padding: 20px; text-align: center; color: red; font-weight: bold;">GRID FAILED TO LOAD - Check console for errors</div>';
        }
    } else {
        console.error("❌ map-grid element not found in DOM");
    }
}, 1000);