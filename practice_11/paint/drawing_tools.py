# ============================================================
#  drawing_tools.py  —  Paint App
#  Contains:
#    - All drawing functions (pen, rect, circle, square,
#      right triangle, equilateral triangle, rhombus, eraser)
#    - Toolbar rendering
#    - Toolbar click detection
# ============================================================

import pygame
import math

# Height of each toolbar row
TOOLBAR_HEIGHT       = 50
TOOLBAR_TOTAL_HEIGHT = 100   # Two rows total

# ============================================================
#  Colour Helper
# ============================================================

def get_solid_color(color_mode):
    """Return a solid RGB tuple for the given color_mode string."""
    if color_mode == 'red':
        return (255, 0, 0)
    elif color_mode == 'green':
        return (0, 255, 0)
    else:
        return (0, 0, 255)


def get_gradient_color(index, color_mode):
    """Return a gradient colour based on index (0-255) for pen strokes."""
    c1 = max(0, min(255, 2 * index - 256))
    c2 = max(0, min(255, 2 * index))
    if color_mode == 'blue':
        return (c1, c1, c2)
    elif color_mode == 'red':
        return (c2, c1, c1)
    elif color_mode == 'green':
        return (c1, c2, c1)
    else:
        return (c1, c1, c2)


# ============================================================
#  Toolbar Definition
# ============================================================

# (display label, mode string, x position)
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

# (display label, colour mode string, x position)
COLOR_BUTTONS = [
    ("R", "red",   10),
    ("G", "green", 60),
    ("B", "blue",  110),
]


def draw_toolbar(screen, mode, color_mode, screen_width):
    """Render the two-row toolbar onto the screen.
    Row 1: tool buttons. Row 2: colour buttons.
    """
    font = pygame.font.SysFont("Verdana", 12)

    # Row 1 background
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, screen_width, TOOLBAR_HEIGHT))

    # Tool buttons
    for label, tool_mode, x in TOOLS:
        color = (255, 255, 255) if mode == tool_mode else (120, 120, 120)
        pygame.draw.rect(screen, color, (x, 6, 72, 34), 2)
        text = font.render(label, True, color)
        screen.blit(text, (x + 5, 16))

    # Row 2 background
    pygame.draw.rect(screen, (30, 30, 30), (0, TOOLBAR_HEIGHT, screen_width, TOOLBAR_HEIGHT))

    # Colour buttons
    for label, col, x in COLOR_BUTTONS:
        active = color_mode == col
        rgb = get_solid_color(col)
        pygame.draw.rect(screen, rgb, (x, TOOLBAR_HEIGHT + 8, 40, 34), 0 if active else 2)
        text = font.render(label, True, (255, 255, 255))
        screen.blit(text, (x + 13, TOOLBAR_HEIGHT + 16))

    # Hint text
    hint = font.render("LClick=+size  RClick=-size", True, (150, 150, 150))
    screen.blit(hint, (170, TOOLBAR_HEIGHT + 16))


def get_tool_from_click(x, y):
    """Return the tool or colour string that was clicked, or None."""
    # Row 1: tool buttons
    if 0 <= y <= TOOLBAR_HEIGHT:
        for label, tool_mode, tx in TOOLS:
            if tx <= x <= tx + 72:
                return tool_mode

    # Row 2: colour buttons
    if TOOLBAR_HEIGHT <= y <= TOOLBAR_TOTAL_HEIGHT:
        for label, col, cx in COLOR_BUTTONS:
            if cx <= x <= cx + 40:
                return col

    return None


# ============================================================
#  Drawing Functions
# ============================================================

def drawLineBetween(screen, index, start, end, width, color_mode):
    """Draw a smooth pen stroke segment between two points."""
    color      = get_gradient_color(index, color_mode)
    dx         = start[0] - end[0]
    dy         = start[1] - end[1]
    iterations = max(abs(dx), abs(dy))
    for i in range(iterations):
        progress  = i / iterations
        aprogress = 1 - progress
        x = int(aprogress * start[0] + progress * end[0])
        y = int(aprogress * start[1] + progress * end[1])
        pygame.draw.circle(screen, color, (x, y), width)


def draw_rectangle(screen, start, end, color_mode, outline):
    """Draw an axis-aligned rectangle from start to end corner."""
    color = get_solid_color(color_mode)
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])
    pygame.draw.rect(screen, color, (x, y, w, h), outline)


def draw_square(screen, start, end, color_mode, outline):
    """Draw a perfect square — side = shorter dimension of the drag."""
    color = get_solid_color(color_mode)
    dx   = end[0] - start[0]
    dy   = end[1] - start[1]
    side = min(abs(dx), abs(dy))
    x = start[0] if dx >= 0 else start[0] - side
    y = start[1] if dy >= 0 else start[1] - side
    pygame.draw.rect(screen, color, (x, y, side, side), outline)


def draw_circle(screen, start, end, color_mode, outline):
    """Draw a circle centred on start with radius = distance to end."""
    color = get_solid_color(color_mode)
    r     = int(math.hypot(end[0] - start[0], end[1] - start[1]))
    if r > 0:
        pygame.draw.circle(screen, color, start, r, outline)


def draw_right_triangle(screen, start, end, color_mode, outline):
    """Draw a right-angled triangle. Right angle sits at top-left."""
    color = get_solid_color(color_mode)
    A = (start[0], start[1])   # top-left  — right angle
    B = (start[0], end[1])     # bottom-left
    C = (end[0],   end[1])     # bottom-right
    pygame.draw.polygon(screen, color, [A, B, C], outline)


def draw_equilateral_triangle(screen, start, end, color_mode, outline):
    """Draw an equilateral triangle. Base = horizontal drag width."""
    color  = get_solid_color(color_mode)
    base   = abs(end[0] - start[0])
    if base == 0:
        return
    height = int(base * math.sqrt(3) / 2)
    left   = (min(start[0], end[0]), start[1])
    right  = (max(start[0], end[0]), start[1])
    apex   = ((left[0] + right[0]) // 2, start[1] - height)
    pygame.draw.polygon(screen, color, [left, right, apex], outline)


def draw_rhombus(screen, start, end, color_mode, outline):
    """Draw a rhombus (diamond) fitted inside the drag bounding box."""
    color = get_solid_color(color_mode)
    x_min = min(start[0], end[0])
    x_max = max(start[0], end[0])
    y_min = min(start[1], end[1])
    y_max = max(start[1], end[1])
    cx    = (x_min + x_max) // 2
    cy    = (y_min + y_max) // 2
    top    = (cx,    y_min)
    right  = (x_max, cy)
    bottom = (cx,    y_max)
    left   = (x_min, cy)
    pygame.draw.polygon(screen, color, [top, right, bottom, left], outline)


def erase(screen, position, radius):
    """Erase by painting a black circle at position."""
    pygame.draw.circle(screen, (0, 0, 0), position, radius * 3)
