# ============================================================
#  drawing_tools.py  —  Paint App
#  Contains:
#    - All drawing functions (pen, rect, circle, square,
#      right triangle, equilateral triangle, rhombus, eraser)
#    - Toolbar rendering
#    - Toolbar click detection
# ============================================================

import pygame       # Pygame library for graphics and window management
import math         # Math library for sqrt, hypot, etc.

# Height of each toolbar row in pixels
TOOLBAR_HEIGHT       = 50
TOOLBAR_TOTAL_HEIGHT = 100   # Both rows combined = 100px

# ============================================================
#  Colour Helper
# ============================================================

def get_solid_color(color_mode):
    """Return a solid RGB tuple for the given color_mode string."""
    if color_mode == 'red':         # If mode is red, return pure red
        return (255, 0, 0)
    elif color_mode == 'green':     # If mode is green, return pure green
        return (0, 255, 0)
    else:                           # Default fallback is pure blue
        return (0, 0, 255)


def get_gradient_color(index, color_mode):
    """Return a gradient colour based on index (0-255) for pen strokes."""
    c1 = max(0, min(255, 2 * index - 256))  # Dark component: ramps up only after index > 128
    c2 = max(0, min(255, 2 * index))        # Bright component: ramps up from index 0
    if color_mode == 'blue':                # Blue gradient: c1 tints red/green, c2 drives blue
        return (c1, c1, c2)
    elif color_mode == 'red':               # Red gradient: c2 drives red channel
        return (c2, c1, c1)
    elif color_mode == 'green':             # Green gradient: c2 drives green channel
        return (c1, c2, c1)
    else:                                   # Default to blue gradient
        return (c1, c1, c2)


# ============================================================
#  Toolbar Definition
# ============================================================

# Each tuple: (button label, mode string, x position on screen)
TOOLS = [
    ("Pen",     "pen",     10),
    ("Rect",    "rect",    90),
    ("Square",  "square",  170),
    ("Circle",  "circle",  250),
    ("RTri",    "rtri",    330),
    ("ETri",    "etri",    410),
    ("Rhombus", "rhombus", 490),
    ("Eraser",  "eraser",  570),
]

# Each tuple: (button label, colour mode string, x position on screen)
COLOR_BUTTONS = [
    ("R", "red",   10),
    ("G", "green", 60),
    ("B", "blue",  110),
]


def draw_toolbar(screen, mode, color_mode, screen_width):
    """Render the two-row toolbar onto the screen."""
    font = pygame.font.SysFont("Verdana", 12)   # Small font for button labels

    # Draw dark grey background for tool row
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, screen_width, TOOLBAR_HEIGHT))

    # Loop through each tool and draw its button
    for label, tool_mode, x in TOOLS:
        color = (255, 255, 255) if mode == tool_mode else (120, 120, 120)  # White if active, grey if not
        pygame.draw.rect(screen, color, (x, 6, 72, 34), 2)                 # Draw button border (thickness=2)
        text = font.render(label, True, color)                              # Render label text
        screen.blit(text, (x + 5, 16))                                     # Draw text inside the button

    # Draw darker background for colour row
    pygame.draw.rect(screen, (30, 30, 30), (0, TOOLBAR_HEIGHT, screen_width, TOOLBAR_HEIGHT))

    # Loop through each colour button and draw it
    for label, col, x in COLOR_BUTTONS:
        active = color_mode == col                          # True if this colour is currently selected
        rgb = get_solid_color(col)                          # Get the actual RGB value of this colour
        pygame.draw.rect(screen, rgb, (x, TOOLBAR_HEIGHT + 8, 40, 34), 0 if active else 2)  # Filled if active, outline if not
        text = font.render(label, True, (255, 255, 255))   # White label text
        screen.blit(text, (x + 13, TOOLBAR_HEIGHT + 16))   # Center text inside the button

    # Draw a small usage hint on the right side of the colour row
    hint = font.render("LClick=+size  RClick=-size", True, (150, 150, 150))
    screen.blit(hint, (170, TOOLBAR_HEIGHT + 16))           # Position hint to the right of colour buttons


def get_tool_from_click(x, y):
    """Return the tool or colour string that was clicked, or None."""
    # Check if click is in the top row (tool buttons)
    if 0 <= y <= TOOLBAR_HEIGHT:
        for label, tool_mode, tx in TOOLS:             # Loop through all tools
            if tx <= x <= tx + 72:                     # Check if x is within this button's width
                return tool_mode                        # Return the matched tool mode

    # Check if click is in the bottom row (colour buttons)
    if TOOLBAR_HEIGHT <= y <= TOOLBAR_TOTAL_HEIGHT:
        for label, col, cx in COLOR_BUTTONS:           # Loop through all colour buttons
            if cx <= x <= cx + 40:                     # Check if x is within this button's width
                return col                             # Return the matched colour mode

    return None     # Click was outside all buttons


# ============================================================
#  Drawing Functions
# ============================================================

def drawLineBetween(screen, index, start, end, width, color_mode):
    """Draw a smooth pen stroke segment between two points."""
    color      = get_gradient_color(index, color_mode)  # Pick colour based on stroke progress
    dx         = start[0] - end[0]                      # Horizontal distance between points
    dy         = start[1] - end[1]                      # Vertical distance between points
    iterations = max(abs(dx), abs(dy))                  # Number of steps = longest axis, ensures no gaps
    for i in range(iterations):                         # Step along the line
        progress  = i / iterations                      # 0.0 → 1.0, how far along we are
        aprogress = 1 - progress                        # Inverse: weight for start point
        x = int(aprogress * start[0] + progress * end[0])  # Linearly interpolate X
        y = int(aprogress * start[1] + progress * end[1])  # Linearly interpolate Y
        pygame.draw.circle(screen, color, (x, y), width)   # Draw a filled circle at this step


def draw_rectangle(screen, start, end, color_mode, outline):
    """Draw an axis-aligned rectangle from start to end corner."""
    color = get_solid_color(color_mode)         # Get fill/outline colour
    x = min(start[0], end[0])                  # Left edge (handles dragging in any direction)
    y = min(start[1], end[1])                  # Top edge
    w = abs(end[0] - start[0])                 # Width = horizontal drag distance
    h = abs(end[1] - start[1])                 # Height = vertical drag distance
    pygame.draw.rect(screen, color, (x, y, w, h), outline)  # Draw; outline=0 fills, >0 draws border only


def draw_square(screen, start, end, color_mode, outline):
    """Draw a perfect square — side = shorter dimension of the drag."""
    color = get_solid_color(color_mode)         # Get fill/outline colour
    dx   = end[0] - start[0]                   # Raw horizontal drag delta
    dy   = end[1] - start[1]                   # Raw vertical drag delta
    side = min(abs(dx), abs(dy))               # Use the shorter side to keep it square
    x = start[0] if dx >= 0 else start[0] - side   # Shift left edge if dragging left
    y = start[1] if dy >= 0 else start[1] - side   # Shift top edge if dragging up
    pygame.draw.rect(screen, color, (x, y, side, side), outline)  # Draw the square


def draw_circle(screen, start, end, color_mode, outline):
    """Draw a circle centred on start with radius = distance to end."""
    color = get_solid_color(color_mode)                             # Get fill/outline colour
    r     = int(math.hypot(end[0] - start[0], end[1] - start[1])) # Euclidean distance = radius
    if r > 0:                                                       # Skip if radius is zero
        pygame.draw.circle(screen, color, start, r, outline)       # Draw circle at start point


def draw_right_triangle(screen, start, end, color_mode, outline):
    """Draw a right-angled triangle. Right angle sits at top-left."""
    color = get_solid_color(color_mode)         # Get fill/outline colour
    A = (start[0], start[1])   # Top-left corner — where the right angle is
    B = (start[0], end[1])     # Bottom-left corner — directly below A
    C = (end[0],   end[1])     # Bottom-right corner — at drag endpoint
    pygame.draw.polygon(screen, color, [A, B, C], outline)  # Draw triangle with 3 vertices


def draw_equilateral_triangle(screen, start, end, color_mode, outline):
    """Draw an equilateral triangle. Base = horizontal drag width."""
    color  = get_solid_color(color_mode)                # Get fill/outline colour
    base   = abs(end[0] - start[0])                     # Base length = horizontal drag distance
    if base == 0:                                        # Skip if no width (avoid division by zero)
        return
    height = int(base * math.sqrt(3) / 2)              # Equilateral triangle height formula
    left   = (min(start[0], end[0]), start[1])          # Left base corner
    right  = (max(start[0], end[0]), start[1])          # Right base corner
    apex   = ((left[0] + right[0]) // 2, start[1] - height)  # Apex: centered above base
    pygame.draw.polygon(screen, color, [left, right, apex], outline)  # Draw the triangle


def draw_rhombus(screen, start, end, color_mode, outline):
    """Draw a rhombus (diamond) fitted inside the drag bounding box."""
    color = get_solid_color(color_mode)         # Get fill/outline colour
    x_min = min(start[0], end[0])              # Left edge of bounding box
    x_max = max(start[0], end[0])              # Right edge of bounding box
    y_min = min(start[1], end[1])              # Top edge of bounding box
    y_max = max(start[1], end[1])              # Bottom edge of bounding box
    cx    = (x_min + x_max) // 2              # Horizontal center of bounding box
    cy    = (y_min + y_max) // 2              # Vertical center of bounding box
    top    = (cx,    y_min)     # Top point of the diamond
    right  = (x_max, cy)        # Right point of the diamond
    bottom = (cx,    y_max)     # Bottom point of the diamond
    left   = (x_min, cy)        # Left point of the diamond
    pygame.draw.polygon(screen, color, [top, right, bottom, left], outline)  # Draw 4-point diamond


def erase(screen, position, radius):
    """Erase by painting a black circle at position."""
    pygame.draw.circle(screen, (0, 0, 0), position, radius * 3)  # Black circle, 3x larger than pen size