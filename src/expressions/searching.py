import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Window settings
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Searching Face (🌐)")

# Colors
BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)
GLOW_BLUE = (70, 180, 255)
DEEP_CYAN = (40, 140, 220)

# Proportional Ratios (relative to face diameter = face_radius * 2)
FACE_RADIUS_RATIO = 0.36
EYE_WIDTH_RATIO = 0.125
EYE_HEIGHT_RATIO = 0.130
EYE_SPACING_RATIO = 0.165
EYE_Y_OFFSET_RATIO = -0.095

GLOBE_Y_OFFSET_RATIO = 0.11     # Vertical position of globe relative to center
WAVE_Y_OFFSET_RATIO = 0.29      # Vertical position of data wave relative to center

clock = pygame.time.Clock()


def draw_scanning_eye(surface, center, width, height, scan_x_offset=0, t_ms=0):
    """Draws an attentive scanning eye with glowing cyan halo and digital reticle."""
    x, y = center
    gx = x + scan_x_offset

    # Soft outer glow
    glow_surf = pygame.Surface((width * 2 + 30, height * 2 + 30), pygame.SRCALPHA)
    cx = glow_surf.get_width() // 2
    cy = glow_surf.get_height() // 2

    for r in range(14, 2, -3):
        alpha = max(6, int(22 * (1.0 - r / 14)))
        pygame.draw.ellipse(
            glow_surf,
            (*GLOW_BLUE, alpha),
            (cx - width // 2 - r, cy - height // 2 - r, width + r * 2, height + r * 2),
        )
    surface.blit(glow_surf, (gx - cx, y - cy))

    # Outer dome
    eye_rect = pygame.Rect(gx - width // 2, y - height // 2, width, height)
    pygame.draw.ellipse(surface, CYAN, eye_rect)
    pygame.draw.rect(surface, CYAN, (eye_rect.left, eye_rect.centery, width, max(1, height // 2)))

    # Inner bright white core
    core_inset = max(2, int(width * 0.08))
    core_rect = pygame.Rect(
        eye_rect.left + core_inset,
        eye_rect.top + core_inset,
        max(2, width - core_inset * 2),
        max(2, height - core_inset * 2),
    )
    pygame.draw.ellipse(surface, WHITE, core_rect)
    pygame.draw.rect(surface, WHITE, (core_rect.left, core_rect.centery, core_rect.width, max(1, core_rect.height // 2)))

    # Digital horizontal scanline sweeping through the eye
    scan_line_y = eye_rect.top + int(((t_ms % 1200) / 1200.0) * eye_rect.height)
    pygame.draw.line(surface, (*WHITE, 220), (eye_rect.left + 3, scan_line_y), (eye_rect.right - 3, scan_line_y), width=1)


def draw_spinning_globe(surface, center, radius, t_ms):
    """
    Renders a 3D procedural spinning wireframe holographic globe (🌐).
    Features rotating longitude meridians, latitude rings, and pulsing sonar signal rings.
    """
    cx, cy = center
    angle = (t_ms / 2000.0) * (2 * math.pi)

    # 1. Pulsing radiating web search waves (concentric radio signals)
    pulse_t = (t_ms / 1500.0) % 1.0
    for i in range(2):
        p = (pulse_t + i * 0.5) % 1.0
        wave_r = int(radius * (1.1 + p * 0.8))
        wave_alpha = int(90 * (1.0 - p))
        wave_surf = pygame.Surface((wave_r * 2 + 10, wave_r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(wave_surf, (*GLOW_BLUE, wave_alpha), (wave_r + 5, wave_r + 5), wave_r, width=1)
        surface.blit(wave_surf, (cx - wave_r - 5, cy - wave_r - 5))

    # 2. Outer atmospheric bloom
    glow_surf = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
    gcx, gcy = radius * 3 // 2, radius * 3 // 2
    for r in range(radius + 15, radius, -3):
        alpha = max(4, int(20 * (1.0 - (r - radius) / 15)))
        pygame.draw.circle(glow_surf, (*GLOW_BLUE, alpha), (gcx, gcy), r)
    surface.blit(glow_surf, (cx - gcx, cy - gcy))

    # 3. Outer boundary circle
    pygame.draw.circle(surface, CYAN, (cx, cy), radius, width=2)
    pygame.draw.circle(surface, (*WHITE, 180), (cx, cy), radius, width=1)

    # 4. Latitude lines (parallels)
    for lat_factor in (0.38, 0.72):
        lh = int(radius * lat_factor)
        lw = int(math.sqrt(max(0, radius**2 - lh**2)))
        pygame.draw.ellipse(surface, DEEP_CYAN, (cx - lw, cy - lh - 1, lw * 2, 2))
        pygame.draw.ellipse(surface, DEEP_CYAN, (cx - lw, cy + lh - 1, lw * 2, 2))

    # 5. Equator line
    pygame.draw.line(surface, (*WHITE, 200), (cx - radius, cy), (cx + radius, cy), width=1)

    # 6. Rotating longitude meridians (spinning around Y-axis)
    num_meridians = 4
    for i in range(num_meridians):
        lon_ang = angle + i * (math.pi / num_meridians)
        cos_val = math.cos(lon_ang)
        lon_w = max(1, int(radius * abs(cos_val)))
        
        # Color intensity based on 3D depth facing front or back
        if math.sin(lon_ang) >= 0:
            meridian_color = CYAN
            meridian_width = 2 if lon_w > 4 else 1
        else:
            meridian_color = DEEP_CYAN
            meridian_width = 1

        pygame.draw.ellipse(
            surface,
            meridian_color,
            (cx - lon_w, cy - radius, lon_w * 2, radius * 2),
            width=meridian_width,
        )

    # 7. Central prime meridian (fixed axis)
    pygame.draw.line(surface, (*WHITE, 120), (cx, cy - radius), (cx, cy + radius), width=1)

    # 8. Sweeping radar scan beam (360 degree sweep)
    sweep_ang = (t_ms / 1200.0) * (2 * math.pi)
    beam_x = cx + int(math.cos(sweep_ang) * (radius - 2))
    beam_y = cy + int(math.sin(sweep_ang) * (radius - 2))
    pygame.draw.line(surface, WHITE, (cx, cy), (beam_x, beam_y), width=2)
    pygame.draw.circle(surface, WHITE, (beam_x, beam_y), 3)


def draw_digital_mouth_wave(surface, center, face_diameter, t_ms):
    """Draws dynamic digital search audio/data waveform bars below the globe."""
    cx, cy = center
    num_bars = 7
    bar_w = max(2, int(face_diameter * 0.008))
    spacing = max(3, int(face_diameter * 0.015))
    total_w = num_bars * (bar_w + spacing) - spacing
    start_x = cx - total_w // 2

    for i in range(num_bars):
        # Sine-wave audio/data animation (smoother period)
        h_ratio = 0.3 + 0.7 * abs(math.sin((t_ms / 350.0) + i * 0.9))
        bar_h = max(3, int(face_diameter * 0.035 * h_ratio))
        bx = start_x + i * (bar_w + spacing)
        by = cy - bar_h // 2

        pygame.draw.rect(surface, (*GLOW_BLUE, 70), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, CYAN, (bx, by, bar_w, bar_h))


def draw_face(current_time_ms):
    center = (WIDTH // 2, HEIGHT // 2)
    face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2

    # Background
    screen.fill(BACKGROUND)

    # Circular black robot face plate
    pygame.draw.circle(screen, BLACK, center, face_radius)

    # Search scanning gaze (smooth left-to-right eye pan as if reading web results)
    scan_cycle = (current_time_ms / 2200.0) * (2 * math.pi)
    scan_x_offset = int(math.sin(scan_cycle) * (face_diameter * 0.028))

    eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
    eye_w = int(face_diameter * EYE_WIDTH_RATIO)
    eye_h = int(face_diameter * EYE_HEIGHT_RATIO)
    eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)

    # Left & Right Scanning Eyes
    draw_scanning_eye(screen, (center[0] - eye_spacing, eye_y), eye_w, eye_h, scan_x_offset, current_time_ms)
    draw_scanning_eye(screen, (center[0] + eye_spacing, eye_y), eye_w, eye_h, scan_x_offset, current_time_ms)

    # Holographic Spinning Globe (🌐) in lower-center
    globe_center = (center[0], center[1] + int(face_diameter * GLOBE_Y_OFFSET_RATIO))
    globe_radius = int(face_diameter * 0.125)
    draw_spinning_globe(screen, globe_center, globe_radius, current_time_ms)

    # Digital search data wave beneath the globe
    wave_center = (center[0], center[1] + int(face_diameter * WAVE_Y_OFFSET_RATIO))
    draw_digital_mouth_wave(screen, wave_center, face_diameter, current_time_ms)

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
