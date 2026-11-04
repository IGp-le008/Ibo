"""
expressions/sleep.py
State 1c: Sleep.
Closed u-u eyes, a small smile, and drifting Z letters.
No gaze and no nose bubble. Arm target is down (PDF).
"""

import math

import pygame

from expression_config import Colors, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, draw_face_plate, draw_mouth,
)
from expression_config import Timing

GLOW_EYE_STEPS = 16
Z_PARTICLES = 3
Z_RISE_RATIO = 0.35          # how far a Z rises, relative to face_diameter
Z_SWAY_RATIO = 0.04
Z_BASE_SIZE_RATIO = 0.055
Z_ORIGIN_X_RATIO = 0.12      # anchor offset from face center
Z_ORIGIN_Y_RATIO = -0.08
SLEEP_EYE_HEIGHT_RATIO = 0.055  # flattened arc height, same as ideal.py


def draw_sleep_eye(surface, center, width, height, face_diameter):
    """Draw one downward-curving closed eye, the 'u' shape."""
    x, y = center
    surf = pygame.Surface((width * 2, height * 4), pygame.SRCALPHA)
    cx, cy = width, height * 2

    points = []
    for i in range(GLOW_EYE_STEPS + 1):
        t = i / GLOW_EYE_STEPS
        px = cx - width // 2 + t * width
        py = cy + height // 2 - (4 * (t - 0.5) ** 2) * height
        points.append((px, py))

    for r in range(8, 1, -2):
        alpha = max(10, 50 - r * 5)
        pygame.draw.lines(surf, (*Colors.GLOW_BLUE, alpha), False, points, width=max(3, r + 2))
    pygame.draw.lines(surf, Colors.CYAN, False, points, width=max(3, int(width * 0.08)))
    pygame.draw.lines(surf, Colors.WHITE, False, points, width=max(1, int(width * 0.04)))

    surface.blit(surf, (x - cx, y - cy))


def draw_glowing_z(surface, center, size, alpha):
    """Draw one stylized Z with soft glow. alpha is 0..255."""
    if alpha <= 0 or size <= 2:
        return
    x, y = center
    z_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    ox, oy = size, size
    pts = [
        (ox - size // 2, oy - size // 2),
        (ox + size // 2, oy - size // 2),
        (ox - size // 2, oy + size // 2),
        (ox + size // 2, oy + size // 2),
    ]
    pygame.draw.lines(z_surf, (*Colors.GLOW_BLUE, int(alpha * 0.45)), False, pts, width=max(3, size // 3))
    pygame.draw.lines(z_surf, (*Colors.WHITE, int(alpha)), False, pts, width=max(2, size // 6))
    surface.blit(z_surf, (x - ox, y - oy))


def draw_drifting_zs(surface, origin, face_diameter, now_ms):
    """Three staggered Zs that rise, sway, and fade in and out."""
    sx, sy = origin
    base_size = int(face_diameter * Z_BASE_SIZE_RATIO)
    for i in range(Z_PARTICLES):
        p_t = ((now_ms / Timing.SLEEP_Z_CYCLE_MS) + i * 0.33) % 1.0
        rise = p_t * (face_diameter * Z_RISE_RATIO)
        sway = math.sin(p_t * math.pi * 3 + i) * (face_diameter * Z_SWAY_RATIO)
        zx = sx + int(rise * 0.5 + sway)
        zy = sy - int(rise)
        size = int(base_size * (0.8 + 0.4 * i))
        if p_t < 0.2:
            alpha = int(255 * (p_t / 0.2))
        elif p_t > 0.8:
            alpha = int(255 * ((1.0 - p_t) / 0.2))
        else:
            alpha = 255
        draw_glowing_z(surface, (zx, zy), size, alpha)


def draw_sleep(surface, now_ms):
    """Draw one 1c frame. Caller owns flip()."""
    center, face_radius, face_diameter = face_geometry()
    eye_w, base_h, spacing, y_off = eye_metrics(face_diameter)

    draw_face_plate(surface, center, face_radius)

    eye_h = max(3, int(face_diameter * SLEEP_EYE_HEIGHT_RATIO))
    eye_y = center[1] + y_off
    draw_sleep_eye(surface, (center[0] - spacing, eye_y), eye_w, eye_h, face_diameter)
    draw_sleep_eye(surface, (center[0] + spacing, eye_y), eye_w, eye_h, face_diameter)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)

    origin = (center[0] + int(face_diameter * Z_ORIGIN_X_RATIO),
              center[1] + int(face_diameter * Z_ORIGIN_Y_RATIO))
    draw_drifting_zs(surface, origin, face_diameter, now_ms)