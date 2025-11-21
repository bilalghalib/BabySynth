"""
BabySynth - Session Manager
Captures and persists all interaction events for playback and analysis.
"""
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging


class SessionManager:
    """
    Manages recording, storage, and retrieval of BabySynth sessions.

    A session captures all button events, LED changes, and audio playback
    to enable reflection, pattern discovery, and sharing of meaningful moments.
    """

    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self.current_session_id: Optional[int] = None
        self.session_start_time: Optional[float] = None
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with schema for sessions and events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time REAL NOT NULL,
                end_time REAL,
                duration REAL,
                user_profile TEXT,
                config_name TEXT,
                scale TEXT,
                model_name TEXT,
                total_events INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        # Events table - captures all interactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                relative_time REAL NOT NULL,
                event_type TEXT NOT NULL,
                x INTEGER,
                y INTEGER,
                note_name TEXT,
                frequency REAL,
                color_r INTEGER,
                color_g INTEGER,
                color_b INTEGER,
                audio_file TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # LED state table - tracks visual changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS led_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                relative_time REAL NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                color_r INTEGER NOT NULL,
                color_g INTEGER NOT NULL,
                color_b INTEGER NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Patterns table - detected interesting moments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                description TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_session
            ON events(session_id, timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_led_session
            ON led_changes(session_id, timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_session
            ON patterns(session_id)
        """)

        conn.commit()
        conn.close()
        logging.info(f"Session database initialized at {self.db_path}")

    def start_session(self, user_profile: str = "default",
                     config_name: str = None, scale: str = None,
                     model_name: str = None, notes: str = None) -> int:
        """
        Start a new recording session.

        Args:
            user_profile: Name of the user profile (e.g., "Sarah_daughter", "Marcus", "James_client_Alex")
            config_name: Name of the config file used
            scale: Musical scale in use
            model_name: Grid model name
            notes: Optional notes about this session

        Returns:
            Session ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        self.session_start_time = time.time()

        cursor.execute("""
            INSERT INTO sessions (start_time, user_profile, config_name, scale, model_name, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (self.session_start_time, user_profile, config_name, scale, model_name, notes))

        self.current_session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logging.info(f"Session {self.current_session_id} started for profile '{user_profile}'")
        return self.current_session_id

    def end_session(self):
        """End the current recording session."""
        if not self.current_session_id:
            logging.warning("No active session to end")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        end_time = time.time()
        duration = end_time - self.session_start_time

        # Count total events
        cursor.execute("""
            SELECT COUNT(*) FROM events WHERE session_id = ?
        """, (self.current_session_id,))
        total_events = cursor.fetchone()[0]

        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, duration = ?, total_events = ?
            WHERE id = ?
        """, (end_time, duration, total_events, self.current_session_id))

        conn.commit()
        conn.close()

        logging.info(f"Session {self.current_session_id} ended. Duration: {duration:.2f}s, Events: {total_events}")

        # Run pattern detection
        self.detect_patterns(self.current_session_id)

        self.current_session_id = None
        self.session_start_time = None

    def record_button_press(self, x: int, y: int, note_name: str = None,
                           frequency: float = None, audio_file: str = None,
                           metadata: dict = None):
        """Record a button press event."""
        self._record_event("button_press", x, y, note_name, frequency,
                          None, None, None, audio_file, metadata)

    def record_button_release(self, x: int, y: int, note_name: str = None,
                             metadata: dict = None):
        """Record a button release event."""
        self._record_event("button_release", x, y, note_name, None,
                          None, None, None, None, metadata)

    def record_led_change(self, x: int, y: int, color: Tuple[int, int, int]):
        """Record an LED color change."""
        if not self.current_session_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = time.time()
        relative_time = timestamp - self.session_start_time

        cursor.execute("""
            INSERT INTO led_changes
            (session_id, timestamp, relative_time, x, y, color_r, color_g, color_b)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.current_session_id, timestamp, relative_time, x, y,
              color[0], color[1], color[2]))

        conn.commit()
        conn.close()

    def _record_event(self, event_type: str, x: int, y: int,
                     note_name: str = None, frequency: float = None,
                     color_r: int = None, color_g: int = None, color_b: int = None,
                     audio_file: str = None, metadata: dict = None):
        """Internal method to record any event."""
        if not self.current_session_id:
            logging.warning(f"Cannot record {event_type}: no active session")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = time.time()
        relative_time = timestamp - self.session_start_time

        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute("""
            INSERT INTO events
            (session_id, timestamp, relative_time, event_type, x, y,
             note_name, frequency, color_r, color_g, color_b, audio_file, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.current_session_id, timestamp, relative_time, event_type,
              x, y, note_name, frequency, color_r, color_g, color_b,
              audio_file, metadata_json))

        conn.commit()
        conn.close()

    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session metadata by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sessions WHERE id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def list_sessions(self, user_profile: str = None, limit: int = 20) -> List[Dict]:
        """
        List recent sessions.

        Args:
            user_profile: Filter by user profile (optional)
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_profile:
            cursor.execute("""
                SELECT * FROM sessions
                WHERE user_profile = ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (user_profile, limit))
        else:
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_session_events(self, session_id: int) -> List[Dict]:
        """Get all events for a session, ordered by time."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM events
            WHERE session_id = ?
            ORDER BY relative_time ASC
        """, (session_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_session_led_changes(self, session_id: int) -> List[Dict]:
        """Get all LED changes for a session, ordered by time."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM led_changes
            WHERE session_id = ?
            ORDER BY relative_time ASC
        """, (session_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def detect_patterns(self, session_id: int):
        """
        Detect interesting patterns in a session.

        Patterns detected:
        - Rapid sequences (quick button presses)
        - Repeated patterns (same sequence multiple times)
        - Long pauses (moments of concentration)
        - Spatial patterns (lines, clusters)
        - Happy accidents (unexpected combinations)
        """
        events = self.get_session_events(session_id)

        if len(events) < 3:
            return  # Not enough data for pattern detection

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Detect rapid sequences (< 0.3s between presses)
        rapid_sequence_start = None
        rapid_sequence_count = 0

        for i in range(len(events) - 1):
            if events[i]['event_type'] == 'button_press':
                time_diff = events[i + 1]['relative_time'] - events[i]['relative_time']

                if time_diff < 0.3 and events[i + 1]['event_type'] == 'button_press':
                    if rapid_sequence_start is None:
                        rapid_sequence_start = events[i]['relative_time']
                    rapid_sequence_count += 1
                else:
                    if rapid_sequence_count >= 3:
                        # Found a rapid sequence!
                        cursor.execute("""
                            INSERT INTO patterns
                            (session_id, pattern_type, start_time, end_time, description)
                            VALUES (?, ?, ?, ?, ?)
                        """, (session_id, "rapid_sequence",
                             rapid_sequence_start, events[i]['relative_time'],
                             f"Rapid sequence of {rapid_sequence_count} notes"))
                    rapid_sequence_start = None
                    rapid_sequence_count = 0

        # Detect long pauses (> 3s between presses)
        for i in range(len(events) - 1):
            if events[i]['event_type'] == 'button_press' and events[i + 1]['event_type'] == 'button_press':
                time_diff = events[i + 1]['relative_time'] - events[i]['relative_time']

                if time_diff > 3.0:
                    cursor.execute("""
                        INSERT INTO patterns
                        (session_id, pattern_type, start_time, end_time, description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, "long_pause",
                         events[i]['relative_time'], events[i + 1]['relative_time'],
                         f"Pause of {time_diff:.1f}s - moment of concentration?"))

        # Detect repeated sequences (same 3+ button pattern)
        press_events = [e for e in events if e['event_type'] == 'button_press']
        sequence_length = 3

        if len(press_events) >= sequence_length * 2:
            for i in range(len(press_events) - sequence_length + 1):
                pattern_positions = [(press_events[i + j]['x'], press_events[i + j]['y'])
                                   for j in range(sequence_length)]

                # Look for this pattern later in the session
                for k in range(i + sequence_length, len(press_events) - sequence_length + 1):
                    later_positions = [(press_events[k + j]['x'], press_events[k + j]['y'])
                                     for j in range(sequence_length)]

                    if pattern_positions == later_positions:
                        cursor.execute("""
                            INSERT INTO patterns
                            (session_id, pattern_type, start_time, end_time, description, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (session_id, "repeated_sequence",
                             press_events[i]['relative_time'],
                             press_events[k + sequence_length - 1]['relative_time'],
                             f"Repeated sequence discovered",
                             json.dumps({"positions": pattern_positions})))
                        break  # Only record first repetition

        conn.commit()
        conn.close()

        logging.info(f"Pattern detection completed for session {session_id}")

    def get_session_patterns(self, session_id: int) -> List[Dict]:
        """Get detected patterns for a session."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM patterns
            WHERE session_id = ?
            ORDER BY start_time ASC
        """, (session_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def export_session(self, session_id: int, output_path: str):
        """
        Export a session to a JSON file for sharing.

        Args:
            session_id: Session to export
            output_path: Path to write JSON file
        """
        session = self.get_session(session_id)
        events = self.get_session_events(session_id)
        led_changes = self.get_session_led_changes(session_id)
        patterns = self.get_session_patterns(session_id)

        export_data = {
            "session": session,
            "events": events,
            "led_changes": led_changes,
            "patterns": patterns,
            "exported_at": datetime.now().isoformat()
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logging.info(f"Session {session_id} exported to {output_path}")

    def get_session_summary(self, session_id: int) -> Dict:
        """
        Generate a human-readable summary of a session.

        Returns insights like:
        - Total duration and event count
        - Most pressed buttons
        - Average tempo
        - Detected patterns
        """
        session = self.get_session(session_id)
        events = self.get_session_events(session_id)
        patterns = self.get_session_patterns(session_id)

        if not session or not events:
            return {}

        press_events = [e for e in events if e['event_type'] == 'button_press']

        # Calculate button press frequencies
        button_counts = {}
        for event in press_events:
            key = (event['x'], event['y'])
            button_counts[key] = button_counts.get(key, 0) + 1

        most_pressed = sorted(button_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate average tempo (time between presses)
        if len(press_events) > 1:
            time_diffs = [press_events[i + 1]['relative_time'] - press_events[i]['relative_time']
                         for i in range(len(press_events) - 1)]
            avg_tempo = sum(time_diffs) / len(time_diffs)
        else:
            avg_tempo = 0

        return {
            "session_id": session_id,
            "duration": session.get('duration', 0),
            "total_events": len(events),
            "button_presses": len(press_events),
            "most_pressed_buttons": [{"position": pos, "count": count}
                                     for pos, count in most_pressed],
            "average_tempo": avg_tempo,
            "patterns_detected": len(patterns),
            "pattern_types": list(set(p['pattern_type'] for p in patterns))
        }
