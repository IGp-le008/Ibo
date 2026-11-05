"""
expressions/bored.py
State 1b: Bored / exhausted.
Flat-top, U-bottom eyes. Random looking and blinking continue from 1a.
Gaze source is passed in by the controller, so this file never imports idle_look.
"""

from expression_config import Blink, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, eye_positions, draw_face_plate,
    draw_glowing_eye, draw_mouth, blink_scale,
)


def draw_bored(surface, gaze, now_ms):
    """
    Draw one 1b frame. gaze must provide update(now_ms), gaze_offset(now_ms, d),
    and arm_target. The arm target is forced to "down" during bored (PDF).
    """
    gaze.update(now_ms)
    gaze.arm_target = "down"

    center, face_radius, face_diameter = face_geometry()
    eye_w, base_h, spacing, y_off = eye_metrics(face_diameter)

    draw_face_plate(surface, center, face_radius)

    gx, gy = gaze.gaze_offset(now_ms, face_diameter)
    scale = blink_scale(now_ms, Blink.INTERVAL_MS, Blink.DURATION_MS, Blink.MIN_OPEN_SCALE)
    eye_h = max(2, int(base_h * scale))

    left, right = eye_positions(center, spacing, y_off, base_h, eye_h, gx, gy)
    # flat_bottom=False gives the flat-top, U-bottom disappointed eye
    draw_glowing_eye(surface, left, eye_w, eye_h, face_diameter, flat_bottom=False)
    draw_glowing_eye(surface, right, eye_w, eye_h, face_diameter, flat_bottom=False)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)

