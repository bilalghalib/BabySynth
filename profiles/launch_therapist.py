#!/usr/bin/env python3
"""
BabySynth - Therapist Profile Launcher
For music therapy sessions with client progress tracking.
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
    therapist_name = input("Therapist name: ") or "Therapist"
    client_id = input("Client ID/pseudonym: ") or "Client"
    session_notes = input("Session goal/notes (optional): ") or ""

    user_profile = f"{therapist_name}_client_{client_id}"

    print(f"\n🧑‍⚕️ Starting BabySynth therapy session")
    print(f"   Therapist: {therapist_name}")
    print(f"   Client: {client_id}")
    print(f"   Profile: {user_profile}")
    if session_notes:
        print(f"   Notes: {session_notes}")
    print(f"\n💡 Tips for therapeutic sessions:")
    print(f"   • No pressure - all button presses are valid")
    print(f"   • Watch for subtle engagement signals")
    print(f"   • Long pauses indicate processing time")
    print(f"   • Repeated patterns show learning/comfort")
    print(f"   • Review session for progress documentation")
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
        print("\n\n🛑 Ending therapy session...")
        if session_manager.current_session_id:
            session_id = session_manager.current_session_id

            # Add session notes if provided
            if session_notes:
                import sqlite3
                conn = sqlite3.connect(session_manager.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE sessions SET notes = ? WHERE id = ?",
                             (session_notes, session_id))
                conn.commit()
                conn.close()

            session_manager.end_session()
            summary = session_manager.get_session_summary(session_id)
            patterns = session_manager.get_session_patterns(session_id)

            print(f"\n✨ Session documented!")
            print(f"   Duration: {summary.get('duration', 0):.1f}s")
            print(f"   Client interactions: {summary.get('button_presses', 0)}")
            print(f"   Avg response time: {summary.get('average_tempo', 0):.2f}s")

            # Highlight therapeutic milestones
            if patterns:
                print(f"\n   🎯 Therapeutic observations:")
                for pattern in patterns:
                    if pattern['pattern_type'] == 'long_pause':
                        print(f"      • Processing moment at {pattern['start_time']:.1f}s")
                    elif pattern['pattern_type'] == 'repeated_sequence':
                        print(f"      • Learning pattern at {pattern['start_time']:.1f}s")
                    elif pattern['pattern_type'] == 'rapid_sequence':
                        print(f"      • Engaged/excited at {pattern['start_time']:.1f}s")

            print(f"\n   Review: python replay.py {session_id} --summary")
            print(f"   Export: python replay.py {session_id} --export client_{client_id}_session.json\n")
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
