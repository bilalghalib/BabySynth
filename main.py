"""
BabySynth - Main Entry Point
Initializes the LaunchpadSynth and handles button events.
"""
from concurrent.futures import ThreadPoolExecutor
from synth import LaunchpadSynth
import time
import sys

def main():
    config_file = 'config.yaml'
    try:
        synth = LaunchpadSynth(config_file)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        print("   Make sure your Launchpad Mini MK3 is connected and recognized by the OS.")
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=10) as executor:
        synth.start('C_major', 'ADGC')  # Use the correct model name from the YAML

        while True:
            button_event = synth.lp.panel.buttons().poll_for_event()
            if button_event:
                executor.submit(synth.handle_event, button_event)
            time.sleep(0.01)  # Small sleep to prevent high CPU usage

if __name__ == "__main__":
    main()
