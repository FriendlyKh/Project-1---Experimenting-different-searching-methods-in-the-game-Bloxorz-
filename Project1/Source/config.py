"""
Global configurations, cute & bright color palette, 3D camera defaults,
and animation constants for the Bloxorz Solver & Algorithm Visualizer project.
"""
from pathlib import Path

# Base Paths
SOURCE_DIR = Path(__file__).resolve().parent
STAGES_DIR = SOURCE_DIR / "stages"
EXPERIMENTS_DIR = SOURCE_DIR / "experiments"
OUTPUT_DIR = EXPERIMENTS_DIR / "output"

# Window / GUI Settings
SCREEN_WIDTH = 1180
SCREEN_HEIGHT = 760

FPS = 60
TILE_SIZE = 48  # default pixels per cell
SIDEBAR_WIDTH = 350

# View Modes
VIEW_MODE_25D = "2.5D"   # 3D / 2.5D Rotatable Diorama Viewpoint
VIEW_MODE_2D = "2D"      # 2D Top-Down Algorithm Visualization Viewpoint

# 3D Camera & Interactive Viewport Defaults
DEFAULT_CAM_YAW = 28.0       # degrees (horizontal orbit angle; 0 = front-oblique, 45 = classic isometric)
DEFAULT_CAM_PITCH = 54.0     # degrees (vertical tilt angle; 25 = low 3D, 85 = top-down)
DEFAULT_CAM_ZOOM = 1.0       # zoom multiplier (0.40x to 3.00x)
MIN_CAM_ZOOM = 0.40
MAX_CAM_ZOOM = 3.00
MIN_CAM_PITCH = 24.0
MAX_CAM_PITCH = 84.0

# Animation Settings
MOVE_ANIM_DURATION = 0.19    # seconds for smooth manual/step block roll animation
REPLAY_STEP_INTERVAL = 320   # milliseconds per step in auto-replay
DEATH_ANIM_DURATION = 1.80   # seconds for the dramatic tumbling fall death sequence
LEVEL_TRANSITION_DURATION = 1.35  # seconds for a smooth, visible cinematic swipe-in / swipe-out level transition

# ============================================================================
# CUTE & BRIGHT PASTEL DAYDREAM COLOR PALETTE (RGB)
# ============================================================================

# Main Backgrounds & Surfaces
COLOR_BG = (238, 245, 255)             # Soft pastel sky-cream canvas background
COLOR_BG_ACCENT = (225, 236, 252)      # Subtle dot/cloud pattern accent
COLOR_BOARD_MAT = (248, 251, 255)      # Elevated board playmat card
COLOR_BOARD_MAT_BORDER = (210, 224, 245)

COLOR_PANEL_BG = (255, 252, 248)       # Warm milky cream sidebar background
COLOR_PANEL_BORDER = (228, 218, 235)   # Soft lavender-rose divider line
COLOR_CARD_BG = (246, 242, 255)        # Cute pastel lavender card background
COLOR_CARD_ALT_BG = (255, 244, 238)    # Cute pastel peach card background
COLOR_CARD_MINT_BG = (236, 250, 245)   # Cute pastel mint card background
COLOR_CARD_BORDER = (222, 214, 240)

# Typography Colors (High-contrast warmberry & slate for crisp readability)
COLOR_TEXT = (58, 46, 78)              # Deep plum-charcoal primary text
COLOR_TEXT_MUTED = (128, 116, 148)     # Soft dusty-violet secondary text
COLOR_TEXT_ACCENT = (230, 95, 135)     # Cute berry-rose accent title text

# Tile Colors (Bright, tactile, toy-like palette)
COLOR_VOID = (232, 240, 252)           # Soft sky void
COLOR_FLOOR = (255, 253, 247)          # Creamy ivory ceramic tile top
COLOR_FLOOR_SHADE = (236, 229, 218)    # Subtle warm checker/texture tint
COLOR_FLOOR_BORDER = (212, 202, 190)   # Warm biscuit border
COLOR_FLOOR_SIDE = (206, 194, 180)     # 3D tile thickness slab (front)
COLOR_FLOOR_SIDE_DARK = (184, 172, 158)

COLOR_GOAL = (52, 42, 84)              # Deep starlight indigo portal well
COLOR_GOAL_INNER = (88, 72, 138)       # Portal inner ring
COLOR_GOAL_GLOW = (255, 216, 102)      # Glowing golden starlight portal rim
COLOR_GOAL_BORDER = (255, 198, 68)     # Bright gold outline for goal

COLOR_FRAGILE = (255, 176, 124)        # Cute coral-apricot fragile wafer tile
COLOR_FRAGILE_STRIPE = (255, 142, 92)  # Honeycomb/crack warning pattern
COLOR_FRAGILE_BORDER = (228, 118, 72)  # Warm terracotta border
COLOR_FRAGILE_SIDE = (214, 106, 62)    # 3D fragile slab

# Bridge & Switch Colors
COLOR_BRIDGE_OPEN = (132, 226, 212)    # Bright aqua-mint energy/wood plank
COLOR_BRIDGE_OPEN_PLANK = (102, 204, 190)
COLOR_BRIDGE_OPEN_BORDER = (74, 178, 166)
COLOR_BRIDGE_OPEN_SIDE = (82, 168, 158)
COLOR_BRIDGE_CLOSED = (218, 228, 242)  # Soft ghostly blueprint socket
COLOR_BRIDGE_CLOSED_BORDER = (178, 194, 218)

COLOR_SWITCH_SOFT = (255, 218, 88)     # Sunny lemon-butter button
COLOR_SWITCH_SOFT_RIM = (224, 172, 36)
COLOR_SWITCH_HEAVY = (255, 108, 138)   # Strawberry-rose pressure plate
COLOR_SWITCH_HEAVY_RIM = (212, 68, 102)
COLOR_SWITCH_SPLIT = (106, 224, 156)   # Mint-emerald twin teleport pad
COLOR_SWITCH_SPLIT_RIM = (56, 178, 112)

# Block Colors (Cute Strawberry-Caramel / Cozy Toy Block)
COLOR_BLOCK_TOP = (255, 136, 156)      # Bright sakura-strawberry top face
COLOR_BLOCK = (238, 104, 128)          # Berry-coral front face
COLOR_BLOCK_SIDE = (212, 82, 108)      # Deep berry side face
COLOR_BLOCK_BORDER = (148, 48, 72)     # Crisp dark-berry outline
COLOR_BLOCK_SHINE = (255, 198, 210)    # Glossy toy highlight

# Split Cube Colors (Distinct cute twin cubes)
COLOR_SPLIT_CUBE_1 = (255, 148, 112)   # Peach-tangerine primary cube
COLOR_SPLIT_CUBE_1_SIDE = (222, 112, 78)
COLOR_SPLIT_CUBE_2 = (122, 188, 255)   # Sky-periwinkle secondary cube
COLOR_SPLIT_CUBE_2_SIDE = (86, 148, 224)
COLOR_ACTIVE_HIGHLIGHT = (255, 226, 76)# Glowing sunny-gold halo

# Algorithm Visualization (2D Mode) Overlay Colors
COLOR_VIS_EXPLORED = (186, 224, 255)   # Soft sky tint for visited states
COLOR_VIS_EXPLORED_BORDER = (118, 178, 238)
COLOR_VIS_PATH = (255, 112, 150)       # Vibrant berry-pink solution trail
COLOR_VIS_PATH_NODE = (255, 238, 120)  # Sunny yellow step node dot
COLOR_VIS_START = (118, 224, 158)      # Mint start marker
COLOR_VIS_LINK = (168, 132, 238)       # Lavender switch-to-bridge connector

# Button Palette Presets (bg, hover, shadow, text)
BTN_PRIMARY = ((124, 156, 255), (144, 174, 255), (86, 114, 212), (255, 255, 255))
BTN_MINT = ((88, 206, 164), (108, 222, 182), (56, 164, 126), (255, 255, 255))
BTN_CORAL = ((255, 126, 142), (255, 148, 162), (214, 84, 102), (255, 255, 255))
BTN_SUNNY = ((255, 194, 84), (255, 210, 112), (218, 152, 42), (78, 52, 24))
BTN_LAVENDER = ((176, 142, 248), (194, 164, 255), (134, 98, 208), (255, 255, 255))
BTN_NEUTRAL = ((242, 236, 248), (250, 246, 255), (204, 194, 218), (68, 56, 88))

# Solvers & Performance limits
DEFAULT_SEARCH_TIMEOUT = 60.0  # seconds
MAX_EXPANDED_NODES = 500_000