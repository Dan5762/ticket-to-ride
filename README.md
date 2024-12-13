# Ticket to Ride Game Simulator

A Python implementation of the Ticket to Ride board game with AI players and visual game state rendering.

## Features

- Map visualization using SVG
- Multi-player game simulation
- Basic AI implementation
- Game state visualization with animated GIF replay
- Route claiming and point calculation
- Train card deck management

## Installation

### Prerequisites

In order to generate the gif's of the game you will need to install the following packages for the svg to png conversion. On macOS you can use brew to install them.

```bash
brew install cairo
brew install pango
```

In addition you may need to set the following environment variable to point to the location of the cairo dyld library.

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/cairo/lib:$DYLD_LIBRARY_PATH"
```

## Project Structure

`game/map.py` - Map representation and visualization
`game/state.py` - Game state management
`game/utils.py` - Data classes and enums
`game/agent.py` - AI player implementation
`main.py` - Game simulation runner

## Visualization
The game generates:
- SVG files for each turn
- A final animated GIF (game_replay.gif) showing the game progression
- Each frame in the GIF represents one turn and lasts for 1 second

## AI Implementation

The AI uses a simple strategy system that:

Evaluates the current game state
Considers the value of:
Drawing cards
Claiming routes
Drawing new destination tickets
Makes decisions based on:
Current hand composition
Progress towards destination tickets
Remaining trains
Points potential

## Contributing
Feel free to submit issues and enhancement requests!

## Acknowledgments
Based on the board game "Ticket to Ride" by Alan R. Moon