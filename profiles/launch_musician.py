#!/usr/bin/env python3
"""
BabySynth - Musician Profile Launcher
For performance practice, pattern discovery, and creative exploration.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrent.futures import ThreadPoolExecutor
from synth import LaunchpadSynth
from session_manager import SessionManager
import time
import signal

def main():
    # === CUSTOMIZE YOUR PROFILE HERE ===
    artist_name = input("Artist/stage name: ") or "Musician"
    session_type = input("Session type (practice/performance/experiment): ") or "practice"

    user_profile = f"{artist_name}_{session_type}"

    print(f"\n🎸 Starting BabySynth for {artist_name}")
    print(f"   Session: {session_type}")
    print(f"   Profile: {user_profile}")
    print(f"\n💡 Tips for musicians:")
    print(f"   • Let your hands discover patterns")
    print(f"   • Embrace constraints - limited options = creativity")
    print(f"   • Watch for embodied patterns (muscle memory)")
    print(f"   • Review rapid sequences in slow motion later")
    print(f"\n   Press Ctrl+C when done to save the session\n")

    config_file = 'config.yaml'
    session_manager = SessionManager()

    try:
        synth = LaunchpadSynth(config_file, session_manager=session_manager, user_profile=user_profile)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        print("   Make sure your Launchpad Mini MK3 is connected.")
        sys.exit(1)

    # Graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n🛑 Stopping BabySynth...")
        if session_manager.current_session_id:
            session_manager.end_session()
            session_id = session_manager.current_session_id
            summary = session_manager.get_session_summary(session_id)
            patterns = summary.get('patterns_detected', 0)

            print(f"\n✨ Session saved!")
            print(f"   Duration: {summary.get('duration', 0):.1f}s")
            print(f"   Events: {summary.get('total_events', 0)}")
            print(f"   Patterns discovered: {patterns}")
            print(f"\n   Analyze: python replay.py {session_id} --summary")
            print(f"   Review in slow-mo: python replay.py {session_id} --speed 0.5\n")
        synth.clear_grid()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    with ThreadPoolExecutor(max_workers=10) as executor:
        synth.start('C_major', 'ADGC')

        try:
            while True:
                button_event = synth.lp.panel.buttons().poll_for_event()
                if button_event:
                    executor.submit(synth.handle_event, button_event)
                time.sleep(0.01)
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
