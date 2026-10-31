import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Window settings (responsive to any resolution)
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Sleeping / Ideal Face")

# Colors
BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)
GLOW_BLUE = (70, 180, 255)
BUBBLE_BASE = (130, 215, 255)

# Proportional Ratios (relative to face diameter = face_radius * 2)
FACE_RADIUS_RATIO = 0.36
EYE_WIDTH_RATIO = 0.125
EYE_HEIGHT_RATIO = 0.055
EYE_SPACING_RATIO = 0.165
EYE_Y_OFFSET_RATIO = -0.065

MOUTH_Y_OFFSET_RATIO = 0.075    # Vertical position of mouth relative to center

# Animation timeline constants
TOTAL_CYCLE_MS = 20000     # 20 seconds total loop
BUBBLE_PHASE_MS = 10000    # First 10 seconds: nose bubble (5 cycles of 2s)
BUBBLE_CYCLE_MS = 2000     # Each bubble cycle: 1s growing, 1s shrinking

clock = pygame.time.Clock()


def draw_sleeping_eye(surface, center, width, height, glow_color=GLOW_BLUE):
    """Draws a peaceful downward-curving sleeping eye arc `u u` with soft glow."""
    x, y = center
    surf = pygame.Surface((width * 2, height * 4), pygame.SRCALPHA)
    cx, cy = width, height * 2

    # Arc points for curved downward sleeping eye `u u`
    points = []
    steps = 16
    for i in range(steps + 1):
        t = i / steps
        px = cx - width // 2 + t * width
        # Downward curved hammock dip
        py = cy + height // 2 - (4 * (t - 0.5) ** 2) * height
        points.append((px, py))

    # Glow layer
    for r in range(8, 1, -2):
        alpha = max(10, 50 - r * 5)
        pygame.draw.lines(surf, (*glow_color, alpha), False, points, width=max(3, r + 2))

    # Core white/cyan arc
    pygame.draw.lines(surf, CYAN, False, points, width=max(3, int(width * 0.08)))
    pygame.draw.lines(surf, WHITE, False, points, width=max(1, int(width * 0.04)))

    surface.blit(surf, (x - cx, y - cy))


def draw_small_sleeping_mouth(surface, center, face_diameter):
    """Draws a tiny, relaxed sleeping mouth."""
    x, y = center
    w = int(face_diameter * 0.06)
    h = int(face_diameter * 0.02)
    surf = pygame.Surface((w * 2, h * 3), pygame.SRCALPHA)
    cx, cy = w, h

    pts = [(cx - w // 2, cy), (cx, cy + h // 2), (cx + w // 2, cy)]
    pygame.draw.lines(surf, (*GLOW_BLUE, 80), False, pts, width=4)
    pygame.draw.lines(surf, WHITE, False, pts, width=2)
    surface.blit(surf, (x - cx, y - cy))


def draw_nose_bubble(surface, origin, max_radius, progress, alpha_multiplier=1.0):
    """
    Draws an animated breathing snot bubble.
    progress: 0.0 -> 1.0 (grow), 1.0 -> 0.0 (shrink)
    """
    if progress <= 0.01:
        return

    # Smooth ease in-out scaling with cubic smoothstep
    t = 0.5 * (1.0 - math.cos(progress * math.pi))
    scale = t * t * (3.0 - 2.0 * t)
    current_radius = max(2, int(max_radius * scale))

    ox, oy = origin
    # Float slightly outwards as it inflates
    bx = ox + int(current_radius * 0.6)
    by = oy - int(current_radius * 0.3)

    size = current_radius * 4 + 20
    b_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Outer soft glow
    glow_alpha = int(35 * alpha_multiplier)
    for g_r in range(current_radius + 10, current_radius, -2):
        pygame.draw.circle(b_surf, (*GLOW_BLUE, max(5, glow_alpha)), (cx, cy), g_r)

    # Bubble translucent membrane
    body_alpha = int(140 * alpha_multiplier)
    pygame.draw.circle(b_surf, (*BUBBLE_BASE, body_alpha), (cx, cy), current_radius)

    # Membrane rim highlight
    rim_alpha = int(220 * alpha_multiplier)
    pygame.draw.circle(b_surf, (*WHITE, rim_alpha), (cx, cy), current_radius, width=max(1, current_radius // 10))

    # Specular glint reflection (glossy bubble shine)
    glint_r = max(1, current_radius // 4)
    glint_x = cx - int(current_radius * 0.35)
    glint_y = cy - int(current_radius * 0.35)
    pygame.draw.circle(b_surf, (*WHITE, int(250 * alpha_multiplier)), (glint_x, glint_y), glint_r)

    surface.blit(b_surf, (bx - cx, by - cy))


def draw_glowing_z(surface, center, size, alpha):
    """Draws a stylized, resolution-independent vector 'Z' with glow."""
    if alpha <= 0 or size <= 2:
        return
    x, y = center
    z_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    ox, oy = size, size

    # Vector vertices for 'Z'
    pts = [
        (ox - size // 2, oy - size // 2),
        (ox + size // 2, oy - size // 2),
        (ox - size // 2, oy + size // 2),
        (ox + size // 2, oy + size // 2),
    ]

    # Glow layer
    pygame.draw.lines(z_surf, (*GLOW_BLUE, int(alpha * 0.45)), False, pts, width=max(3, size // 3))
    # Core layer
    pygame.draw.lines(z_surf, (*WHITE, int(alpha)), False, pts, width=max(2, size // 6))

    surface.blit(z_surf, (x - ox, y - oy))


def draw_sleeping_zzz(surface, start_pos, face_diameter, phase_progress):
    """
    Renders floating, gently drifting 'Z z z' letters.
    phase_progress goes from 0.0 to 1.0 across the 10-second Zzz phase.
    """
    sx, sy = start_pos
    base_size = int(face_diameter * 0.055)

    # 3 drifting Z particles
    for i in range(3):
        # Staggered particle cycle
        p_t = (phase_progress * 3.5 + i * 0.33) % 1.0
        
        # Float upward and sway gently
        float_dist = p_t * (face_diameter * 0.35)
        sway = math.sin(p_t * math.pi * 3 + i) * (face_diameter * 0.04)

        zx = sx + int(float_dist * 0.5 + sway)
        zy = sy - int(float_dist)

        # Scale and alpha fade in, then fade out
        z_size = int(base_size * (0.8 + 0.4 * i))
        if p_t < 0.2:
            alpha = int(255 * (p_t / 0.2))
        elif p_t > 0.8:
            alpha = int(255 * ((1.0 - p_t) / 0.2))
        else:
            alpha = 255

        draw_glowing_z(surface, (zx, zy), z_size, alpha)


def draw_face(current_time_ms):
    center = (WIDTH // 2, HEIGHT // 2)
    face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2

    # Background
    screen.fill(BACKGROUND)

    # Circular black robot face plate
    pygame.draw.circle(screen, BLACK, center, face_radius)

    # Geometry
    eye_w = max(4, int(face_diameter * EYE_WIDTH_RATIO))
    eye_h = max(3, int(face_diameter * EYE_HEIGHT_RATIO))
    eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
    eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)

    # Gentle breathing motion (smooth subtle eye pulse)
    breath_cycle = (current_time_ms % 4000) / 4000.0
    breath_offset = int(math.sin(breath_cycle * 2 * math.pi) * 2.0)

    # Draw closed sleeping eyes `u u`
    draw_sleeping_eye(screen, (center[0] - eye_spacing, eye_y + breath_offset), eye_w, eye_h)
    draw_sleeping_eye(screen, (center[0] + eye_spacing, eye_y + breath_offset), eye_w, eye_h)

    # Draw tiny sleeping mouth
    mouth_pos = (center[0], center[1] + int(face_diameter * MOUTH_Y_OFFSET_RATIO))
    draw_small_sleeping_mouth(screen, mouth_pos, face_diameter)

    # Timeline calculation: 20 seconds total cycle
    timeline_ms = current_time_ms % TOTAL_CYCLE_MS

    if timeline_ms < BUBBLE_PHASE_MS:
        # Phase 1 (0–10s): Nose bubble animation (5 cycles of 2 seconds)
        cycle_in_phase = timeline_ms % BUBBLE_CYCLE_MS
        cycle_idx = timeline_ms // BUBBLE_CYCLE_MS  # 0 to 4
        
        # In each 2s cycle: 0..1s grow, 1..2s shrink
        if cycle_in_phase < 1000:
            bubble_progress = cycle_in_phase / 1000.0
        else:
            bubble_progress = (2000 - cycle_in_phase) / 1000.0

        # On the 5th (last) cycle, as it approaches 10s, fade out smoothly into Zzz
        alpha_mult = 1.0
        if cycle_idx == 4 and cycle_in_phase > 1200:
            alpha_mult = max(0.0, (2000 - cycle_in_phase) / 800.0)

        bubble_origin = (center[0] + int(face_diameter * 0.035), center[1] + int(face_diameter * 0.045))
        max_bubble_r = int(face_diameter * 0.080)
        draw_nose_bubble(screen, bubble_origin, max_bubble_r, bubble_progress, alpha_mult)

    else:
        # Phase 2 (10–20s): Floating sleeping 'Z z z'
        zzz_timeline = timeline_ms - BUBBLE_PHASE_MS
        zzz_progress = zzz_timeline / float(TOTAL_CYCLE_MS - BUBBLE_PHASE_MS)
        zzz_origin = (center[0] + int(face_diameter * 0.12), center[1] - int(face_diameter * 0.08))
        draw_sleeping_zzz(screen, zzz_origin, face_diameter, zzz_progress)

    pygame.display.flip()


def main():
    running = True

    while running:
        current_time_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        draw_face(current_time_ms)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
