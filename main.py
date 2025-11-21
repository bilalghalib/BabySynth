"""
BabySynth - Main Entry Point
Initializes the LaunchpadSynth and handles button events.
"""
from concurrent.futures import ThreadPoolExecutor
from synth import LaunchpadSynth
from session_manager import SessionManager
import time
import sys
import signal

def main():
    config_file = 'config.yaml'

    # Enable session recording
    session_manager = SessionManager()
    user_profile = "default"  # You can customize this (e.g., "Sarah_daughter", "Marcus", "James_client_Alex")

    try:
        synth = LaunchpadSynth(config_file, session_manager=session_manager, user_profile=user_profile)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        print("   Make sure your Launchpad Mini MK3 is connected and recognized by the OS.")
        sys.exit(1)

    # Graceful shutdown handler
    def signal_handler(sig, frame):
        print("\n\n🛑 Stopping BabySynth...")
        if session_manager and session_manager.current_session_id:
            session_manager.end_session()
            session_id = session_manager.current_session_id or "last"
            print(f"✨ Session saved! Run 'python replay.py --list' to see your sessions")
            print(f"   Replay this session with: python replay.py {session_id}")
        synth.clear_grid()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    with ThreadPoolExecutor(max_workers=10) as executor:
        synth.start('C_major', 'ADGC')  # Use the correct model name from the YAML

        try:
            while True:
                button_event = synth.lp.panel.buttons().poll_for_event()
                if button_event:
                    executor.submit(synth.handle_event, button_event)
                time.sleep(0.01)  # Small sleep to prevent high CPU usage
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
