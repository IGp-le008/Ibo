import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Window settings (can be changed to any screen resolution)
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Greeting Face")

# Colors
BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)

# -------------------------------------------------------------
# Proportional Ratios (relative to face diameter = face_radius * 2)
# -------------------------------------------------------------
FACE_RADIUS_RATIO = 0.36        # Relative to min(WIDTH, HEIGHT)
EYE_WIDTH_RATIO = 0.122         # Eye width relative to face diameter
EYE_HEIGHT_RATIO = 0.130        # Base eye height relative to face diameter
EYE_SPACING_RATIO = 0.163       # Distance from center to each eye center
EYE_Y_OFFSET_RATIO = -0.076     # Vertical position relative to center
EYE_GLOW_RATIO = 0.039          # Max outer glow radius relative to face diameter
EYE_CORE_INSET_RATIO = 0.009    # Inset for inner white core relative to face diameter

MOUTH_Y_OFFSET_RATIO = 0.140    # Vertical position of mouth relative to center 

MOUTH_GLOW_W_RATIO = 0.152      # Width of mouth glow relative to face diameter
MOUTH_GLOW_H_RATIO = 0.083      # Height of mouth glow relative to face diameter

# Normalized (dx, dy) polygon points for the smile relative to face diameter
MOUTH_POINTS_RATIOS = [
    (-0.0587, -0.0174),
    ( 0.0587, -0.0174),
    ( 0.0522,  0.0022),
    ( 0.0370,  0.0196),
    ( 0.0174,  0.0283),
    ( 0.0000,  0.0304),
    (-0.0174,  0.0283),
    (-0.0370,  0.0196),
    (-0.0522,  0.0022),
]

# Animation timing & scale multipliers
BLINK_INTERVAL_MS = 4000  # Trigger blink every 4 seconds
BLINK_DURATION_MS = 240   # Total blink duration in milliseconds
SMILE_SIZE = 1.65        # Scale multiplier for the smile (1.0 = default baseline, 1.25 = 1.25x larger)

clock = pygame.time.Clock()


def get_blink_scale(current_time_ms):
    """Calculate eye openness scale factor (1.0 = fully open, ~0.08 = closed) for a 4s blink cycle."""
    cycle = current_time_ms % BLINK_INTERVAL_MS
    if cycle < BLINK_DURATION_MS:
        progress = cycle / BLINK_DURATION_MS
        blink_factor = math.sin(progress * math.pi)
        return 1.0 - (0.92 * blink_factor)
    return 1.0


def draw_glowing_eye(surface, center, width, height, face_diameter):
    """Draw a soft cyan glowing eye with a flat bottom and illuminated core scaled to face diameter."""
    x, y = center
    height = max(2, height)

    # Glow surface sized to bounding box of the eye + glow for performance
    max_glow_radius = max(3, int(face_diameter * EYE_GLOW_RATIO))
    step = max(1, max_glow_radius // 6)

    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for radius in range(max_glow_radius, 1, -step):
        alpha = max(4, int(20 * (1.0 - radius / max_glow_radius)))
        pygame.draw.ellipse(
            glow,
            (70, 180, 255, alpha),
            (
                x - width // 2 - radius,
                y - height // 2 - radius,
                width + radius * 2,
                height + radius * 2,
            ),
        )

    surface.blit(glow, (0, 0))

    # Outer cyan shell
    eye_rect = pygame.Rect(
        x - width // 2,
        y - height // 2,
        width,
        height,
    )

    pygame.draw.ellipse(surface, CYAN, eye_rect)
    pygame.draw.rect(
        surface,
        CYAN,
        (
            eye_rect.left,
            y,
            width,
            max(1, height // 2),
        ),
    )

    # Inner bright white core
    core_inset = max(1, int(face_diameter * EYE_CORE_INSET_RATIO))
    min_core_height = core_inset * 3

    if height > min_core_height:
        core_rect = pygame.Rect(
            eye_rect.left + core_inset,
            eye_rect.top + core_inset,
            max(2, width - core_inset * 2),
            max(2, height - core_inset * 2),
        )
        pygame.draw.ellipse(surface, WHITE, core_rect)
        pygame.draw.rect(
            surface,
            WHITE,
            (
                core_rect.left,
                core_rect.top + core_rect.height // 2,
                core_rect.width,
                max(1, core_rect.height // 2),
            ),
        )
    else:
        # Subtle illuminated slit when closed during blink
        slit_height = max(1, core_inset)
        slit_rect = pygame.Rect(
            eye_rect.left + core_inset,
            y - slit_height // 2,
            max(1, width - core_inset * 2),
            slit_height,
        )
        pygame.draw.rect(surface, WHITE, slit_rect)


def draw_mouth(surface, center, face_diameter, smile_size=1.0):
    """Draw the small, friendly cyan smile scaled to face diameter and smile_size."""
    x, y = center

    glow_w = max(4, int(face_diameter * MOUTH_GLOW_W_RATIO * smile_size))
    glow_h = max(2, int(face_diameter * MOUTH_GLOW_H_RATIO * smile_size))

    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(
        glow,
        (60, 175, 255, 35),
        (x - glow_w // 2, y - glow_h // 2, glow_w, glow_h),
    )
    surface.blit(glow, (0, 0))

    # Scale polygon points proportionally by face_diameter and smile_size
    points = [
        (
            int(x + px * face_diameter * smile_size),
            int(y + py * face_diameter * smile_size),
        )
        for px, py in MOUTH_POINTS_RATIOS
    ]

    pygame.draw.polygon(surface, WHITE, points)


def draw_face(current_time_ms):
    center = (WIDTH // 2, HEIGHT // 2)
    face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2

    # Background
    screen.fill(BACKGROUND)

    # Circular black face
    pygame.draw.circle(
        screen,
        BLACK,
        center,
        face_radius,
    )

    # Calculate proportional eye dimensions and blink scale
    eye_width = max(4, int(face_diameter * EYE_WIDTH_RATIO))
    base_eye_height = max(4, int(face_diameter * EYE_HEIGHT_RATIO))
    eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
    base_eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)

    blink_scale = get_blink_scale(current_time_ms)
    current_height = max(2, int(base_eye_height * blink_scale))

    # Keep bottom baseline anchored so eyelid closes from top downwards
    baseline = base_eye_y + base_eye_height // 2
    cur_eye_y = baseline - current_height // 2

    # Left Eye
    draw_glowing_eye(
        screen,
        (center[0] - eye_spacing, cur_eye_y),
        eye_width,
        current_height,
        face_diameter,
    )

    # Right Eye
    draw_glowing_eye(
        screen,
        (center[0] + eye_spacing, cur_eye_y),
        eye_width,
        current_height,
        face_diameter,
    )

    # Mouth
    mouth_center = (center[0], center[1] + int(face_diameter * MOUTH_Y_OFFSET_RATIO))
    draw_mouth(
        screen,
        mouth_center,
        face_diameter,
        smile_size=SMILE_SIZE,
    )

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
