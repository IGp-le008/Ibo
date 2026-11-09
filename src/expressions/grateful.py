"""
expressions/grateful.py
Grateful reaction: happy arch eyes ^ ^ with pink blush, mouth kept.
Triggered by a transcript match (Audio.GRATEFUL_WORDS). Plays once, then
the controller returns to the previous state after Timing.GRATEFUL_MS.
Arm target is "down". Eyes do not track or wander.
"""

import math

import pygame

from expressions.expression_config import Colors, Eye, Timing, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, draw_face_plate, draw_mouth,
)

BLUSH_Y_OFFSET_RATIO = 0.08
BLUSH_SPACING_RATIO = 0.23
BLUSH_RADIUS_RATIO = 0.055
ARCH_STEPS = 16


def draw_arch_eye(surface, center, width, height, bounce_y=0):
    """Happy upward arch ^ with a soft cyan glow, as in appreciate.py."""
    x, y = center
    y += bounce_y
    surf = pygame.Surface((width * 2, height * 4), pygame.SRCALPHA)
    cx, cy = width, height * 2

    points = []
    for i in range(ARCH_STEPS + 1):
        t = i / ARCH_STEPS
        px = cx - width // 2 + t * width
        py = cy - height // 2 + (4 * (t - 0.5) ** 2) * height
        points.append((px, py))

    for r in range(10, 1, -2):
        alpha = max(8, 45 - r * 4)
        pygame.draw.lines(surf, (*Colors.GLOW_BLUE, alpha), False, points, width=max(3, r + 2))
    pygame.draw.lines(surf, Colors.CYAN, False, points, width=max(4, int(width * 0.12)))
    pygame.draw.lines(surf, Colors.WHITE, False, points, width=max(2, int(width * 0.05)))

    surface.blit(surf, (x - cx, y - cy))


def draw_blush(surface, center, face_diameter, pulse_alpha):
    """Pink glowing blush on both cheeks with three small stripes each."""
    cx, cy = center
    spacing = int(face_diameter * BLUSH_SPACING_RATIO)
    blush_y = cy + int(face_diameter * BLUSH_Y_OFFSET_RATIO)
    blush_r = max(3, int(face_diameter * BLUSH_RADIUS_RATIO))

    for sign in (-1, 1):
        bx = cx + sign * spacing
        b_surf = pygame.Surface((blush_r * 4, blush_r * 4), pygame.SRCALPHA)
        ox, oy = blush_r * 2, blush_r * 2
        for r in range(blush_r, 2, -2):
            factor = 1.0 - r / blush_r
            alpha = int(pulse_alpha * factor * 0.45)
            pygame.draw.circle(b_surf, (*Colors.BLUSH_GLOW, alpha), (ox, oy), r)

        stripe_alpha = int(pulse_alpha * 0.8)
        sw = max(2, int(face_diameter * 0.008))
        sh = int(face_diameter * 0.025)
        for offset_x in (-sw * 3, 0, sw * 3):
            p1 = (ox + offset_x - sw, oy - sh // 2)
            p2 = (ox + offset_x + sw, oy + sh // 2)
            pygame.draw.line(b_surf, (*Colors.BLUSH_PINK, stripe_alpha), p1, p2, width=sw)

        surface.blit(b_surf, (bx - ox, blush_y - oy))


def grateful_pulse(elapsed_ms):
    """
    Return (bounce_y, pulse_alpha) for a short giggle at the start,
    then a relaxed hold. elapsed_ms is time since the reaction started.
    """
    _, _, face_diameter = face_geometry()
    if elapsed_ms < 1200:
        phase = elapsed_ms / 400.0
        wobble = abs(math.sin(phase * math.pi))
        bounce_y = -int(wobble * (face_diameter * 0.012))
        pulse_alpha = int(180 + 70 * wobble)
    else:
        hold = (elapsed_ms - 1200) / 1800.0
        bounce_y = int(math.sin(hold * math.pi) * 1.5)
        pulse_alpha = int(180 + 30 * math.sin(hold * math.pi))
    return bounce_y, pulse_alpha


def draw_grateful(surface, elapsed_ms):
    """
    Draw one grateful frame. elapsed_ms is time since the reaction began.
    The controller calls this until elapsed_ms >= Timing.GRATEFUL_MS.
    Caller owns flip().
    """
    center, face_radius, face_diameter = face_geometry()
    eye_w, _, spacing, y_off = eye_metrics(face_diameter)
    eye_h = max(3, int(face_diameter * Eye.ARCH_HEIGHT_RATIO))
    eye_y = center[1] + int(face_diameter * Eye.ARCH_Y_OFFSET_RATIO)

    draw_face_plate(surface, center, face_radius)

    bounce_y, pulse_alpha = grateful_pulse(elapsed_ms)
    draw_arch_eye(surface, (center[0] - spacing, eye_y), eye_w, eye_h, bounce_y)
    draw_arch_eye(surface, (center[0] + spacing, eye_y), eye_w, eye_h, bounce_y)

    draw_blush(surface, center, face_diameter, pulse_alpha)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)