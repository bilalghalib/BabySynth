"""
BabySynth - Hot Config Reloader
Enables live configuration changes without restarting the synth.

Supports:
- File watcher for automatic reload
- A/B config switching via button press
- Smooth transitions between configs
- Backup/restore on reload failure
"""
import os
import time
import threading
import yaml
import logging
from typing import Callable, Optional, List
from pathlib import Path
import copy


class ConfigReloader:
    """
    Manages live configuration reloading.

    Features:
    - Watch config file for changes
    - Hot-reload without restart
    - A/B config switching
    - Graceful error handling
    - Transition animations
    """

    def __init__(self, synth, initial_config_path: str):
        self.synth = synth
        self.current_config_path = initial_config_path
        self.alternate_config_path = None

        # Watch state
        self.watching = False
        self.watch_thread = None
        self.last_modified_time = 0

        # Config history
        self.config_history = []
        self.max_history = 10

        # Callbacks
        self.on_reload_callbacks = []

        # Lock for thread safety
        self.lock = threading.Lock()

        # Track last known good config
        self.last_good_config = None

        self._update_modified_time()

    def _update_modified_time(self):
        """Update the last modified time of the config file."""
        try:
            self.last_modified_time = os.path.getmtime(self.current_config_path)
        except OSError:
            pass

    def start_watching(self, check_interval: float = 1.0):
        """Start watching config file for changes."""
        if self.watching:
            logging.warning("Already watching config file")
            return

        self.watching = True

        def watch_loop():
            logging.info(f"👀 Watching {self.current_config_path} for changes...")
            while self.watching:
                try:
                    current_mtime = os.path.getmtime(self.current_config_path)
                    if current_mtime > self.last_modified_time:
                        logging.info(f"📝 Config file changed! Reloading...")
                        self.last_modified_time = current_mtime
                        self.reload_config()
                except Exception as e:
                    logging.error(f"Error watching config: {e}")

                time.sleep(check_interval)

        self.watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self.watch_thread.start()

    def stop_watching(self):
        """Stop watching config file."""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2.0)

    def reload_config(self, config_path: str = None, smooth_transition: bool = True):
        """
        Reload configuration from file.

        Args:
            config_path: Path to config file (None = use current)
            smooth_transition: If True, fade out/in during reload
        """
        with self.lock:
            if config_path is None:
                config_path = self.current_config_path

            try:
                # Save current config as backup
                old_config = {
                    'notes': copy.deepcopy(self.synth.notes),
                    'audio_files': copy.deepcopy(self.synth.audio_files),
                    'model_name': self.synth.model_name,
                    'scales': copy.deepcopy(self.synth.scales),
                    'colors': copy.deepcopy(self.synth.colors)
                }

                # Smooth transition: fade out
                if smooth_transition:
                    self._transition_fade_out()

                # Load new config
                logging.info(f"Loading config from {config_path}")
                self.synth.load_config(config_path)

                # Re-initialize with new config
                # Determine scale and model from config
                scale = list(self.synth.scales.keys())[0] if self.synth.scales else 'C_major'
                model = list(self.synth.models.keys())[0] if self.synth.models else 'ADGC'

                self.synth.assign_notes_and_files(scale, model)

                # Smooth transition: fade in
                if smooth_transition:
                    self._transition_fade_in()

                # Update success
                self.last_good_config = config_path
                self.current_config_path = config_path

                # Add to history
                self.config_history.append({
                    'path': config_path,
                    'timestamp': time.time(),
                    'success': True
                })

                if len(self.config_history) > self.max_history:
                    self.config_history.pop(0)

                logging.info(f"✅ Config reloaded successfully!")

                # Notify callbacks
                for callback in self.on_reload_callbacks:
                    callback(config_path, True)

            except Exception as e:
                logging.error(f"❌ Config reload failed: {e}")

                # Restore old config
                try:
                    self.synth.notes = old_config['notes']
                    self.synth.audio_files = old_config['audio_files']
                    self.synth.model_name = old_config['model_name']
                    self.synth.scales = old_config['scales']
                    self.synth.colors = old_config['colors']
                    logging.info("Restored previous config")
                except:
                    logging.error("Failed to restore config!")

                # Record failure
                self.config_history.append({
                    'path': config_path,
                    'timestamp': time.time(),
                    'success': False,
                    'error': str(e)
                })

                # Notify callbacks
                for callback in self.on_reload_callbacks:
                    callback(config_path, False)

    def set_alternate_config(self, config_path: str):
        """Set alternate config for A/B switching."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        self.alternate_config_path = config_path
        logging.info(f"Alternate config set: {config_path}")

    def toggle_config(self):
        """Switch between primary and alternate configs (A/B switching)."""
        if not self.alternate_config_path:
            logging.warning("No alternate config set for toggle")
            return

        # Swap configs
        temp = self.current_config_path
        self.current_config_path = self.alternate_config_path
        self.alternate_config_path = temp

        logging.info(f"🔄 Switching to config: {self.current_config_path}")

        # Reload
        self.reload_config(smooth_transition=True)

    def _transition_fade_out(self):
        """Fade out all LEDs before config change."""
        if not self.synth.led_animator:
            return

        logging.debug("Fading out for config transition...")

        # Fade all active notes
        for note in self.synth.notes.values():
            for button in note.buttons:
                self.synth.led_animator.fade(
                    button.x, button.y,
                    note.color, (0, 0, 0),
                    duration=0.3
                )

        time.sleep(0.4)  # Wait for fade to complete

    def _transition_fade_in(self):
        """Fade in all LEDs after config change."""
        if not self.synth.led_animator:
            # Just set colors directly
            self.synth.initialize_grid()
            return

        logging.debug("Fading in after config transition...")

        # Fade in all new notes
        for note in self.synth.notes.values():
            for button in note.buttons:
                self.synth.led_animator.fade(
                    button.x, button.y,
                    (0, 0, 0), note.color,
                    duration=0.5
                )

    def add_reload_callback(self, callback: Callable[[str, bool], None]):
        """
        Add callback for reload events.

        Callback signature: callback(config_path: str, success: bool)
        """
        self.on_reload_callbacks.append(callback)

    def get_reload_history(self) -> List[dict]:
        """Get history of config reloads."""
        return self.config_history.copy()

    def manual_reload(self):
        """Manually trigger config reload (for button press)."""
        logging.info("Manual reload triggered")
        self.reload_config(smooth_transition=True)

    def load_config_from_path(self, config_path: str):
        """Load a specific config file."""
        if not os.path.exists(config_path):
            logging.error(f"Config file not found: {config_path}")
            return

        self.reload_config(config_path, smooth_transition=True)

    def get_available_configs(self, config_dir: str = "configs") -> List[str]:
        """List all available config files."""
        configs = []

        # Check main directory
        for file in Path(".").glob("*.yaml"):
            configs.append(str(file))

        # Check configs directory
        if os.path.exists(config_dir):
            for file in Path(config_dir).glob("*.yaml"):
                configs.append(str(file))

        return sorted(configs)

    def cycle_configs(self, config_dir: str = "configs"):
        """Cycle through available configs."""
        configs = self.get_available_configs(config_dir)

        if not configs:
            logging.warning("No configs found to cycle through")
            return

        try:
            current_index = configs.index(self.current_config_path)
            next_index = (current_index + 1) % len(configs)
        except ValueError:
            next_index = 0

        next_config = configs[next_index]
        logging.info(f"🔄 Cycling to config: {next_config}")
        self.reload_config(next_config, smooth_transition=True)


class ConfigSwitcher:
    """
    Helper for binding config switching to Launchpad buttons.

    Use top-right corner buttons for config controls:
    - (8, 0): Toggle A/B
    - (7, 0): Manual reload
    - (6, 0): Cycle configs
    """

    def __init__(self, config_reloader: ConfigReloader, launchpad):
        self.reloader = config_reloader
        self.lp = launchpad

        # Control button positions
        self.toggle_button = (8, 0)
        self.reload_button = (7, 0)
        self.cycle_button = (6, 0)

        # Button colors
        self.control_color = (100, 100, 100)  # Gray for controls
        self.active_color = (0, 255, 0)       # Green when pressed

        self._init_control_buttons()

    def _init_control_buttons(self):
        """Initialize control button LEDs."""
        for pos in [self.toggle_button, self.reload_button, self.cycle_button]:
            led = self.lp.panel.led(pos[0], pos[1])
            led.color = self.control_color

    def handle_button_press(self, x: int, y: int) -> bool:
        """
        Handle button press for config controls.

        Returns:
            True if button was a control button, False otherwise
        """
        if (x, y) == self.toggle_button:
            logging.info("🔄 Toggle A/B button pressed")
            self._flash_button(x, y)
            self.reloader.toggle_config()
            return True

        elif (x, y) == self.reload_button:
            logging.info("♻️ Reload button pressed")
            self._flash_button(x, y)
            self.reloader.manual_reload()
            return True

        elif (x, y) == self.cycle_button:
            logging.info("🔁 Cycle button pressed")
            self._flash_button(x, y)
            self.reloader.cycle_configs()
            return True

        return False

    def _flash_button(self, x: int, y: int):
        """Flash button to show it was pressed."""
        led = self.lp.panel.led(x, y)

        # Quick flash
        led.color = self.active_color
        time.sleep(0.1)
        led.color = self.control_color
