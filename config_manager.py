"""
BabySynth - Configuration Manager
Handles loading, saving, validating, and hot-reloading of YAML configurations.
Supports advanced features like animations, chord progressions, themes, and macros.
"""

import yaml
import os
import time
import threading
from pathlib import Path


class ConfigManager:
    """Manages BabySynth YAML configurations with hot-reload support"""

    def __init__(self, default_config='config.yaml'):
        self.default_config = default_config
        self.current_config = None
        self.config_path = default_config
        self.last_modified = 0
        self.watch_thread = None
        self.watching = False
        self.on_reload_callback = None

    def load(self, config_path=None):
        """Load a configuration file"""
        if config_path:
            self.config_path = config_path

        try:
            with open(self.config_path, 'r') as file:
                self.current_config = yaml.safe_load(file)
            self.last_modified = os.path.getmtime(self.config_path)
            self._validate_config()
            print(f"✅ Config loaded: {self.config_path}")
            return self.current_config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None

    def save(self, config, config_path=None):
        """Save a configuration to file"""
        if config_path:
            self.config_path = config_path

        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as file:
                yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)

            self.current_config = config
            self.last_modified = os.path.getmtime(self.config_path)
            print(f"💾 Config saved: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False

    def _validate_config(self):
        """Validate configuration structure"""
        if not self.current_config:
            raise ValueError("Configuration is empty")

        required_keys = ['models', 'scales', 'colors']
        for key in required_keys:
            if key not in self.current_config:
                print(f"⚠️  Warning: Missing required key '{key}' in config")

        # Validate models
        if 'models' in self.current_config:
            for model_name, model_data in self.current_config['models'].items():
                if 'layout' not in model_data:
                    raise ValueError(f"Model '{model_name}' missing layout")

        return True

    def start_watching(self, callback=None):
        """Start watching config file for changes (hot-reload)"""
        self.on_reload_callback = callback
        self.watching = True
        self.watch_thread = threading.Thread(target=self._watch_file, daemon=True)
        self.watch_thread.start()
        print(f"👀 Watching {self.config_path} for changes...")

    def stop_watching(self):
        """Stop watching config file"""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=1)

    def _watch_file(self):
        """Watch file for modifications and reload"""
        while self.watching:
            try:
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime > self.last_modified:
                    print(f"🔄 Config file changed, reloading...")
                    old_config = self.current_config
                    self.load()
                    if self.on_reload_callback:
                        self.on_reload_callback(self.current_config, old_config)
            except Exception as e:
                print(f"⚠️  Error watching file: {e}")

            time.sleep(1)  # Check every second

    def get_animation(self, name):
        """Get an animation sequence by name"""
        if 'animations' in self.current_config:
            return self.current_config['animations'].get(name)
        return None

    def get_chord_progression(self, name):
        """Get a chord progression by name"""
        if 'chord_progressions' in self.current_config:
            return self.current_config['chord_progressions'].get(name)
        return None

    def get_theme(self, name):
        """Get a color theme by name"""
        if 'themes' in self.current_config:
            return self.current_config['themes'].get(name)
        return None

    def get_macro(self, name):
        """Get a macro by name"""
        if 'macros' in self.current_config:
            return self.current_config['macros'].get(name)
        return None

    def list_configs(self, directory='configs'):
        """List all available configuration files"""
        configs = []

        # Main config
        if os.path.exists('config.yaml'):
            configs.append('config.yaml')

        # Configs directory
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    configs.append(os.path.join(directory, filename))

        return configs

    def apply_theme(self, theme_name):
        """Apply a theme to the current config colors"""
        theme = self.get_theme(theme_name)
        if theme:
            self.current_config['colors'] = theme
            print(f"🎨 Applied theme: {theme_name}")
            return True
        return False


class AnimationPlayer:
    """Plays LED animations defined in YAML"""

    def __init__(self, launchpad, web_broadcaster=None):
        self.lp = launchpad
        self.web_broadcaster = web_broadcaster
        self.playing = False
        self.play_thread = None

    def play(self, animation_data):
        """Play an animation sequence"""
        if not animation_data:
            return

        self.playing = True
        self.play_thread = threading.Thread(
            target=self._play_animation,
            args=(animation_data,),
            daemon=True
        )
        self.play_thread.start()

    def _play_animation(self, animation_data):
        """Animation playback loop"""
        duration = animation_data.get('duration', 2.0)
        loop = animation_data.get('loop', False)
        frames = animation_data.get('frames', [])

        while self.playing:
            for frame in frames:
                if not self.playing:
                    break

                delay = frame.get('delay', 0.1)
                pattern = frame.get('pattern', [])

                # Apply pattern to grid
                for y, row in enumerate(pattern):
                    for x, color in enumerate(row):
                        if x < 9 and y < 9:
                            self.lp.panel.led(x, y).color = tuple(color)
                            if self.web_broadcaster:
                                self.web_broadcaster.update_led(x, y, color)

                time.sleep(delay)

            if not loop:
                break

    def stop(self):
        """Stop animation playback"""
        self.playing = False
        if self.play_thread:
            self.play_thread.join(timeout=1)


class ChordPlayer:
    """Plays chord progressions"""

    def __init__(self, synth):
        self.synth = synth

    def play_progression(self, progression):
        """Play a chord progression"""
        # progression is a list of note names like ['C', 'F', 'G', 'C']
        print(f"🎵 Playing chord progression: {progression}")
        # Implementation would trigger multiple notes at once
        # This is a placeholder for the actual implementation


# Example usage
if __name__ == '__main__':
    manager = ConfigManager()
    config = manager.load('config.yaml')

    print("\n📋 Current Configuration:")
    print(f"Name: {config.get('name')}")
    print(f"Models: {list(config.get('models', {}).keys())}")
    print(f"Scales: {list(config.get('scales', {}).keys())}")

    # List all configs
    print("\n📁 Available Configurations:")
    for cfg in manager.list_configs():
        print(f"  - {cfg}")

    # Test hot-reload
    def on_reload(new_config, old_config):
        print("🔥 Hot reload triggered!")
        print(f"Old: {old_config.get('name')}")
        print(f"New: {new_config.get('name')}")

    manager.start_watching(callback=on_reload)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_watching()
        print("\n👋 Stopped watching")
