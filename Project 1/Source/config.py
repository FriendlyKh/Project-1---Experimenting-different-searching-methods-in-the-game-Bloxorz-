"""
Global configurations and constants for Bloxorz Solver project.
"""

from pathlib import Path

# Base Paths
SOURCE_DIR = Path(__file__).resolve().parent
STAGES_DIR = SOURCE_DIR / "stages"
EXPERIMENTS_DIR = SOURCE_DIR / "experiments"
OUTPUT_DIR = EXPERIMENTS_DIR / "output"

# Window / GUI Settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
TILE_SIZE = 40  # pixels per cell in 2D view
SIDEBAR_WIDTH = 300

# Color Palette (RGB)
COLOR_BG = (28, 30, 38)            # Dark slate background
COLOR_PANEL_BG = (38, 41, 54)      # Darker panel background
COLOR_TEXT = (240, 240, 245)
COLOR_TEXT_MUTED = (150, 155, 175)

# Tile Colors
COLOR_VOID = (20, 22, 28)
COLOR_FLOOR = (215, 220, 230)      # White / Marble floor
COLOR_FLOOR_BORDER = (180, 185, 195)
COLOR_GOAL = (20, 20, 20)          # Hole in the floor
COLOR_GOAL_BORDER = (255, 215, 0)  # Gold outline for goal
COLOR_FRAGILE = (245, 140, 60)     # Orange fragile tile
COLOR_FRAGILE_BORDER = (200, 100, 30)

# Bridge & Switch Colors
COLOR_BRIDGE_OPEN = (100, 180, 240)    # Passable cyan/blue
COLOR_BRIDGE_CLOSED = (45, 50, 65)     # Dim empty outline
COLOR_SWITCH_SOFT = (255, 220, 50)     # Yellow circle
COLOR_SWITCH_HEAVY = (235, 75, 75)     # Red 'X'
COLOR_SWITCH_SPLIT = (80, 220, 100)    # Green '( )'

# Block Colors
COLOR_BLOCK = (180, 95, 45)            # Wood / Terracotta
COLOR_BLOCK_BORDER = (110, 50, 20)
COLOR_BLOCK_TOP = (210, 125, 70)
COLOR_SPLIT_CUBE_1 = (180, 95, 45)     # Primary cube
COLOR_SPLIT_CUBE_2 = (65, 145, 225)    # Secondary cube
COLOR_ACTIVE_HIGHLIGHT = (255, 255, 100)

# Solvers & Performance limits
DEFAULT_SEARCH_TIMEOUT = 60.0  # seconds
MAX_EXPANDED_NODES = 500_000
