"""
BabySynth - Web UI Server
Flask-based web server that provides a visual representation of the Launchpad grid.
Shows real-time LED colors so you can monitor what the baby is doing.
"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'babysynth-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store the current LED state (9x9 grid)
led_state = [[{'x': x, 'y': y, 'color': [0, 0, 0]} for x in range(9)] for y in range(9)]

class WebUIBroadcaster:
    """Singleton class to broadcast LED changes to all connected web clients"""
    _instance = None
    _socketio = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebUIBroadcaster, cls).__new__(cls)
        return cls._instance

    def set_socketio(self, socketio_instance):
        """Set the SocketIO instance for broadcasting"""
        self._socketio = socketio_instance

    def update_led(self, x, y, color):
        """Update a single LED and broadcast to all clients"""
        global led_state
        if 0 <= x < 9 and 0 <= y < 9:
            led_state[y][x] = {'x': x, 'y': y, 'color': list(color)}
            if self._socketio:
                self._socketio.emit('led_update', {
                    'x': x,
                    'y': y,
                    'color': list(color)
                })

    def update_grid(self, grid_data):
        """Update entire grid and broadcast to all clients"""
        global led_state
        led_state = grid_data
        if self._socketio:
            self._socketio.emit('grid_update', {'grid': grid_data})

# Create singleton instance
broadcaster = WebUIBroadcaster()

@app.route('/')
def index():
    """Serve the main web UI page"""
    return render_template('index.html')

@app.route('/editor')
def editor():
    """Serve the audio engine editor page"""
    return render_template('editor.html')

@socketio.on('connect')
def handle_connect():
    """Handle new client connection - send current LED state"""
    print('Client connected to web UI')
    emit('grid_update', {'grid': led_state})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected from web UI')

@socketio.on('button_click')
def handle_button_click(data):
    """Handle button clicks from the web UI (for remote control)"""
    x = data.get('x')
    y = data.get('y')
    action = data.get('action', 'press')
    print(f'Web UI button {action}: ({x}, {y})')
    # This can be extended to trigger actual button events on the synth

@socketio.on('update_settings')
def handle_settings_update(data):
    """Handle audio engine settings updates from the editor"""
    print(f'Settings update received: {data}')
    # TODO: Apply settings to the synth
    emit('settings_applied', {'status': 'success'})

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """Start the web server"""
    broadcaster.set_socketio(socketio)
    print(f'\n🌐 Web UI available at: http://localhost:{port}')
    print('   Open this URL in your browser to see the Launchpad grid\n')
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

def start_web_server_thread(host='0.0.0.0', port=5000):
    """Start the web server in a background thread"""
    broadcaster.set_socketio(socketio)
    thread = threading.Thread(target=run_web_server, args=(host, port, False), daemon=True)
    thread.start()
    print(f'\n🌐 Web UI starting at: http://localhost:{port}')
    print('   Open this URL in your browser to see the Launchpad grid\n')
    return thread

if __name__ == '__main__':
    run_web_server(debug=True)
