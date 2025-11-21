#!/usr/bin/env python3
"""
BabySynth - Duet Mode Launcher
For parent-child duets, collaborative composition, or musical conversations.

Features:
- Turn-taking modes (free, strict, call-response, timed)
- Visual turn indicators (top row LEDs)
- Grid zones for each player
- Session recording with turn statistics
- Hot-reload configs during play
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrent.futures import ThreadPoolExecutor
from synth import LaunchpadSynth
from session_manager import SessionManager
from turn_taker import TurnTaker, TurnMode, GridZone
from config_reloader import ConfigReloader, ConfigSwitcher
import time
import signal


def main():
    print("\n🎵🎵 BabySynth Duet Mode")
    print("========================\n")

    # === DUET SETUP ===
    print("Who's playing today?\n")
    player1_name = input("Player 1 name: ") or "Player1"
    player2_name = input("Player 2 name: ") or "Player2"

    print("\n📋 Turn-Taking Modes:")
    print("  1. Free Play - Both players anytime (great for jamming)")
    print("  2. Strict Turns - One at a time (structured learning)")
    print("  3. Call & Response - Musical conversation (therapeutic/creative)")
    print("  4. Timed Turns - Each gets 10 seconds (fair sharing)")

    mode_choice = input("\nChoose mode (1-4): ") or "1"

    mode_map = {
        "1": TurnMode.FREE_PLAY,
        "2": TurnMode.STRICT_TURNS,
        "3": TurnMode.CALL_RESPONSE,
        "4": TurnMode.TIMED_TURNS
    }

    turn_mode = mode_map.get(mode_choice, TurnMode.FREE_PLAY)

    print(f"\n✓ Mode: {turn_mode.value}")
    print(f"✓ Players: {player1_name} (left) & {player2_name} (right)")

    # Grid zones
    print("\n🗺️  Grid Layout:")
    print(f"   {player1_name}: Left half (buttons on left)")
    print(f"   {player2_name}: Right half (buttons on right)")
    print(f"   Top row: Turn indicators")

    # Config
    config_file = 'config.yaml'
    user_profile = f"duet_{player1_name}_{player2_name}"

    # Optional: Set alternate config for A/B switching
    print("\n⚙️  Config Options:")
    print("   [Enter] Use default config")
    print("   [path] Specify config file path")
    alt_config = input("Alternate config for A/B switching (optional): ")

    # Session recording
    session_manager = SessionManager()

    try:
        synth = LaunchpadSynth(config_file, session_manager=session_manager, user_profile=user_profile)
    except RuntimeError as exc:
        print(f"\n❌ {exc}")
        print("   Make sure your Launchpad Mini MK3 is connected.")
        sys.exit(1)

    # Initialize turn-taker
    turn_taker = TurnTaker(synth.lp, synth.led_animator, session_manager)
    turn_taker.set_mode(turn_mode)
    turn_taker.set_player_zones(GridZone.LEFT_HALF, GridZone.RIGHT_HALF)

    # Set player colors
    turn_taker.set_player_colors(
        (255, 100, 100),  # Red for player 1
        (100, 100, 255)   # Blue for player 2
    )

    # Initialize config reloader
    config_reloader = ConfigReloader(synth, config_file)

    if alt_config and os.path.exists(alt_config):
        config_reloader.set_alternate_config(alt_config)
        print(f"   ✓ Alternate config set: {alt_config}")

    # Config switcher for control buttons
    config_switcher = ConfigSwitcher(config_reloader, synth.lp)

    # Start watching for config changes
    config_reloader.start_watching(check_interval=2.0)

    print("\n🎮 Controls:")
    print("   Top-right corner buttons:")
    print("   • Position (8,0): Toggle A/B configs")
    print("   • Position (7,0): Reload current config")
    print("   • Position (6,0): Cycle through all configs")
    print("\n💡 Tips:")
    if turn_mode == TurnMode.FREE_PLAY:
        print("   • Both players can play anytime - jam together!")
    elif turn_mode == TurnMode.STRICT_TURNS:
        print("   • Only the current player can press buttons")
        print("   • Watch the top row to see whose turn it is")
        print("   • Take turns to build a collaborative piece")
    elif turn_mode == TurnMode.CALL_RESPONSE:
        print("   • Player 1 plays a pattern, then Player 2 responds")
        print("   • Great for musical conversations!")
        print("   • Turn switches automatically after 2 seconds")
    elif turn_mode == TurnMode.TIMED_TURNS:
        print("   • Each player gets 10 seconds")
        print("   • Watch the top row for your turn indicator")

    print("\n   Press Ctrl+C when done\n")

    # Start synth
    with ThreadPoolExecutor(max_workers=10) as executor:
        synth.start('C_major', 'ADGC')

        # Show initial turn indicator
        turn_taker.update_turn_indicator()

        # Turn change callback
        def on_turn_change(old_player, new_player):
            print(f"   🔄 Turn: Player {old_player} → Player {new_player}")

        turn_taker.add_turn_change_callback(on_turn_change)

        # Config reload callback
        def on_config_reload(path, success):
            if success:
                print(f"   ✨ Config reloaded: {path}")
            else:
                print(f"   ❌ Config reload failed: {path}")

        config_reloader.add_reload_callback(on_config_reload)

        # Graceful shutdown
        def signal_handler(sig, frame):
            print("\n\n🛑 Stopping duet...")

            # Stop watching
            config_reloader.stop_watching()

            # Get turn statistics
            stats = turn_taker.get_turn_stats()

            if session_manager.current_session_id:
                session_manager.end_session()
                session_id = session_manager.current_session_id

                print(f"\n✨ Duet session saved!")
                print(f"   Session ID: {session_id}")

                # Show turn statistics
                if stats:
                    print(f"\n📊 Turn Statistics:")
                    for player, data in stats.items():
                        print(f"   {player.replace('_', ' ').title()}:")
                        print(f"      Turns: {data['turn_count']}")
                        print(f"      Total time: {data['total_time']:.1f}s")
                        print(f"      Avg turn: {data['avg_turn_duration']:.1f}s")

                print(f"\n   Replay: python replay.py {session_id}")

            synth.clear_grid()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Main event loop
        try:
            while True:
                button_event = synth.lp.panel.buttons().poll_for_event()

                if button_event:
                    from lpminimk3 import ButtonEvent

                    if button_event.type == ButtonEvent.PRESS:
                        x, y = button_event.button.x, button_event.button.y

                        # Check if it's a control button
                        if config_switcher.handle_button_press(x, y):
                            continue

                        # Check turn rules
                        button_player = turn_taker.get_player_for_button(x, y)

                        if button_player and turn_taker.can_player_press(x, y):
                            # Valid press - handle normally
                            executor.submit(synth.handle_event, button_event)

                            # In call-response, pressing switches turn
                            if turn_mode == TurnMode.CALL_RESPONSE:
                                turn_taker.request_turn_change(button_player)

                        else:
                            # Invalid press - visual feedback
                            if turn_mode != TurnMode.FREE_PLAY:
                                print(f"   ⚠️  Not {['', player1_name, player2_name][turn_taker.current_player]}'s turn!")

                                # Flash the correct zone
                                turn_taker.highlight_player_zone(turn_taker.current_player)

                    else:
                        # Release events always handled
                        executor.submit(synth.handle_event, button_event)

                time.sleep(0.01)

        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
