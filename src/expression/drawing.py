"""
expressions/drawing.py
Shared drawing primitives for all CUDO face expressions.
Imports only config.py. No expression file is imported here.
Every function draws onto a supplied surface and does not call flip().
"""

import math
import pygame

from expression_config import Window, Colors, Eye, Mouth

def eye_positions(center, spacing, y_offset, base_h, eye_h, gx, gy):
    """
    Return (left, right) eye centers. The bottom edge stays anchored to
    the base baseline so a blink closes the eye from the top down.
    gx, gy: gaze offset in pixels.
    """
    baseline = center[1] + y_offset + base_h // 2
    eye_y = baseline - eye_h // 2 + gy
    left = (center[0] - spacing + gx, eye_y)
    right = (center[0] + spacing + gx, eye_y)
    return left, right

def face_geometry():
    """
    Return the reference geometry for the face.
    center: pixel center of the face
    face_radius, face_diameter: pixels
    """
    center = (Window.WIDTH // 2, Window.HEIGHT // 2)
    face_radius = int(min(Window.WIDTH, Window.HEIGHT) * Window.FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2
    return center, face_radius, face_diameter


def eye_metrics(face_diameter):
    """Return eye width, base height, spacing, and y-offset in pixels."""
    eye_width = max(4, int(face_diameter * Eye.WIDTH_RATIO))
    base_eye_height = max(4, int(face_diameter * Eye.HEIGHT_RATIO))
    eye_spacing = int(face_diameter * Eye.SPACING_RATIO)
    eye_y_offset = int(face_diameter * Eye.Y_OFFSET_RATIO)
    return eye_width, base_eye_height, eye_spacing, eye_y_offset


def draw_face_plate(surface, center, face_radius):
    """Fill the background and draw the black circular face plate."""
    surface.fill(Window.BACKGROUND)
    pygame.draw.circle(surface, Colors.BLACK, center, face_radius)


def draw_glowing_eye(surface, center, width, height, face_diameter, flat_bottom=True):
    """
    Draw one cyan eye.
    flat_bottom=True : rounded top, flat bottom (normal eye).
    flat_bottom=False: flat top, rounded/U bottom (bored eye).
    center: pixel center of the eye. height is clamped to at least 2 px.
    """
    x, y = center
    height = max(2, height)

    # Soft outer glow sized to the eye's bounding box
    glow_radius_max = max(3, int(face_diameter * Eye.GLOW_RATIO))
    glow_step = max(1, glow_radius_max // 6)
    glow_size = (width + glow_radius_max * 2 + 4, height + glow_radius_max * 2 + 4)
    glow = pygame.Surface(glow_size, pygame.SRCALPHA)
    gcx, gcy = glow_size[0] // 2, glow_size[1] // 2
    for radius in range(glow_radius_max, 1, -glow_step):
        alpha = max(4, int(20 * (1.0 - radius / glow_radius_max)))
        pygame.draw.ellipse(
            glow,
            (*Colors.GLOW_BLUE, alpha),
            (gcx - width // 2 - radius, gcy - height // 2 - radius,
             width + radius * 2, height + radius * 2),
        )
    surface.blit(glow, (x - gcx, y - gcy))

    eye_rect = pygame.Rect(x - width // 2, y - height // 2, width, height)

    # Outer cyan shell: rounded top
    pygame.draw.ellipse(surface, Colors.CYAN, eye_rect)
    if flat_bottom:
        # Cut the lower half flat: fill the bottom half with a rectangle
        pygame.draw.rect(surface, Colors.CYAN,
                         (eye_rect.left, eye_rect.centery, width, max(1, height // 2)))
    else:
        # Flat top: cover the upper half with background, then re-draw a flat lid line
        pygame.draw.rect(surface, Colors.BLACK,
                         (eye_rect.left - 4, eye_rect.top - 4, width + 8, height // 2 + 4))
        pygame.draw.line(surface, Colors.CYAN,
                         (eye_rect.left, eye_rect.centery),
                         (eye_rect.right, eye_rect.centery), 3)

    # Inner white core
    core_inset = max(1, int(face_diameter * Eye.CORE_INSET_RATIO))
    if height > core_inset * 3:
        core_rect = pygame.Rect(
            eye_rect.left + core_inset,
            eye_rect.top + core_inset,
            max(2, width - core_inset * 2),
            max(2, height - core_inset * 2),
        )
        pygame.draw.ellipse(surface, Colors.WHITE, core_rect)
        if flat_bottom:
            pygame.draw.rect(surface, Colors.WHITE,
                             (core_rect.left, core_rect.top + core_rect.height // 2,
                              core_rect.width, max(1, core_rect.height // 2)))
    else:
        # Closed during a blink: thin illuminated slit
        slit_h = max(1, core_inset)
        pygame.draw.rect(surface, Colors.WHITE,
                         (eye_rect.left + core_inset, y - slit_h // 2,
                          max(1, width - core_inset * 2), slit_h))


def draw_mouth(surface, center, face_diameter, smile_size=None):
    """
    Draw the smile polygon with its soft glow.
    center: pixel anchor (mouth center). Points are normalized to face_diameter.
    """
    if smile_size is None:
        smile_size = Mouth.SMILE_SIZE
    x, y = center

    glow_w = max(4, int(face_diameter * Mouth.GLOW_W_RATIO * smile_size))
    glow_h = max(2, int(face_diameter * Mouth.GLOW_H_RATIO * smile_size))
    glow_size = (glow_w + 8, glow_h + 8)
    glow = pygame.Surface(glow_size, pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (60, 175, 255, 35), (4, 4, glow_w, glow_h))
    surface.blit(glow, (x - glow_size[0] // 2, y - glow_size[1] // 2))

    points = [
        (int(x + px * face_diameter * smile_size),
         int(y + py * face_diameter * smile_size))
        for px, py in Mouth.POINTS_RATIOS
    ]
    pygame.draw.polygon(surface, Colors.WHITE, points)


def ease_in_out(p):
    """Cosine ease-in-out for p in 0..1."""
    p = max(0.0, min(1.0, p))
    return 0.5 * (1.0 - math.cos(p * math.pi))


def blink_scale(elapsed_ms, interval_ms, duration_ms, min_open_scale):
    """
    Return eye openness 1.0 (open) to min_open_scale (closed) for a blink
    that fires every interval_ms and lasts duration_ms.
    """
    cycle = elapsed_ms % interval_ms
    if cycle < duration_ms:
        progress = cycle / duration_ms
        closing = math.sin(progress * math.pi)
        return 1.0 - (1.0 - min_open_scale) * closing
    return 1.0