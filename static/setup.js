class MapSetup {
    constructor() {
        const widthInput = document.getElementById('width');
        const heightInput = document.getElementById('height');

        this.width = parseInt(widthInput.value) || 20;
        this.height = parseInt(heightInput.value) || 20;
        this.init();

    }

    init() {
        this.updatePreview();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('width').addEventListener('input', () => {
            this.updateDimensions();
        });

        document.getElementById('height').addEventListener('input', () => {
            this.updateDimensions();
        });

        document.querySelector('form').addEventListener('submit', (e) => {
            if (!this.validateDimensions()) {
                e.preventDefault();
                alert('Please enter valid dimensions (positive numbers for both width and height)');
            }
        });
    }

    updateDimensions() {
        console.log("UPDATE dimensions")
        this.width = parseInt(document.getElementById('width').value);
        this.height = parseInt(document.getElementById('height').value);
        
        this.width = Math.max(1, this.width);
        this.height = Math.max(1, this.height);
        
        document.getElementById('width').value = this.width;
        document.getElementById('height').value = this.height;
        
        this.updatePreview();
    }

    validateDimensions() {
        return this.width > 0 && this.height > 0;
    }

    updatePreview() {
        console.log("UPDATE")
        const preview = document.getElementById('grid-preview');
        const previewInfo = document.getElementById('preview-info');
        
        preview.innerHTML = '';
        
        const maxDisplaySize = 200;
        const cellSize = Math.max(2, Math.floor(maxDisplaySize / Math.max(this.width, this.height)));
        
        for (let y = 0; y < this.height; y++) {
            const row = document.createElement('div');
            row.className = 'preview-row';
            
            for (let x = 0; x < this.width; x++) {
                const cell = document.createElement('div');
                cell.className = 'preview-cell';
                cell.style.width = `${cellSize}px`;
                cell.style.height = `${cellSize}px`;
                row.appendChild(cell);
            }
            preview.appendChild(row);
        }
        
        previewInfo.innerHTML = `Grid size: <span id="preview-size">${this.width}×${this.height}</span> cells`;
        preview.style.border = '2px solid #2c3e50';
        preview.style.background = '#ecf0f1';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MapSetup();
});