"""
BabySynth - Web UI Enabled Main Entry Point
Runs the synthesizer with a web-based visual monitor.
"""
from concurrent.futures import ThreadPoolExecutor
from synth import LaunchpadSynth
from web_ui import start_web_server_thread, WebUIBroadcaster
import time
import sys

def main():
    print("=" * 60)
    print("🎹 BabySynth - Web UI Mode")
    print("=" * 60)

    # Start the web server in the background
    print("\n📡 Starting web server...")
    web_thread = start_web_server_thread(host='0.0.0.0', port=5000)

    # Give the web server a moment to start
    time.sleep(2)

    # Get the broadcaster instance
    broadcaster = WebUIBroadcaster()

    # Initialize synth with web broadcaster
    print("\n🎵 Initializing synthesizer...")
    config_file = 'config.yaml'
    try:
        synth = LaunchpadSynth(config_file, web_broadcaster=broadcaster)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your Launchpad Mini MK3 is connected!")
        sys.exit(1)

    print("\n✅ Setup complete!")
    print("\n" + "=" * 60)
    print("READY TO PLAY!")
    print("=" * 60)
    print("\n📱 Open your browser to: http://localhost:5000")
    print("   (or http://YOUR_IP:5000 from another device)")
    print("\n🎮 Press buttons on your Launchpad to make music!")
    print("   The web UI will show what's happening in real-time.")
    print("\n⌨️  Press Ctrl+C to exit\n")

    # Start the synthesizer
    with ThreadPoolExecutor(max_workers=10) as executor:
        synth.start('C_major', 'ADGC')  # Use the correct model name from the YAML

        try:
            while True:
                button_event = synth.lp.panel.buttons().poll_for_event()
                if button_event:
                    executor.submit(synth.handle_event, button_event)
                time.sleep(0.01)  # Small sleep to prevent high CPU usage
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for playing!")
            sys.exit(0)

if __name__ == "__main__":
    main()
