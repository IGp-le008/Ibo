import pygame
import sys
import math

from .greetings import draw_glowing_eye as draw_greeting_eye


# -------------------------------------------------------------
# Initialize Pygame
# -------------------------------------------------------------
pygame.init()

WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Thinking Face")

BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)

clock = pygame.time.Clock()


# -------------------------------------------------------------
# Proportional Ratios
# Reference: face diameter = face_radius * 2
# -------------------------------------------------------------

FACE_RADIUS_RATIO = 0.36

# Eyes: match greetings.py
EYE_WIDTH_RATIO = 0.122
EYE_HEIGHT_RATIO = 0.130
EYE_SPACING_RATIO = 0.163
EYE_Y_OFFSET_RATIO = -0.076

# Eyebrows
EYEBROW_WIDTH_RATIO = 0.105
EYEBROW_HEIGHT_RATIO = 0.035
EYEBROW_Y_OFFSET_RATIO = -0.155
EYEBROW_STROKE_RATIO = 0.009

# Thinking mouth: intentionally not a smile
MOUTH_WIDTH_RATIO = 0.075
MOUTH_HEIGHT_RATIO = 0.012
MOUTH_Y_OFFSET_RATIO = 0.155
MOUTH_STROKE_RATIO = 0.008

# Hand placement and size
HAND_X_OFFSET_RATIO = -0.205
HAND_Y_OFFSET_RATIO = 0.245
HAND_WIDTH_RATIO = 0.205
HAND_HEIGHT_RATIO = 0.285
HAND_OUTLINE_RATIO = 0.006

# Animation
ANIMATION_PERIOD_MS = 1800
HAND_FLOAT_RATIO = 0.012
BROW_FLOAT_RATIO = 0.008
EYE_SHIFT_RATIO = 0.004


# -------------------------------------------------------------
# Animation Helpers
# -------------------------------------------------------------

def get_thinking_motion(elapsed_ms):
    """
    Return subtle animation offsets normalized to face diameter.

    The loop eases the hand slightly toward the chin and back,
    using a smoothed sine wave for more natural motion.
    """
    phase = (elapsed_ms % ANIMATION_PERIOD_MS) / ANIMATION_PERIOD_MS
    raw = math.sin(phase * 2 * math.pi)
    # Smooth the sine wave with power ease for gentler transitions
    wave = math.copysign(abs(raw) ** 0.7, raw)

    hand_y_offset = wave * HAND_FLOAT_RATIO
    brow_y_offset = wave * BROW_FLOAT_RATIO
    eye_x_offset = wave * EYE_SHIFT_RATIO

    return hand_y_offset, brow_y_offset, eye_x_offset


# -------------------------------------------------------------
# Draw Thinking Eyebrow
# -------------------------------------------------------------

def draw_thinking_eyebrow(
    surface,
    center,
    width,
    height,
    raised=False,
):
    """
    Draw a white eyebrow using normalized curve points.
    One eyebrow is arched; the other is more level.
    """
    x, y = center

    if raised:
            points_ratios = [
            (-0.50,  0.20),
            (-0.25, -0.15),
            ( 0.00, -0.60),
            ( 0.25, -0.30),
            ( 0.50,  0.05),
        ]
    else:
        points_ratios = [
            (-0.50,  0.12),
            (-0.25,  0.02),
            ( 0.00, -0.02),
            ( 0.25,  0.04),
            ( 0.50,  0.15),
        ]

    points = [
        (
            int(x + px * width),
            int(y + py * height),
        )
        for px, py in points_ratios
    ]

    stroke_width = max(2, int(width * EYEBROW_STROKE_RATIO))

    pygame.draw.lines(
        surface,
        WHITE,
        False,
        points,
        stroke_width,
    )


# -------------------------------------------------------------
# Draw Thinking Mouth
# -------------------------------------------------------------


def draw_thinking_mouth(surface, center, face_diameter):
    """
    Draw a small, subtly concerned mouth.
    The corners sit slightly higher than the center.
    """

    x, y = center

    mouth_width = max(
        4,
        int(face_diameter * MOUTH_WIDTH_RATIO),
    )

    mouth_height = max(
        2,
        int(face_diameter * 0.018),
    )

    stroke_width = max(
        2,
        int(face_diameter * MOUTH_STROKE_RATIO),
    )

    points_ratios = [
        (-0.50, -0.25),
        (-0.25,  0.15),
        ( 0.00,  0.45),
        ( 0.25,  0.15),
        ( 0.50, -0.25),
    ]

    points = [
        (
            int(x + px * mouth_width),
            int(y + py * mouth_height),
        )
        for px, py in points_ratios
    ]

    pygame.draw.lines(
        surface,
        WHITE,
        False,
        points,
        stroke_width,
    )


# -------------------------------------------------------------
# Draw Thinking Hand
# -------------------------------------------------------------


def draw_thinking_hand(
    surface,
    anchor,
    face_diameter,
):
    """
    Draw a white thinking hand on the left side of the face.
    Black creases define the index finger, thumb, and palm.
    """

    anchor_x, anchor_y = anchor

    hand_width = max(
        4,
        int(face_diameter * HAND_WIDTH_RATIO),
    )

    hand_height = max(
        4,
        int(face_diameter * HAND_HEIGHT_RATIO),
    )

    # Normalized hand silhouette.
    # The index finger points upward beside the cheek.
    hand_points_ratios = [
        ( 0.10,  0.50),
        ( 0.42,  0.42),
        ( 0.42,  0.12),
        ( 0.30, -0.28),
        ( 0.16, -0.42),
        ( 0.04, -0.36),
        ( 0.13, -0.02),
        (-0.02,  0.08),
        (-0.36,  0.02),
        (-0.48,  0.15),
        (-0.35,  0.30),
        (-0.08,  0.48),
    ]

    # Mirror the hand horizontally so it sits on the left.
    points = [
        (
            int(anchor_x - px * hand_width),
            int(anchor_y + py * hand_height),
        )
        for px, py in hand_points_ratios
    ]

    pygame.draw.polygon(
        surface,
        WHITE,
        points,
    )

    # Cyan outline
    outline_width = max(
        1,
        int(face_diameter * HAND_OUTLINE_RATIO),
    )

    pygame.draw.lines(
        surface,
        CYAN,
        True,
        points,
        outline_width,
    )

    # ---------------------------------------------------------
    # Black finger creases
    # ---------------------------------------------------------

    crease_width = max(
        1,
        int(face_diameter * 0.0045),
    )

    def hand_point(px, py):
        return (
            int(anchor_x - px * hand_width),
            int(anchor_y + py * hand_height),
        )

    # Index finger crease
    pygame.draw.lines(
        surface,
        BLACK,
        False,
        [
            hand_point(0.13, -0.02),
            hand_point(0.23, -0.01),
            hand_point(0.28, 0.08),
        ],
        crease_width,
    )

    # Thumb crease beneath the chin
    pygame.draw.lines(
        surface,
        BLACK,
        False,
        [
            hand_point(-0.05, 0.12),
            hand_point(-0.22, 0.18),
            hand_point(-0.31, 0.14),
        ],
        crease_width,
    )

    # Palm crease
    pygame.draw.lines(
        surface,
        BLACK,
        False,
        [
            hand_point(0.08, 0.25),
            hand_point(-0.02, 0.34),
            hand_point(-0.16, 0.37),
        ],
        crease_width,
    )



# -------------------------------------------------------------
# Draw Complete Thinking Face
# -------------------------------------------------------------

def draw_face(elapsed_ms):
    center = (WIDTH // 2, HEIGHT // 2)

    face_radius = int(
        min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO
    )
    face_diameter = face_radius * 2

    hand_motion, brow_motion, eye_motion = get_thinking_motion(
        elapsed_ms
    )

    screen.fill(BACKGROUND)

    pygame.draw.circle(
        screen,
        BLACK,
        center,
        face_radius,
    )

    # ---------------------------------------------------------
    # Eyes
    # ---------------------------------------------------------

    eye_width = max(
        4,
        int(face_diameter * EYE_WIDTH_RATIO),
    )

    eye_height = max(
        4,
        int(face_diameter * EYE_HEIGHT_RATIO),
    )

    eye_spacing = int(
        face_diameter * EYE_SPACING_RATIO
    )

    eye_y = center[1] + int(
        face_diameter * EYE_Y_OFFSET_RATIO
    )

    left_eye_center = (
        center[0] - eye_spacing + int(face_diameter * eye_motion),
        eye_y,
    )

    right_eye_center = (
        center[0] + eye_spacing + int(face_diameter * eye_motion),
        eye_y,
    )

    draw_greeting_eye(
        screen,
        left_eye_center,
        eye_width,
        eye_height,
        face_diameter,
    )

    draw_greeting_eye(
        screen,
        right_eye_center,
        eye_width,
        eye_height,
        face_diameter,
    )

    # ---------------------------------------------------------
    # Eyebrows
    # ---------------------------------------------------------

    eyebrow_width = int(
        face_diameter * EYEBROW_WIDTH_RATIO
    )

    eyebrow_height = int(
        face_diameter * EYEBROW_HEIGHT_RATIO
    )

    eyebrow_y_offset = int(
        face_diameter * EYEBROW_Y_OFFSET_RATIO
    )

    left_eyebrow_center = (
        left_eye_center[0],
        eye_y + eyebrow_y_offset + int(face_diameter * brow_motion),
    )

    right_eyebrow_center = (
        right_eye_center[0],
        eye_y + eyebrow_y_offset - int(face_diameter * brow_motion),
    )

    draw_thinking_eyebrow(
        screen,
        left_eyebrow_center,
        eyebrow_width,
        eyebrow_height,
        raised=False,
    )

    draw_thinking_eyebrow(
        screen,
        right_eyebrow_center,
        eyebrow_width,
        eyebrow_height,
        raised=True,
    )

    # ---------------------------------------------------------
    # Mouth: small, thoughtful, not smiling
    # ---------------------------------------------------------

    mouth_center = (
        center[0],
        center[1] + int(
            face_diameter * MOUTH_Y_OFFSET_RATIO
        ),
    )

    draw_thinking_mouth(
        screen,
        mouth_center,
        face_diameter,
    )

    # ---------------------------------------------------------
    # Hand: resting against the lower-right chin
    # ---------------------------------------------------------

    hand_anchor = (
        center[0] + int(
            face_diameter * HAND_X_OFFSET_RATIO
        ),
        center[1] + int(
            face_diameter * HAND_Y_OFFSET_RATIO
        ) + int(face_diameter * hand_motion),
    )

    draw_thinking_hand(
        screen,
        hand_anchor,
        face_diameter,
    )

    pygame.display.flip()


# -------------------------------------------------------------
# Main Loop
# -------------------------------------------------------------

def main():
    running = True
    start_time = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        elapsed_ms = pygame.time.get_ticks() - start_time

        draw_face(elapsed_ms)

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
