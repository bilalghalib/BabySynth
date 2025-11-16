"""
BabySynth Game Plugin System
A simple framework for creating games that run on the Launchpad.

To create a new game:
1. Inherit from the Game base class
2. Implement the required methods
3. Save your game in the plugins/ directory
4. The game will be automatically discovered and loaded!
"""

import os
import importlib.util
from abc import ABC, abstractmethod
from lpminimk3 import find_launchpads, Mode


class Game(ABC):
    """
    Base class for all BabySynth games.

    Your game must implement these methods:
    - start(): Initialize and start your game
    - handle_button_press(x, y): Called when a button is pressed
    - handle_button_release(x, y): Called when a button is released
    - stop(): Clean up when the game ends
    """

    def __init__(self, name, description, difficulty="Easy", min_age=1):
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.min_age = min_age
        self.lp = None
        self.running = False

    def init_launchpad(self):
        """Initialize connection to the Launchpad"""
        launchpads = find_launchpads()
        if not launchpads:
            raise RuntimeError("No Launchpad found! Please connect your device.")
        self.lp = launchpads[0]
        self.lp.open()
        self.lp.mode = Mode.PROG

    def clear_grid(self):
        """Clear all LEDs on the Launchpad"""
        if self.lp:
            for x in range(9):
                for y in range(9):
                    self.lp.panel.led(x, y).color = (0, 0, 0)

    def set_led(self, x, y, color):
        """Set a single LED color"""
        if self.lp and 0 <= x < 9 and 0 <= y < 9:
            self.lp.panel.led(x, y).color = color

    @abstractmethod
    def start(self):
        """Start the game - implement your initialization here"""
        pass

    @abstractmethod
    def handle_button_press(self, x, y):
        """Handle button press events"""
        pass

    def handle_button_release(self, x, y):
        """Handle button release events (optional)"""
        pass

    @abstractmethod
    def stop(self):
        """Stop the game and clean up"""
        pass


class GameLoader:
    """Loads game plugins from the plugins directory"""

    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.games = {}

    def discover_games(self):
        """Automatically discover and load all game plugins"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            print(f"Created plugins directory: {self.plugins_dir}")
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                self.load_game(filename)

    def load_game(self, filename):
        """Load a single game plugin"""
        filepath = os.path.join(self.plugins_dir, filename)
        module_name = filename[:-3]  # Remove .py extension

        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find Game subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, Game) and
                    attr is not Game):
                    # Instantiate the game
                    game_instance = attr()
                    self.games[game_instance.name] = game_instance
                    print(f"✅ Loaded game: {game_instance.name}")

        except Exception as e:
            print(f"❌ Failed to load {filename}: {e}")

    def list_games(self):
        """List all available games"""
        if not self.games:
            print("No games found. Add .py files to the plugins/ directory!")
            return

        print("\n🎮 Available Games:")
        print("=" * 60)
        for name, game in self.games.items():
            print(f"\n📱 {name}")
            print(f"   Description: {game.description}")
            print(f"   Difficulty: {game.difficulty}")
            print(f"   Min Age: {game.min_age}+")
        print("\n" + "=" * 60)

    def run_game(self, game_name):
        """Run a specific game by name"""
        if game_name not in self.games:
            print(f"Game '{game_name}' not found!")
            self.list_games()
            return

        game = self.games[game_name]
        print(f"\n🎮 Starting {game.name}...")
        print(f"📝 {game.description}")
        print(f"⚠️  Press Ctrl+C to exit\n")

        try:
            game.init_launchpad()
            game.start()
            game.running = True

            # Main game loop
            while game.running:
                button_event = game.lp.panel.buttons().poll_for_event()
                if button_event:
                    from lpminimk3 import ButtonEvent
                    if button_event.type == ButtonEvent.PRESS:
                        game.handle_button_press(button_event.button.x, button_event.button.y)
                    elif button_event.type == ButtonEvent.RELEASE:
                        game.handle_button_release(button_event.button.x, button_event.button.y)

        except KeyboardInterrupt:
            print("\n\n👋 Game stopped!")
        finally:
            game.stop()
            if game.lp:
                game.lp.close()


if __name__ == '__main__':
    # Example usage
    loader = GameLoader()
    loader.discover_games()
    loader.list_games()

    if loader.games:
        # Run the first available game
        first_game = list(loader.games.keys())[0]
        loader.run_game(first_game)
