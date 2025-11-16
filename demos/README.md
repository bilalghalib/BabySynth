# BabySynth Demos and Games

This directory contains various interactive games and demonstrations built on top of the BabySynth/Launchpad framework.

## Games

### Simon Says Games
- **simon.py** - Classic Simon Says memory game for babies with musical notes
- **simonbaby.py** - Simplified Simon Says variation
- **simonquad.py** - Simon Says with quadrant-based gameplay

### Action/Arcade Games
- **bubble.py, bubblepop.py, bubblepoppy.py, bubpop.py, fixbubblepop.py** - Various iterations of bubble popping games
- **colorcatch.py, colorcatch2.py** - Color-based catching games
- **colorgarden.py, garden.py** - Garden growing/cultivation games
- **snake.py** - Classic Snake game on the Launchpad
- **tetrix.py** - Tetris-style game
- **runner.py, runnerrun.py, run2.py, run3.py** - Running/platform game variations
- **light_chaser.py** - Light chasing/following game
- **powerup.py** - Power-up collection game
- **game.py** - Generic game framework

### Music & Visual Demos
- **player.py, player2.py, babyplayer.py** - Audio/music players
- **britney.py** - Music-specific player (possibly Britney Spears songs)
- **song.py** - Song playback system
- **dance.py, danceparty.py** - Dance/rhythm-based interactions
- **rainbow.py, rainbowrain.py** - Rainbow visual effects
- **stars.py** - Star visual effects
- **realgrow.py** - Growing animation/interaction

## Running Demos

Most demos can be run directly:
```bash
python demos/simon.py
python demos/snake.py
# etc.
```

Note: Ensure your Launchpad Mini MK3 is connected before running any demo.

## Creating Your Own

These demos serve as great examples for building your own Launchpad-based games and interactive experiences. Key patterns include:
- Button event handling
- LED color control
- Sound playback
- Game state management
- Threading for smooth gameplay
