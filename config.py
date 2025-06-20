# config.py

# Grid dimensions (default 20x20, can be adjusted via UI in simulation)
GRID_WIDTH = 10
GRID_HEIGHT = 10

# Cell geometry (in pixels)
CELL_SIZE = 45         # each cell's drawn size in pixels
CELL_MARGIN = 10       # margin (spacing) between cells in pixels
CELL_SPACING = CELL_SIZE + CELL_MARGIN  # effective spacing from one cell center to adjacent

# Special cell counts
INBOUND_CELLS = 5      # number of inbound cells along the left edge (top rows)
OUTBOUND_CELLS = 5     # number of outbound cells along the right edge (top rows)
MAX_ITEMS_PER_CELL = 20  # storage cell capacity (stack height)

# Item preference update interval (in seconds)
PREFERENCE_UPDATE_INTERVAL = 60.0  # default 1 minute

# Bot movement parameters
MAX_SPEED_CELLS_PER_SEC = 2       # max bot speed in cells per second (2 cells/s ≈ 90-110 px/s as given)
ACCEL_TIME = 0.1                   # time in seconds to accelerate from 0 to max speed
DECEL_TIME = 0.1                   # time in seconds to decelerate to a stop
# (From ACCEL_TIME and DECEL_TIME we can derive acceleration rates if needed)

# Colors (RGB tuples)
BACKGROUND_COLOR = (30, 30, 30)    # dark background for the grid
CELL_COLOR = (80, 80, 80)          # base color for empty storage cells
INBOUND_COLOR = (80, 120, 180)     # color for inbound cells (e.g., bluish)
OUTBOUND_COLOR = (180, 120, 80)    # color for outbound cells (e.g., brownish)
# Base colors
BOT_COLOR = (255, 255, 0)          # yellow color for bots (will be drawn with transparency)
PATH_COLOR = (0, 255, 0)           # default path colour
# Palette of path colours used to distinguish bots
PATH_COLORS = [
    (255, 0, 0),    # red
    (0, 255, 0),    # green
    (0, 128, 255),  # blue
    (255, 0, 255),  # magenta
    (255, 165, 0),  # orange
    (255, 255, 0),  # yellow
]
# (Additional colors for item preference highlighting can be defined if needed)
