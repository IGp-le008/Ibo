"""
expressions/listening.py
State 2: Listening.
Eyes turn toward the speaking person's face center.
target_x, target_y: normalized 0..1 frame position from face_worker (or None).
If no target is known, the eyes stay centered.
Arm target is "down" (PDF).
"""

from expression_config import Blink, Gaze, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, eye_positions, draw_face_plate,
    draw_glowing_eye, draw_mouth, blink_scale,
)


def target_to_gaze(target_x, target_y, face_diameter):
    """
    Map a normalized frame position to a pixel gaze offset.
    Frame center (0.5, 0.5) maps to (0, 0). The result is clamped to the
    configured maximum, so the eyes never leave the face plate.
    """
    if target_x is None or target_y is None:
        return 0, 0
    ux = max(-1.0, min(1.0, (target_x - 0.5) * 2.0))
    uy = max(-1.0, min(1.0, (target_y - 0.5) * 2.0))
    return (int(ux * Gaze.MAX_X_RATIO * face_diameter),
            int(uy * Gaze.MAX_Y_RATIO * face_diameter))


def draw_listening(surface, now_ms, target_x=None, target_y=None):
    """Draw one State 2 frame. Caller owns flip()."""
    center, face_radius, face_diameter = face_geometry()
    eye_w, base_h, spacing, y_off = eye_metrics(face_diameter)

    draw_face_plate(surface, center, face_radius)

    gx, gy = target_to_gaze(target_x, target_y, face_diameter)
    scale = blink_scale(now_ms, Blink.INTERVAL_MS, Blink.DURATION_MS, Blink.MIN_OPEN_SCALE)
    eye_h = max(2, int(base_h * scale))

    left, right = eye_positions(center, spacing, y_off, base_h, eye_h, gx, gy)
    draw_glowing_eye(surface, left, eye_w, eye_h, face_diameter, flat_bottom=True)
    draw_glowing_eye(surface, right, eye_w, eye_h, face_diameter, flat_bottom=True)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)