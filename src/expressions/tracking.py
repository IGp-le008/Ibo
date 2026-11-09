"""
expressions/tracking.py
State 3: Tracking.
Eyes follow the largest detected face. Only drawn while a face is visible.
target_x, target_y: normalized 0..1 from face_worker, or None when no face.
Dead zone: left of LEFT_THRESHOLD looks left, right of RIGHT_THRESHOLD looks right,
between them looks centre. Arm target is "down".
"""

from expressions.expression_config import Blink, Gaze, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, eye_positions, draw_face_plate,
    draw_glowing_eye, draw_mouth, blink_scale,
)


def tracking_gaze(target_x, face_diameter):
    """
    Horizontal dead-zone mapping for tracking. Returns (dx, dy) in pixels.
    Vertical gaze stays centered: the PDF only specifies left, right, and centre.
    """
    if target_x is None:
        return 0, 0
    if target_x < Gaze.LEFT_THRESHOLD:
        dx = -Gaze.MAX_X_RATIO
    elif target_x > Gaze.RIGHT_THRESHOLD:
        dx = Gaze.MAX_X_RATIO
    else:
        dx = 0.0
    return int(dx * face_diameter), 0


def draw_tracking(surface, now_ms, target_x=None):
    """Draw one State 3 frame. Caller owns flip()."""
    center, face_radius, face_diameter = face_geometry()
    eye_w, base_h, spacing, y_off = eye_metrics(face_diameter)

    draw_face_plate(surface, center, face_radius)

    gx, gy = tracking_gaze(target_x, face_diameter)
    scale = blink_scale(now_ms, Blink.INTERVAL_MS, Blink.DURATION_MS, Blink.MIN_OPEN_SCALE)
    eye_h = max(2, int(base_h * scale))

    left, right = eye_positions(center, spacing, y_off, base_h, eye_h, gx, gy)
    draw_glowing_eye(surface, left, eye_w, eye_h, face_diameter, flat_bottom=True)
    draw_glowing_eye(surface, right, eye_w, eye_h, face_diameter, flat_bottom=True)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)