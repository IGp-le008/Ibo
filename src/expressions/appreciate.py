import pygame
import sys
import math

# Reuse mouth drawing from greetings
from .greetings import draw_mouth as draw_greeting_mouth

# Initialize Pygame
pygame.init()

# Window settings
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Appreciated Face (🤭)")

# Colors
BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)
GLOW_BLUE = (70, 180, 255)
BLUSH_PINK = (255, 130, 175)
BLUSH_GLOW = (255, 100, 150)

# Proportional Ratios (relative to face diameter = face_radius * 2)
FACE_RADIUS_RATIO = 0.36
EYE_WIDTH_RATIO = 0.125
EYE_HEIGHT_RATIO = 0.065
EYE_SPACING_RATIO = 0.165
EYE_Y_OFFSET_RATIO = -0.065

MOUTH_Y_OFFSET_RATIO = 0.155    # Vertical position of mouth relative to center
BLUSH_Y_OFFSET_RATIO = 0.08     # Vertical position of blush relative to center
SMILE_SIZE = 1.5                # Scale multiplier for the smile (1.0 = default baseline)

# Display Options
SHOW_MOUTH = True  # Set to True if a smiling mouth is desired; False keeps only eyes, face, and blush

clock = pygame.time.Clock()


def draw_happy_arch_eye(surface, center, width, height, bounce_y=0):
    """Draws a joyful closed arch eye `^ ^` with glowing cyan trail."""
    x, y = center
    y += bounce_y
    surf = pygame.Surface((width * 2, height * 4), pygame.SRCALPHA)
    cx, cy = width, height * 2

    # Upward curved arch `^`
    points = []
    steps = 16
    for i in range(steps + 1):
        t = i / steps
        px = cx - width // 2 + t * width
        # Inverted parabola for happy arch
        py = cy - height // 2 + (4 * (t - 0.5) ** 2) * height
        points.append((px, py))

    # Glow layer
    for r in range(10, 1, -2):
        alpha = max(8, 45 - r * 4)
        pygame.draw.lines(surf, (*GLOW_BLUE, alpha), False, points, width=max(3, r + 2))

    # Core arc
    pygame.draw.lines(surf, CYAN, False, points, width=max(4, int(width * 0.12)))
    pygame.draw.lines(surf, WHITE, False, points, width=max(2, int(width * 0.05)))

    surface.blit(surf, (x - cx, y - cy))


def draw_blush_cheeks(surface, center, face_diameter, pulse_alpha):
    """Draws rosy pink glowing blush spots on both cheeks."""
    cx, cy = center
    blush_spacing = int(face_diameter * 0.23)
    blush_y = cy + int(face_diameter * BLUSH_Y_OFFSET_RATIO)
    blush_r = int(face_diameter * 0.055)

    for sign in (-1, 1):
        bx = cx + sign * blush_spacing
        b_surf = pygame.Surface((blush_r * 4, blush_r * 4), pygame.SRCALPHA)
        ox, oy = blush_r * 2, blush_r * 2

        # Multi-layer soft radial blush
        for r in range(blush_r, 2, -2):
            factor = (1.0 - r / blush_r)
            alpha = int(pulse_alpha * factor * 0.45)
            pygame.draw.circle(b_surf, (*BLUSH_GLOW, alpha), (ox, oy), r)

        # Cheerful cute blush marks (3 diagonal pink stripes)
        stripe_alpha = int(pulse_alpha * 0.8)
        sw = max(2, int(face_diameter * 0.008))
        sh = int(face_diameter * 0.025)
        for offset_x in (-sw * 3, 0, sw * 3):
            s_pts = [(ox + offset_x - sw, oy - sh // 2), (ox + offset_x + sw, oy + sh // 2)]
            pygame.draw.line(b_surf, (*BLUSH_PINK, stripe_alpha), s_pts[0], s_pts[1], width=sw)

        surface.blit(b_surf, (bx - ox, blush_y - oy))


def draw_smiling_mouth(surface, center, face_diameter):
    # Placeholder: actual mouth drawing delegated to greetings.draw_mouth
    pass
    """Draws the shy, smiling mouth underneath the hand."""
    x, y = center
    mw = int(face_diameter * 0.11)
    mh = int(face_diameter * 0.05)

    glow = pygame.Surface((mw * 2, mh * 3), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*GLOW_BLUE, 40), (mw // 2, mh // 2, mw, mh))
    surface.blit(glow, (x - mw, y - mh))

    # Cute open half-smile
    pts = [
        (x - mw // 2, y),
        (x + mw // 2, y),
        (x + mw // 3, y + mh),
        (x, y + mh + 2),
        (x - mw // 3, y + mh),
    ]
    pygame.draw.polygon(surface, WHITE, pts)


def draw_face(current_time_ms):
    center = (WIDTH // 2, HEIGHT // 2)
    face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2

    # Background
    screen.fill(BACKGROUND)

    # Black face plate
    pygame.draw.circle(screen, BLACK, center, face_radius)

    # Giggle animation cycle (3.0 seconds loop)
    giggle_timeline = current_time_ms % 3000
    bounce_y = 0
    pulse_alpha = 180

    # During the first 1200 ms: cute 3-bounce giggle chuckle!
    if giggle_timeline < 1200:
        giggle_phase = giggle_timeline / 400.0  # 3 quick bounces
        bounce_y = -int(abs(math.sin(giggle_phase * math.pi)) * (face_diameter * 0.012))
        pulse_alpha = int(180 + 70 * abs(math.sin(giggle_phase * math.pi)))
    else:
        # Relaxed flattered hold
        hold_p = (giggle_timeline - 1200) / 1800.0
        bounce_y = int(math.sin(hold_p * math.pi) * 1.5)
        pulse_alpha = int(180 + 30 * math.sin(hold_p * math.pi))

    eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
    eye_w = int(face_diameter * EYE_WIDTH_RATIO)
    eye_h = int(face_diameter * EYE_HEIGHT_RATIO)
    eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)

    # 1. Joyful happy arch eyes `^ ^` with giggle bounce
    draw_happy_arch_eye(screen, (center[0] - eye_spacing, eye_y), eye_w, eye_h, bounce_y)
    draw_happy_arch_eye(screen, (center[0] + eye_spacing, eye_y), eye_w, eye_h, bounce_y)

    # 2. Glowing pink blush cheeks
    draw_blush_cheeks(screen, center, face_diameter, pulse_alpha)

    # 3. Optional smiling mouth (disabled by default to keep clean eyes, face, and blush)
    if SHOW_MOUTH:
        mouth_center = (center[0], center[1] + int(face_diameter * MOUTH_Y_OFFSET_RATIO))
        draw_greeting_mouth(screen, mouth_center, face_diameter, smile_size=SMILE_SIZE)

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
