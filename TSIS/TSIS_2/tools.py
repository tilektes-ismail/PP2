# ============================================================
#  tools.py  —  Paint App (TSIS 2)
#  Contains:
#    - All drawing functions (pen, pencil, line, rect, circle,
#      square, right triangle, equilateral triangle, rhombus,
#      eraser, fill, text)
#    - Toolbar rendering (two rows + size row)
#    - Toolbar click detection
# ============================================================

import pygame                   # Pygame library for drawing and surface operations
import math                     # math.hypot and math.sqrt for geometry calculations
from collections import deque   # deque used as an efficient queue for flood fill BFS

# Toolbar layout constants
TOOLBAR_HEIGHT       = 50    # Height of a single toolbar row in pixels
TOOLBAR_TOTAL_HEIGHT = 150   # Total height of all three rows combined (3 × 50)


# ============================================================
#  Colour Helpers
# ============================================================

# Dictionary mapping colour name strings to their RGB tuples
NAMED_COLORS = {
    'red':    (255,   0,   0),
    'green':  (  0, 200,   0),
    'blue':   (  0,   0, 255),
    'black':  (  0,   0,   0),
    'white':  (255, 255, 255),
    'yellow': (255, 220,   0),
    'orange': (255, 140,   0),
    'purple': (160,   0, 200),
}


def get_solid_color(color_mode):
    """Return an RGB tuple for the given color_mode string."""
    return NAMED_COLORS.get(color_mode, (0, 0, 255))   # Default to blue if name not found


def get_gradient_color(index, color_mode):
    """Return a gradient colour based on index (0-255) for pen strokes."""
    c1 = max(0, min(255, 2 * index - 256))  # Dark component: only visible after index passes 128
    c2 = max(0, min(255, 2 * index))        # Bright component: ramps up from index 0
    if color_mode == 'blue':                # Blue gradient: c2 drives blue, c1 adds grey tint
        return (c1, c1, c2)
    elif color_mode == 'red':               # Red gradient: c2 drives red channel
        return (c2, c1, c1)
    elif color_mode == 'green':             # Green gradient: c2 drives green channel
        return (c1, c2, c1)
    else:
        return get_solid_color(color_mode)  # Non-primary colours fall back to a flat solid colour


# ============================================================
#  Toolbar Definition
# ============================================================

# Each tuple: (button label, mode string, x position on screen)
TOOLS = [
    ("Pencil",  "pencil",  10),
    ("Line",    "line",    90),
    ("Rect",    "rect",   170),
    ("Square",  "square", 250),
    ("Circle",  "circle", 330),
    ("RTri",    "rtri",   410),
    ("ETri",    "etri",   490),
    ("Rhombus", "rhombus",570),
    ("Eraser",  "eraser", 650),
    ("Fill",    "fill",   730),
    ("Text",    "text",   810),
]

# Each tuple: (button label, colour name string, x position on screen)
COLOR_BUTTONS = [
    ("R", "red",    10),
    ("G", "green",  60),
    ("B", "blue",  110),
    ("K", "black", 160),
    ("W", "white", 210),
    ("Y", "yellow",260),
    ("O", "orange",310),
    ("P", "purple",360),
]

# Each tuple: (display label, keyboard shortcut number, pixel size, x position)
SIZE_LEVELS = [
    ("S (1)", 1,  2,  10),   # Small: key 1 → 2px brush
    ("M (2)", 2,  5,  90),   # Medium: key 2 → 5px brush
    ("L (3)", 3, 10, 170),   # Large: key 3 → 10px brush
]


def draw_toolbar(screen, mode, color_mode, brush_size, screen_width):
    """Render the three-row toolbar onto the screen."""
    font       = pygame.font.SysFont("Verdana", 11)     # Slightly larger font for tool labels
    small_font = pygame.font.SysFont("Verdana", 10)     # Smaller font for hints and size labels

    # ---- Row 1: tools ----
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, screen_width, TOOLBAR_HEIGHT))   # Dark grey background for tool row
    for label, tool_mode, x in TOOLS:
        active  = mode == tool_mode                                 # True if this tool is currently selected
        col     = (255, 255, 100) if active else (160, 160, 160)   # Yellow fill if active, grey outline if not
        pygame.draw.rect(screen, col, (x, 6, 72, 34), 0 if active else 2)  # Filled when active, border-only otherwise
        txt_col = (0, 0, 0) if active else (200, 200, 200)         # Black text on yellow, light grey text on dark
        text    = font.render(label, True, txt_col)
        screen.blit(text, (x + 4, 18))                             # Draw label slightly inset from the button edge

    # ---- Row 2: colours ----
    row2_y = TOOLBAR_HEIGHT                                                                     # Y offset for the second row
    pygame.draw.rect(screen, (30, 30, 30), (0, row2_y, screen_width, TOOLBAR_HEIGHT))          # Darker background for colour row
    for label, col, x in COLOR_BUTTONS:
        rgb    = NAMED_COLORS[col]                                      # Get the actual RGB value for this swatch
        active = color_mode == col                                      # True if this colour is currently selected
        pygame.draw.rect(screen, rgb, (x, row2_y + 8, 40, 34))         # Always fill the swatch with its colour
        if active:
            pygame.draw.rect(screen, (255, 255, 255), (x, row2_y + 8, 40, 34), 3)  # White border highlights the active colour
        text = font.render(label, True,
                           (0, 0, 0) if sum(rgb) > 380 else (255, 255, 255))  # Dark text on light colours, white text on dark
        screen.blit(text, (x + 13, row2_y + 18))

    # Keyboard shortcut hint displayed to the right of colour swatches
    hint = small_font.render("Keys: r g b k w y o p", True, (100, 100, 100))
    screen.blit(hint, (420, row2_y + 18))

    # ---- Row 3: brush sizes ----
    row3_y = TOOLBAR_HEIGHT * 2                                                                     # Y offset for the third row
    pygame.draw.rect(screen, (40, 40, 40), (0, row3_y, screen_width, TOOLBAR_HEIGHT))              # Medium grey background
    size_label = small_font.render("Brush size:", True, (180, 180, 180))
    screen.blit(size_label, (10, row3_y + 18))                                                     # Static label at the left
    for label, key_num, px, x in SIZE_LEVELS:
        active  = brush_size == px                                                                  # True if this pixel size is active
        col     = (255, 220, 80) if active else (120, 120, 120)                                    # Warm yellow if active, grey if not
        pygame.draw.rect(screen, col, (x + 80, row3_y + 6, 72, 34), 0 if active else 2)           # Offset by 80 to clear the "Brush size:" label
        txt_col = (0, 0, 0) if active else (200, 200, 200)
        text    = font.render(label, True, txt_col)
        screen.blit(text, (x + 84, row3_y + 17))

    # Save shortcut hint at the far right of the size row
    hint2 = small_font.render("Ctrl+S = save PNG", True, (100, 100, 100))
    screen.blit(hint2, (screen_width - 160, row3_y + 18))


def get_tool_from_click(x, y):
    """Return the tool/colour/size string that was clicked, or None."""
    if 0 <= y < TOOLBAR_HEIGHT:                     # Click is in the top (tool) row
        for label, tool_mode, tx in TOOLS:
            if tx <= x <= tx + 72:                  # X falls within this button's 72px width
                return tool_mode

    if TOOLBAR_HEIGHT <= y < TOOLBAR_HEIGHT * 2:    # Click is in the middle (colour) row
        for label, col, cx in COLOR_BUTTONS:
            if cx <= x <= cx + 40:                  # X falls within this colour swatch's 40px width
                return col

    if TOOLBAR_HEIGHT * 2 <= y < TOOLBAR_TOTAL_HEIGHT:  # Click is in the bottom (size) row
        for label, key_num, px, tx in SIZE_LEVELS:
            if (tx + 80) <= x <= (tx + 152):            # Offset by 80 to match where buttons are drawn
                return f"size_{px}"                      # Return e.g. "size_5" so caller can parse the pixel value

    return None     # Click didn't land on any toolbar element


def brush_px_from_key(key_num):
    """Map keyboard digit 1/2/3 → brush pixel size."""
    mapping = {1: 2, 2: 5, 3: 10}      # Direct lookup: 1→2px, 2→5px, 3→10px
    return mapping.get(key_num)         # Returns None if key_num is not 1, 2, or 3


# ============================================================
#  Drawing Functions
# ============================================================

def draw_pencil_segment(screen, start, end, color, width):
    """Draw a single freehand pencil segment between two points."""
    if start == end:                                        # No movement — just draw a dot
        pygame.draw.circle(screen, color, start, max(1, width // 2))
        return
    dx = end[0] - start[0]                                 # Horizontal distance
    dy = end[1] - start[1]                                 # Vertical distance
    iterations = max(abs(dx), abs(dy), 1)                  # Step count = longest axis, ensures no pixel gaps
    half = max(1, width // 2)                              # Radius = half the brush width, minimum 1
    for i in range(iterations + 1):                        # +1 so the endpoint itself is included
        t = i / iterations                                  # Progress from 0.0 (start) to 1.0 (end)
        x = int(start[0] + t * dx)                         # Interpolated X position along the segment
        y = int(start[1] + t * dy)                         # Interpolated Y position along the segment
        pygame.draw.circle(screen, color, (x, y), half)    # Draw a filled circle at each step


def draw_straight_line(screen, start, end, color, width):
    """Draw a straight line with given width."""
    pygame.draw.line(screen, color, start, end, max(1, width))  # max(1,...) prevents zero-width crash


def draw_rectangle(screen, start, end, color, outline):
    x = min(start[0], end[0])      # Left edge — handles dragging in any direction
    y = min(start[1], end[1])      # Top edge
    w = abs(end[0] - start[0])     # Width = absolute horizontal drag distance
    h = abs(end[1] - start[1])     # Height = absolute vertical drag distance
    if w > 0 and h > 0:            # Skip drawing if either dimension is zero
        pygame.draw.rect(screen, color, (x, y, w, h), outline)  # outline=0 fills; >0 draws border only


def draw_square(screen, start, end, color, outline):
    dx   = end[0] - start[0]               # Raw horizontal drag delta
    dy   = end[1] - start[1]               # Raw vertical drag delta
    side = min(abs(dx), abs(dy))           # Use the shorter side to enforce a perfect square
    x = start[0] if dx >= 0 else start[0] - side   # Shift left if dragging left
    y = start[1] if dy >= 0 else start[1] - side   # Shift up if dragging up
    if side > 0:                            # Skip if no drag distance
        pygame.draw.rect(screen, color, (x, y, side, side), outline)


def draw_circle(screen, start, end, color, outline):
    r = int(math.hypot(end[0] - start[0], end[1] - start[1]))  # Euclidean distance from centre to drag end = radius
    if r > 0:                                                    # Skip if radius is zero
        pygame.draw.circle(screen, color, start, r, outline)    # Circle centred at start point


def draw_right_triangle(screen, start, end, color, outline):
    A = (start[0], start[1])    # Top-left — where the right angle sits
    B = (start[0], end[1])      # Bottom-left — directly below A
    C = (end[0],   end[1])      # Bottom-right — at the drag endpoint
    pygame.draw.polygon(screen, color, [A, B, C], outline)


def draw_equilateral_triangle(screen, start, end, color, outline):
    base = abs(end[0] - start[0])          # Base length equals the horizontal drag distance
    if base == 0:                           # Avoid division by zero if no horizontal drag
        return
    height = int(base * math.sqrt(3) / 2)  # Classic equilateral triangle height formula: h = (√3/2) × base
    left   = (min(start[0], end[0]), start[1])              # Left corner of the base
    right  = (max(start[0], end[0]), start[1])              # Right corner of the base
    apex   = ((left[0] + right[0]) // 2, start[1] - height) # Apex centred above the base
    pygame.draw.polygon(screen, color, [left, right, apex], outline)


def draw_rhombus(screen, start, end, color, outline):
    x_min = min(start[0], end[0]);  x_max = max(start[0], end[0])  # Bounding box left and right
    y_min = min(start[1], end[1]);  y_max = max(start[1], end[1])  # Bounding box top and bottom
    cx = (x_min + x_max) // 2;     cy = (y_min + y_max) // 2      # Centre of the bounding box
    pts = [(cx, y_min), (x_max, cy), (cx, y_max), (x_min, cy)]    # Top, right, bottom, left diamond points
    pygame.draw.polygon(screen, color, pts, outline)


def erase(screen, position, size, canvas_top):
    """Erase by painting a black circle at the given position."""
    if position[1] >= canvas_top:  # Only erase within the canvas area, not over the toolbar
        pygame.draw.circle(screen, (0, 0, 0), position, size * 2)  # Black circle, 2× the brush size


# ============================================================
#  Flood Fill
# ============================================================

def flood_fill(surface, pos, fill_color, canvas_rect):
    """BFS flood fill on a pygame Surface.
    Only fills inside canvas_rect to avoid touching the toolbar.
    """
    x, y = pos
    if not canvas_rect.collidepoint(x, y):  # Abort if the click was outside the canvas boundary
        return

    surface.lock()  # Lock the surface for direct pixel read/write (required for get_at/set_at)
    target_color = surface.get_at((x, y))[:3]              # Read the colour of the clicked pixel (ignore alpha)
    fill_rgb     = fill_color[:3] if len(fill_color) == 4 else fill_color  # Strip alpha from fill colour if present

    if target_color == fill_rgb:    # Already the target colour — nothing to fill
        surface.unlock()
        return

    w, h = surface.get_size()       # Surface dimensions used for boundary checks
    top  = canvas_rect.top          # Top Y of the drawable area (below toolbar)
    visited = set()                 # Tracks pixels already added to the queue to avoid revisits
    queue   = deque()               # BFS queue of (x, y) positions to process
    queue.append((x, y))            # Start BFS from the clicked pixel
    visited.add((x, y))

    while queue:
        cx, cy = queue.popleft()                                # Take the next pixel to process
        if not (0 <= cx < w and top <= cy < h):                 # Skip if out of canvas bounds
            continue
        if surface.get_at((cx, cy))[:3] != target_color:       # Skip if this pixel isn't the target colour
            continue
        surface.set_at((cx, cy), fill_rgb)                      # Paint this pixel with the fill colour
        for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):    # Check all 4 neighbours (no diagonals)
            if (nx, ny) not in visited and 0 <= nx < w and top <= ny < h:  # Only queue in-bounds unvisited pixels
                visited.add((nx, ny))
                queue.append((nx, ny))

    surface.unlock()    # Release the surface lock so Pygame can draw normally again