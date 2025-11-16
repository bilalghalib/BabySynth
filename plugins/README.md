# BabySynth Game Plugins

This directory contains game plugins for BabySynth. Each plugin is a standalone Python file that defines a custom game.

## Creating Your Own Game

Creating a game is easy! Just follow these steps:

### 1. Create a New Python File

Create a new file in this directory (e.g., `my_game.py`)

### 2. Import the Game Base Class

```python
from game_plugin import Game
```

### 3. Define Your Game Class

```python
class MyAwesomeGame(Game):
    def __init__(self):
        super().__init__(
            name="My Awesome Game",
            description="This game does cool things!",
            difficulty="Easy",  # Easy, Medium, Hard
            min_age=2  # Minimum recommended age
        )
        # Add your game variables here
        self.score = 0
```

### 4. Implement Required Methods

#### start()
Initialize your game:
```python
def start(self):
    self.clear_grid()  # Clear all LEDs
    self.score = 0
    print("Game started!")
    # Set up initial LED colors
    self.set_led(4, 4, (255, 0, 0))  # Red LED at center
```

#### handle_button_press(x, y)
Handle button presses:
```python
def handle_button_press(self, x, y):
    print(f"Button pressed at ({x}, {y})")
    self.set_led(x, y, (0, 255, 0))  # Turn LED green
    self.score += 1
```

#### stop()
Clean up when game ends:
```python
def stop(self):
    self.running = False
    self.clear_grid()
    print(f"Game over! Score: {self.score}")
```

### 5. Optional: Handle Button Release

```python
def handle_button_release(self, x, y):
    print(f"Button released at ({x}, {y})")
    self.set_led(x, y, (0, 0, 0))  # Turn LED off
```

## Complete Example

```python
"""
Simple color matching game
"""
import random
from game_plugin import Game

class ColorMatch(Game):
    def __init__(self):
        super().__init__(
            name="Color Match",
            description="Press the button that matches the color!",
            difficulty="Easy",
            min_age=2
        )
        self.target_color = None
        self.target_pos = None

    def start(self):
        self.clear_grid()
        self.show_new_color()

    def show_new_color(self):
        # Pick a random color
        colors = [(255,0,0), (0,255,0), (0,0,255)]
        self.target_color = random.choice(colors)

        # Show it in a random position
        x = random.randint(0, 8)
        y = random.randint(0, 8)
        self.target_pos = (x, y)

        self.set_led(x, y, self.target_color)

    def handle_button_press(self, x, y):
        if (x, y) == self.target_pos:
            # Correct! Flash white
            self.set_led(x, y, (255, 255, 255))
            print("✨ Correct!")
            # Show new color after a moment
            import time
            time.sleep(0.3)
            self.clear_grid()
            self.show_new_color()

    def stop(self):
        self.running = False
        self.clear_grid()
```

## Available Helper Methods

Your game has access to these methods:

- `self.clear_grid()` - Turn off all LEDs
- `self.set_led(x, y, color)` - Set LED color (color is RGB tuple like (255, 0, 0))
- `self.lp` - Direct access to Launchpad object
- `self.running` - Boolean flag for game state

## LED Grid Layout

```
   0  1  2  3  4  5  6  7  8
0  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜  (Usually reserved for controls)
1  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
2  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
3  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
4  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
5  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
6  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
7  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
8  ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜
```

Coordinates are (x, y) where x is column (0-8) and y is row (0-8).

## Running Your Game

```bash
python game_plugin.py
```

The plugin system will automatically discover and list all available games!

## Example Games Included

- **Whack-a-Light** - Press the buttons as they light up!
- **Rainbow Chase** - Catch the moving rainbow colors!

## Tips for Baby-Friendly Games

1. **Use bright, contrasting colors** - Babies love vibrant visuals
2. **Keep it simple** - One action = one reward
3. **Provide immediate feedback** - Flash white/bright color on success
4. **Use sounds** - Combine with the synthesizer for audio feedback
5. **Make it forgiving** - Any press near the target can count as success
6. **Progressive difficulty** - Start slow, speed up gradually

## Share Your Games!

Created a fun game? Share it with the BabySynth community! Submit a pull request or share your .py file.

Happy coding! 🎮✨
