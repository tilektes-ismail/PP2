import pygame

# Toolbar height constant
TOOLBAR_HEIGHT = 50

def draw_toolbar(screen, mode, color_mode):
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, 640, TOOLBAR_HEIGHT))

    tools = [
        ("Pen",    "pen",    10),
        ("Rect",   "rect",   90),
        ("Circle", "circle", 170),
        ("Eraser", "eraser", 250),
    ]

    font = pygame.font.SysFont("Verdana", 14)

    for label, tool_mode, x in tools:
        color = (255, 255, 255) if mode == tool_mode else (120, 120, 120)
        pygame.draw.rect(screen, color, (x, 8, 70, 34), 2)
        text = font.render(label, True, color)
        screen.blit(text, (x + 10, 16))

    colors = [
        ("R", "red",   420),
        ("G", "green", 490),
        ("B", "blue",  560),
    ]

    for label, col, x in colors:
        active = color_mode == col
        rgb = (255,0,0) if col=="red" else (0,255,0) if col=="green" else (0,0,255)
        pygame.draw.rect(screen, rgb, (x, 8, 40, 34), 0 if active else 2)
        text = font.render(label, True, (255, 255, 255))
        screen.blit(text, (x + 13, 16))


def drawLineBetween(screen, index, start, end, width, color_mode):
    c1 = max(0, min(255, 2 * index - 256))
    c2 = max(0, min(255, 2 * index))

    if color_mode == 'blue':
        color = (c1, c1, c2)
    elif color_mode == 'red':
        color = (c2, c1, c1)
    elif color_mode == 'green':
        color = (c1, c2, c1)
    else:
        color = (c1, c1, c2)

    dx = start[0] - end[0]
    dy = start[1] - end[1]
    iterations = max(abs(dx), abs(dy))

    for i in range(iterations):
        progress = 1.0 * i / iterations
        aprogress = 1 - progress
        x = int(aprogress * start[0] + progress * end[0])
        y = int(aprogress * start[1] + progress * end[1])
        pygame.draw.circle(screen, color, (x, y), width)


def draw_rectangle(screen, start, end, color_mode, radius):
    if color_mode == 'red':
        color = (255, 0, 0)
    elif color_mode == 'green':
        color = (0, 255, 0)
    else:
        color = (0, 0, 255)

    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])

    pygame.draw.rect(screen, color, (x, y, w, h), radius)


def draw_circle(screen, start, end, color_mode, radius):
    if color_mode == 'red':
        color = (255, 0, 0)
    elif color_mode == 'green':
        color = (0, 255, 0)
    else:
        color = (0, 0, 255)

    r = int(((end[0] - start[0])**2 + (end[1] - start[1])**2) ** 0.5)
    if r > 0:
        pygame.draw.circle(screen, color, start, r, radius)


def erase(screen, position, radius):
    pygame.draw.circle(screen, (0, 0, 0), position, radius * 3)


def get_tool_from_click(x, y):
    if y > TOOLBAR_HEIGHT:
        return None
    tools = [("pen", 10, 80), ("rect", 90, 160), ("circle", 170, 240), ("eraser", 250, 320)]
    for tool, x1, x2 in tools:
        if x1 <= x <= x2: return tool
    colors = [("red", 420, 460), ("green", 490, 530), ("blue", 560, 600)]
    for col, x1, x2 in colors:
        if x1 <= x <= x2: return col
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()

    radius = 15
    mode = 'pen'
    color_mode = 'blue'
    points = []
    drawing = False
    start_pos = (0, 0)

    canvas = pygame.Surface((640, 480))
    canvas.fill((0, 0, 0))

    while True:
        pressed = pygame.key.get_pressed()
        alt_held = pressed[pygame.K_LALT] or pressed[pygame.K_RALT]
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_w and ctrl_held) or (event.key == pygame.K_F4 and alt_held) or (event.key == pygame.K_ESCAPE):
                    return
                if event.key == pygame.K_r: color_mode = 'red'
                elif event.key == pygame.K_g: color_mode = 'green'
                elif event.key == pygame.K_b: color_mode = 'blue'

            if event.type == pygame.MOUSEBUTTONDOWN:
                click_x, click_y = event.pos
                tool = get_tool_from_click(click_x, click_y)
                
                # Check if clicking toolbar
                if tool in ('pen', 'rect', 'circle', 'eraser'):
                    mode = tool
                    points = []
                elif tool in ('red', 'green', 'blue'):
                    color_mode = tool
                
                # Check for canvas clicks
                elif click_y > TOOLBAR_HEIGHT:
                    if event.button == 1:
                        radius = min(200, radius + 1) # Grow radius
                        drawing = True
                        start_pos = event.pos
                    elif event.button == 3:
                        radius = max(1, radius - 1)   # Shrink radius

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and drawing:
                    drawing = False
                    if mode == 'rect':
                        draw_rectangle(canvas, start_pos, event.pos, color_mode, 2)
                    elif mode == 'circle':
                        draw_circle(canvas, start_pos, event.pos, color_mode, 2)
                    elif mode == 'pen':
                        i = 0
                        while i < len(points) - 1:
                            drawLineBetween(canvas, i, points[i], points[i+1], radius, color_mode)
                            i += 1
                        points = [] 

            if event.type == pygame.MOUSEMOTION:
                if mode == 'pen' and drawing:
                    if event.pos[1] > TOOLBAR_HEIGHT:
                        points = points + [event.pos]
                        points = points[-256:] 
                elif mode == 'eraser' and drawing:
                    if event.pos[1] > TOOLBAR_HEIGHT:
                        erase(canvas, event.pos, radius)

        # Rendering
        screen.blit(canvas, (0, 0))
        
        i = 0
        while i < len(points) - 1:
            drawLineBetween(screen, i, points[i], points[i + 1], radius, color_mode)
            i += 1

        if drawing and mode in ('rect', 'circle'):
            current_pos = pygame.mouse.get_pos()
            if mode == 'rect': draw_rectangle(screen, start_pos, current_pos, color_mode, 2)
            elif mode == 'circle': draw_circle(screen, start_pos, current_pos, color_mode, 2)

        draw_toolbar(screen, mode, color_mode)
        pygame.display.flip()
        clock.tick(60)

main()