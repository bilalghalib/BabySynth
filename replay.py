#!/usr/bin/env python3
"""
BabySynth - Session Replay Tool
Review, analyze, and replay your BabySynth sessions.

Examples:
  python replay.py --list                    # List all sessions
  python replay.py --list --profile Sarah    # List sessions for Sarah
  python replay.py 5                         # Replay session #5
  python replay.py 5 --speed 0.5             # Replay at half speed
  python replay.py 5 --summary               # Show summary only
  python replay.py 5 --export session5.json  # Export session
  python replay.py 5 --ascii video.txt       # Generate ASCII animation
"""
import argparse
import sys
from datetime import datetime
from session_manager import SessionManager
from playback_engine import PlaybackEngine


def list_sessions(session_manager: SessionManager, user_profile=None, limit=20):
    """Display a list of recorded sessions."""
    sessions = session_manager.list_sessions(user_profile=user_profile, limit=limit)

    if not sessions:
        print("\n📭 No sessions found.")
        if user_profile:
            print(f"   (No sessions for profile '{user_profile}')")
        print("   Start recording by running: python main.py\n")
        return

    print("\n" + "="*80)
    print("  RECORDED SESSIONS")
    print("="*80)

    for session in sessions:
        session_id = session['id']
        profile = session['user_profile']
        duration = session.get('duration', 0)
        events = session.get('total_events', 0)
        start_dt = datetime.fromtimestamp(session['start_time'])
        date_str = start_dt.strftime('%Y-%m-%d %H:%M')

        # Get summary for more details
        summary = session_manager.get_session_summary(session_id)
        patterns = summary.get('patterns_detected', 0)

        status = "✨" if patterns > 0 else "🎵"

        print(f"\n  {status} Session #{session_id} - {profile}")
        print(f"     Date: {date_str}")
        print(f"     Duration: {duration:.1f}s | Events: {events} | Patterns: {patterns}")

        # Show notes if any
        if session.get('notes'):
            print(f"     Notes: {session['notes']}")

    print("\n" + "="*80)
    print(f"  Total: {len(sessions)} session(s)")
    print("="*80)
    print("\n  💡 Replay a session: python replay.py <session_id>")
    print("     View summary: python replay.py <session_id> --summary\n")


def show_summary(session_manager: SessionManager, playback_engine: PlaybackEngine, session_id: int):
    """Display detailed summary of a session."""
    playback_engine.display_session_summary(session_id)


def replay_session(session_manager: SessionManager, playback_engine: PlaybackEngine,
                  session_id: int, speed: float = 1.0):
    """Replay a session on the Launchpad."""
    try:
        playback_engine.init_launchpad()
    except RuntimeError as e:
        print(f"\n❌ Cannot replay: {e}")
        print("   Launchpad required for playback.")
        print("   Use --summary or --ascii for visualization without hardware.\n")
        return

    # Show summary first
    show_summary(session_manager, playback_engine, session_id)

    input("   Press Enter to start playback (or Ctrl+C to cancel)...")

    try:
        playback_engine.play_session(session_id, speed=speed, show_patterns=True)
    except KeyboardInterrupt:
        print("\n   Playback cancelled\n")


def export_session(session_manager: SessionManager, session_id: int, output_path: str):
    """Export a session to JSON."""
    try:
        session_manager.export_session(session_id, output_path)
        print(f"\n✨ Session {session_id} exported to {output_path}\n")
    except Exception as e:
        print(f"\n❌ Export failed: {e}\n")


def generate_ascii_video(session_manager: SessionManager, playback_engine: PlaybackEngine,
                        session_id: int, output_path: str):
    """Generate ASCII art animation of a session."""
    try:
        playback_engine.generate_session_video_ascii(session_id, output_path)
    except Exception as e:
        print(f"\n❌ ASCII generation failed: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="🎵 BabySynth Session Replay - Relive your musical moments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                    List all sessions
  %(prog)s --list --profile Sarah    List sessions for a specific profile
  %(prog)s 5                         Replay session #5
  %(prog)s 5 --speed 0.5             Replay at half speed (slow motion!)
  %(prog)s 5 --summary               Show session summary and patterns
  %(prog)s 5 --export output.json    Export session data
  %(prog)s 5 --ascii animation.txt   Generate ASCII art animation

Values served:
  👶 For parents: See your child's discovery moments and developmental progress
  🎸 For musicians: Analyze embodied patterns and performance flow
  🧑‍⚕️ For therapists: Review client engagement and therapeutic milestones
        """
    )

    parser.add_argument('session_id', nargs='?', type=int,
                       help='Session ID to replay or analyze')
    parser.add_argument('--list', action='store_true',
                       help='List all recorded sessions')
    parser.add_argument('--profile', type=str,
                       help='Filter sessions by user profile')
    parser.add_argument('--summary', action='store_true',
                       help='Show session summary without replaying')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Playback speed (0.25 to 4.0, default: 1.0)')
    parser.add_argument('--export', type=str, metavar='FILE',
                       help='Export session to JSON file')
    parser.add_argument('--ascii', type=str, metavar='FILE',
                       help='Generate ASCII art animation')
    parser.add_argument('--limit', type=int, default=20,
                       help='Maximum number of sessions to list (default: 20)')
    parser.add_argument('--db', type=str, default='sessions.db',
                       help='Path to session database (default: sessions.db)')

    args = parser.parse_args()

    # Initialize session manager
    session_manager = SessionManager(db_path=args.db)
    playback_engine = PlaybackEngine(session_manager)

    # Handle --list command
    if args.list:
        list_sessions(session_manager, user_profile=args.profile, limit=args.limit)
        return

    # Need a session ID for other commands
    if args.session_id is None:
        parser.print_help()
        print("\n💡 Tip: Start with --list to see available sessions\n")
        return

    session_id = args.session_id

    # Verify session exists
    session = session_manager.get_session(session_id)
    if not session:
        print(f"\n❌ Session {session_id} not found")
        print("   Run: python replay.py --list\n")
        sys.exit(1)

    # Handle export
    if args.export:
        export_session(session_manager, session_id, args.export)
        return

    # Handle ASCII generation
    if args.ascii:
        generate_ascii_video(session_manager, playback_engine, session_id, args.ascii)
        return

    # Handle summary
    if args.summary:
        show_summary(session_manager, playback_engine, session_id)
        return

    # Default: replay the session
    replay_session(session_manager, playback_engine, session_id, speed=args.speed)


if __name__ == "__main__":
    main()
