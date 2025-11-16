// BabySynth Audio Engine Editor

const socket = io();

// Current settings
const settings = {
    waveform: 'sine',
    envelope: {
        attack: 0.1,
        decay: 0.2,
        sustain: 0.7,
        release: 0.3
    },
    effects: {
        reverb: { mix: 0, size: 50 },
        delay: { mix: 0, time: 0.5 },
        filter: { cutoff: 1000, resonance: 0 }
    },
    layout: {}
};

// Initialize waveform selector
function initWaveformSelector() {
    const buttons = document.querySelectorAll('.waveform-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            settings.waveform = btn.dataset.waveform;
            console.log('Waveform changed to:', settings.waveform);
        });
    });
}

// Initialize ADSR controls
function initADSRControls() {
    const controls = {
        attack: document.getElementById('attack'),
        decay: document.getElementById('decay'),
        sustain: document.getElementById('sustain'),
        release: document.getElementById('release')
    };

    Object.keys(controls).forEach(param => {
        const slider = controls[param];
        const valueSpan = document.getElementById(`${param}-value`);

        slider.addEventListener('input', () => {
            const value = parseFloat(slider.value);
            settings.envelope[param] = value;
            valueSpan.textContent = param === 'sustain' ? value.toFixed(1) : `${value.toFixed(1)}s`;
            drawEnvelope();
        });
    });

    drawEnvelope();
}

// Draw ADSR envelope visualization
function drawEnvelope() {
    const canvas = document.getElementById('envelope-canvas');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
        const y = (height / 10) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Calculate envelope points
    const env = settings.envelope;
    const totalTime = env.attack + env.decay + 0.5 + env.release; // 0.5s for sustain display
    const scale = width / totalTime;

    const points = [
        { x: 0, y: height },
        { x: env.attack * scale, y: 10 },
        { x: (env.attack + env.decay) * scale, y: height - (env.sustain * (height - 20)) },
        { x: (env.attack + env.decay + 0.5) * scale, y: height - (env.sustain * (height - 20)) },
        { x: width, y: height }
    ];

    // Draw envelope curve
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);

    points.forEach((point, i) => {
        if (i > 0) ctx.lineTo(point.x, point.y);
    });

    ctx.stroke();

    // Fill under curve
    ctx.fillStyle = 'rgba(102, 126, 234, 0.1)';
    ctx.beginPath();
    ctx.moveTo(0, height);
    points.forEach(point => ctx.lineTo(point.x, point.y));
    ctx.lineTo(width, height);
    ctx.fill();

    // Draw labels
    ctx.fillStyle = '#333';
    ctx.font = '12px sans-serif';
    ctx.fillText('A', points[1].x - 5, height - 5);
    ctx.fillText('D', points[2].x - 5, height - 5);
    ctx.fillText('S', points[3].x - 20, height - 5);
    ctx.fillText('R', width - 15, height - 5);
}

// Initialize effects controls
function initEffectsControls() {
    const effectControls = [
        { id: 'reverb-mix', param: 'reverb', sub: 'mix', suffix: '%' },
        { id: 'reverb-size', param: 'reverb', sub: 'size', suffix: '%' },
        { id: 'delay-mix', param: 'delay', sub: 'mix', suffix: '%' },
        { id: 'delay-time', param: 'delay', sub: 'time', suffix: 's' },
        { id: 'filter-cutoff', param: 'filter', sub: 'cutoff', suffix: 'Hz' },
        { id: 'filter-res', param: 'filter', sub: 'resonance', suffix: '%' }
    ];

    effectControls.forEach(({ id, param, sub, suffix }) => {
        const slider = document.getElementById(id);
        const valueSpan = document.getElementById(`${id}-value`);

        slider.addEventListener('input', () => {
            const value = parseFloat(slider.value);
            settings.effects[param][sub] = value;
            valueSpan.textContent = `${value}${suffix}`;
        });
    });
}

// Initialize layout grid
function initLayoutGrid() {
    const grid = document.getElementById('layout-grid');
    const noteColors = {
        'C': 'rgb(255, 0, 0)',
        'D': 'rgb(0, 255, 0)',
        'E': 'rgb(0, 0, 255)',
        'F': 'rgb(255, 255, 0)',
        'G': 'rgb(0, 255, 255)',
        'A': 'rgb(255, 0, 255)',
        'B': 'rgb(128, 128, 128)'
    };

    // Create 9x9 grid
    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const btn = document.createElement('div');
            btn.className = 'layout-btn';
            btn.dataset.x = x;
            btn.dataset.y = y;

            btn.addEventListener('click', () => {
                const note = document.getElementById('note-selector').value;
                if (note) {
                    btn.style.backgroundColor = noteColors[note];
                    settings.layout[`${x},${y}`] = note;
                } else {
                    btn.style.backgroundColor = 'rgb(20, 20, 20)';
                    delete settings.layout[`${x},${y}`];
                }
            });

            grid.appendChild(btn);
        }
    }
}

// Save layout
document.getElementById('save-layout')?.addEventListener('click', () => {
    const layoutData = JSON.stringify(settings, null, 2);
    const blob = new Blob([layoutData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'babysynth-config.json';
    a.click();
    URL.revokeObjectURL(url);
    alert('Layout saved! Download starting...');
});

// Load preset
document.getElementById('load-preset')?.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const loadedSettings = JSON.parse(event.target.result);
                Object.assign(settings, loadedSettings);
                alert('Preset loaded successfully!');
                // TODO: Update UI with loaded settings
            } catch (err) {
                alert('Error loading preset: ' + err.message);
            }
        };
        reader.readAsText(file);
    });
    input.click();
});

// Apply settings
document.getElementById('apply-settings')?.addEventListener('click', () => {
    console.log('Applying settings:', settings);
    socket.emit('update_settings', settings);
    alert('Settings applied! They will take effect on next note play.');
});

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Audio Engine Editor');
    initWaveformSelector();
    initADSRControls();
    initEffectsControls();
    initLayoutGrid();
});

// Handle connection status
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});
