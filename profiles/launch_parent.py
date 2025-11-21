#!/usr/bin/env python3
"""
BabySynth - Parent Profile Launcher
For tracking your child's musical development and discovery moments.
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
    parent_name = input("Parent name: ") or "Parent"
    child_name = input("Child's name: ") or "Child"
    child_age = input("Child's age (optional): ") or ""

    user_profile = f"{parent_name}_{child_name}"
    if child_age:
        user_profile += f"_age{child_age}"

    print(f"\n👶 Starting BabySynth for {child_name}")
    print(f"   Profile: {user_profile}")
    print(f"\n💡 Tips for parent-child sessions:")
    print(f"   • Let your child lead - follow their curiosity")
    print(f"   • Watch for moments of concentration (long pauses)")
    print(f"   • Celebrate happy accidents")
    print(f"   • Review sessions later to see developmental progress")
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
            print(f"\n✨ Session saved for {child_name}!")
            print(f"   Review with: python replay.py {session_id} --summary")
            print(f"   Replay with: python replay.py {session_id}\n")
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
