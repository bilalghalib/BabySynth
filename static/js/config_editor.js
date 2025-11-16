// BabySynth Config Editor

const socket = io();

const colorNoteMap = {
    'C': '#ff0000',
    'D': '#00ff00',
    'E': '#0000ff',
    'F': '#ffff00',
    'G': '#00ffff',
    'A': '#ff00ff',
    'B': '#808080'
};

let currentConfig = {
    name: 'ADGC',
    models: {},
    scales: { C_major: ['C', 'D', 'E', 'F', 'G', 'A', 'B'] },
    colors: {
        C: [255, 0, 0],
        D: [0, 255, 0],
        E: [0, 0, 255],
        F: [255, 255, 0],
        G: [0, 255, 255],
        A: [255, 0, 255],
        B: [128, 128, 128]
    },
    file_char_and_locations: {},
    file_colors: {},
    debounce: true
};

let gridState = Array(9).fill(null).map(() => Array(9).fill('x'));

// Initialize grid layout editor
function initLayoutGrid() {
    const grid = document.getElementById('config-layout-grid');
    grid.innerHTML = '';

    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const cell = document.createElement('div');
            cell.className = 'layout-btn';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.textContent = gridState[y][x];

            // Set background color based on note
            const char = gridState[y][x];
            if (char in colorNoteMap) {
                cell.style.backgroundColor = colorNoteMap[char];
                cell.style.color = '#fff';
            } else {
                cell.style.backgroundColor = '#141414';
                cell.style.color = '#666';
            }

            // Click to paint
            cell.addEventListener('click', () => paintCell(x, y));

            grid.appendChild(cell);
        }
    }
    updateLayoutPreview();
}

function paintCell(x, y) {
    const paintNote = document.getElementById('paint-note').value;
    gridState[y][x] = paintNote;
    initLayoutGrid(); // Redraw
}

function updateLayoutPreview() {
    const yamlPreview = gridState.map(row => row.join('')).join('\n  ');
    document.getElementById('layout-yaml-preview').textContent =
        `layout: |\n  ${yamlPreview}`;
}

// Color picker handlers
function initColorPickers() {
    const colorInputs = document.querySelectorAll('#color-editor input[type="color"]');
    colorInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const note = e.target.dataset.note;
            const color = hexToRgb(e.target.value);
            const textInput = e.target.nextElementSibling;
            textInput.value = `${color.r}, ${color.g}, ${color.b}`;

            // Update config
            currentConfig.colors[note] = [color.r, color.g, color.b];
            colorNoteMap[note] = e.target.value;

            // Update grid colors
            initLayoutGrid();
        });
    });
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

// Load config from server
document.getElementById('load-config')?.addEventListener('click', () => {
    const configPath = document.getElementById('config-select').value;
    socket.emit('load_config', { path: configPath });
});

socket.on('config_loaded', (data) => {
    if (data.success) {
        currentConfig = data.config;
        loadConfigIntoUI(data.config);
        alert('Config loaded successfully!');
    } else {
        alert('Error loading config: ' + data.error);
    }
});

function loadConfigIntoUI(config) {
    // Load layout if exists
    if (config.models) {
        const modelNames = Object.keys(config.models);
        if (modelNames.length > 0) {
            const firstModel = modelNames[0];
            const layout = config.models[firstModel].layout;
            if (layout) {
                const lines = layout.trim().split('\n');
                for (let y = 0; y < Math.min(9, lines.length); y++) {
                    for (let x = 0; x < Math.min(9, lines[y].length); x++) {
                        gridState[y][x] = lines[y][x];
                    }
                }
                document.getElementById('model-name').value = firstModel;
            }
        }
    }

    // Load colors
    if (config.colors) {
        Object.keys(config.colors).forEach(note => {
            const [r, g, b] = config.colors[note];
            const hex = rgbToHex(r, g, b);
            const colorInput = document.querySelector(`input[type="color"][data-note="${note}"]`);
            if (colorInput) {
                colorInput.value = hex;
                colorInput.nextElementSibling.value = `${r}, ${g}, ${b}`;
                colorNoteMap[note] = hex;
            }
        });
    }

    // Load raw YAML
    document.getElementById('raw-yaml-editor').value = jsyaml.dump(config);

    initLayoutGrid();
}

// Clear layout
document.getElementById('clear-layout')?.addEventListener('click', () => {
    gridState = Array(9).fill(null).map(() => Array(9).fill('x'));
    initLayoutGrid();
});

// Validate YAML
document.getElementById('validate-yaml')?.addEventListener('click', () => {
    const yamlText = document.getElementById('raw-yaml-editor').value;
    const resultDiv = document.getElementById('yaml-validation-result');

    try {
        const parsed = jsyaml.load(yamlText);
        currentConfig = parsed;
        resultDiv.innerHTML = '<p style="color: green;">✅ Valid YAML!</p>';
        loadConfigIntoUI(parsed);
    } catch (e) {
        resultDiv.innerHTML = `<p style="color: red;">❌ Invalid YAML: ${e.message}</p>`;
    }
});

// Save config
document.getElementById('save-config')?.addEventListener('click', () => {
    // Build config from UI
    const modelName = document.getElementById('model-name').value || 'ADGC';
    const layoutYaml = gridState.map(row => row.join('')).join('\n');

    currentConfig.models[modelName] = {
        layout: layoutYaml
    };

    // Get advanced features
    const animations = document.getElementById('animations-editor').value;
    const chords = document.getElementById('chords-editor').value;
    const themes = document.getElementById('themes-editor').value;
    const macros = document.getElementById('macros-editor').value;

    if (animations.trim()) {
        try {
            const animData = jsyaml.load(animations);
            currentConfig.animations = animData.animations;
        } catch (e) {
            console.error('Invalid animations YAML:', e);
        }
    }

    if (chords.trim()) {
        try {
            const chordsData = jsyaml.load(chords);
            currentConfig.chord_progressions = chordsData.chord_progressions;
        } catch (e) {
            console.error('Invalid chords YAML:', e);
        }
    }

    if (themes.trim()) {
        try {
            const themesData = jsyaml.load(themes);
            currentConfig.themes = themesData.themes;
        } catch (e) {
            console.error('Invalid themes YAML:', e);
        }
    }

    if (macros.trim()) {
        try {
            const macrosData = jsyaml.load(macros);
            currentConfig.macros = macrosData.macros;
        } catch (e) {
            console.error('Invalid macros YAML:', e);
        }
    }

    // Update raw editor
    document.getElementById('raw-yaml-editor').value = jsyaml.dump(currentConfig);

    // Send to server
    const configPath = document.getElementById('config-select').value;
    socket.emit('save_config', {
        path: configPath,
        config: currentConfig
    });
});

socket.on('config_saved', (data) => {
    if (data.success) {
        alert('✅ Configuration saved to ' + data.path);
    } else {
        alert('❌ Error saving: ' + data.error);
    }
});

// Apply config (hot reload)
document.getElementById('apply-config')?.addEventListener('click', () => {
    socket.emit('apply_config', { config: currentConfig });
});

socket.on('config_applied', (data) => {
    if (data.success) {
        alert('🚀 Configuration applied! Launchpad updated.');
    } else {
        alert('❌ Error applying config: ' + data.error);
    }
});

// New config
document.getElementById('new-config')?.addEventListener('click', () => {
    const name = prompt('Enter config name (without .yaml):');
    if (name) {
        currentConfig = {
            name: name,
            models: {},
            scales: { C_major: ['C', 'D', 'E', 'F', 'G', 'A', 'B'] },
            colors: {
                C: [255, 0, 0],
                D: [0, 255, 0],
                E: [0, 0, 255],
                F: [255, 255, 0],
                G: [0, 255, 255],
                A: [255, 0, 255],
                B: [128, 128, 128]
            },
            debounce: true
        };
        document.getElementById('raw-yaml-editor').value = jsyaml.dump(currentConfig);
        alert('New config created! Edit and save.');
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Config Editor');
    initLayoutGrid();
    initColorPickers();
});

socket.on('connect', () => {
    console.log('Connected to server');
});
