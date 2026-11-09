"""
expressions/idle_look.py
State 1a: Randomly looking.
Eyes look in random directions with periodic blinks.
Holds gaze state only. Arm target is a value; servo.py applies it.
"""

import random

from expressions.expression_config import Timing, Gaze, Blink, Mouth
from expressions.drawing import (
    face_geometry, eye_metrics, eye_positions, draw_face_plate,
    draw_glowing_eye, draw_mouth, ease_in_out, blink_scale,
)

# (x, y) direction vectors. Y is positive downward on screen.
LOOK_DIRECTIONS = {
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
    "up": (0.0, -1.0),
    "down": (0.0, 1.0),
    "center": (0.0, 0.0),
}


class GazeSource:
    """
    Random-look schedule. The controller creates one instance and passes
    it to idle_look, bored, and any other expression that wanders.
    Other expressions use it by duck typing, so they never import this file.
    """

    def __init__(self):
        self.direction = "center"
        self.prev_direction = "center"
        self.hold_until_ms = 0
        self.transition_start_ms = 0
        self.arm_target = "down"    # "down" or "random"; servo.py applies it

    def update(self, now_ms):
        if now_ms >= self.hold_until_ms:
            self.prev_direction = self.direction
            choices = [d for d in LOOK_DIRECTIONS if d != self.direction]
            self.direction = random.choice(choices)
            hold = random.randint(Timing.LOOK_HOLD_MIN_MS, Timing.LOOK_HOLD_MAX_MS)
            self.hold_until_ms = now_ms + hold
            self.transition_start_ms = now_ms
            # PDF: look-down lifts the arm at a random position
            self.arm_target = "random" if self.direction == "down" else "down"

    def gaze_offset(self, now_ms, face_diameter):
        """Return (dx, dy) in pixels, eased from the previous direction."""
        p = ease_in_out((now_ms - self.transition_start_ms) / Gaze.EASE_MS)
        prev = LOOK_DIRECTIONS[self.prev_direction]
        cur = LOOK_DIRECTIONS[self.direction]
        ux = prev[0] + (cur[0] - prev[0]) * p
        uy = prev[1] + (cur[1] - prev[1]) * p
        return (int(ux * Gaze.MAX_X_RATIO * face_diameter),
                int(uy * Gaze.MAX_Y_RATIO * face_diameter))


def draw_idle_look(surface, gaze, now_ms):
    """Draw one 1a frame. Caller owns flip()."""
    gaze.update(now_ms)
    center, face_radius, face_diameter = face_geometry()
    eye_w, base_h, spacing, y_off = eye_metrics(face_diameter)

    draw_face_plate(surface, center, face_radius)

    gx, gy = gaze.gaze_offset(now_ms, face_diameter)
    scale = blink_scale(now_ms, Blink.INTERVAL_MS, Blink.DURATION_MS, Blink.MIN_OPEN_SCALE)
    eye_h = max(2, int(base_h * scale))

    left, right = eye_positions(center, spacing, y_off, base_h, eye_h, gx, gy)
    draw_glowing_eye(surface, left, eye_w, eye_h, face_diameter, flat_bottom=True)
    draw_glowing_eye(surface, right, eye_w, eye_h, face_diameter, flat_bottom=True)

    mouth_center = (center[0], center[1] + int(face_diameter * Mouth.Y_OFFSET_RATIO))
    draw_mouth(surface, mouth_center, face_diameter)