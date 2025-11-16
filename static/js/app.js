// BabySynth Web UI - Real-time Launchpad Monitor

// Initialize Socket.IO connection
const socket = io();

// Connection status handling
const statusIndicator = document.getElementById('connection-status');

socket.on('connect', () => {
    console.log('Connected to BabySynth server');
    statusIndicator.textContent = '🟢 Connected';
    statusIndicator.classList.add('connected');
    statusIndicator.classList.remove('disconnected');
});

socket.on('disconnect', () => {
    console.log('Disconnected from BabySynth server');
    statusIndicator.textContent = '🔴 Disconnected';
    statusIndicator.classList.add('disconnected');
    statusIndicator.classList.remove('connected');
});

// Initialize the grid
function initializeGrid() {
    const grid = document.getElementById('launchpad-grid');

    // Create 9x9 grid of LED buttons
    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const button = document.createElement('div');
            button.className = 'led-button';
            button.dataset.x = x;
            button.dataset.y = y;
            button.id = `led-${x}-${y}`;

            // Add click handler for potential remote control
            button.addEventListener('click', () => handleButtonClick(x, y));

            grid.appendChild(button);
        }
    }
}

// Handle button clicks (for future remote control feature)
function handleButtonClick(x, y) {
    console.log(`Button clicked: (${x}, ${y})`);
    // Emit button click event to server
    socket.emit('button_click', { x, y, action: 'press' });

    // Visual feedback
    const button = document.getElementById(`led-${x}-${y}`);
    button.classList.add('active');

    setTimeout(() => {
        button.classList.remove('active');
        socket.emit('button_click', { x, y, action: 'release' });
    }, 200);
}

// Update a single LED color
function updateLED(x, y, color) {
    const button = document.getElementById(`led-${x}-${y}`);
    if (button) {
        const [r, g, b] = color;
        button.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;

        // Add brightness effect for non-black colors
        if (r > 0 || g > 0 || b > 0) {
            button.style.boxShadow = `0 0 10px rgba(${r}, ${g}, ${b}, 0.6)`;
            button.classList.add('active');
        } else {
            button.style.boxShadow = 'none';
            button.classList.remove('active');
        }
    }
}

// Update entire grid
function updateGrid(gridData) {
    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            if (gridData[y] && gridData[y][x]) {
                const cellData = gridData[y][x];
                updateLED(cellData.x, cellData.y, cellData.color);
            }
        }
    }
}

// Socket event handlers
socket.on('led_update', (data) => {
    console.log('LED update:', data);
    updateLED(data.x, data.y, data.color);
});

socket.on('grid_update', (data) => {
    console.log('Grid update received');
    updateGrid(data.grid);
});

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing BabySynth Web UI');
    initializeGrid();
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Press 'R' to refresh/reconnect
    if (e.key === 'r' || e.key === 'R') {
        socket.disconnect();
        socket.connect();
    }

    // Press 'F' for fullscreen
    if (e.key === 'f' || e.key === 'F') {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
});
