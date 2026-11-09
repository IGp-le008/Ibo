"""
servo.py
Arm servo control for the Raspberry Pi 3B+ (two 180° 9g servos on hardware PWM).
Convention: 0° = down, 90° = centre, 180° = up.
Targets are named: "down", "center", "up", or "random".
On a laptop (no RPi.GPIO), a stub is used that only logs angles.
Power: servos use an external 5 V supply, not the Pi's 5 V pin.
"""

import random
import time

from control.control_config import Servo

try:
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    GPIO = None
    ON_PI = False


TARGET_ANGLES = {
    "down": Servo.DOWN_DEG,
    "center": Servo.CENTER_DEG,
    "up": Servo.UP_DEG,
}


def angle_to_duty(angle_deg):
    """Convert an angle (0..180) to a PWM duty cycle percent for 50 Hz."""
    pulse_ms = Servo.MIN_PULSE_MS + (angle_deg / 180.0) * (Servo.MAX_PULSE_MS - Servo.MIN_PULSE_MS)
    period_ms = 1000.0 / Servo.PWM_HZ
    return pulse_ms / period_ms * 100.0


class ArmServo:
    """One servo on one BCM pin. Moves are eased by stepping over Servo.MOVE_MS."""

    def __init__(self, pin_bcm, name):
        self.name = name
        self.pin = pin_bcm
        self.current_deg = Servo.CENTER_DEG
        self.pwm = None
        if ON_PI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin_bcm, GPIO.OUT)
            self.pwm = GPIO.PWM(pin_bcm, Servo.PWM_HZ)
            self.pwm.start(angle_to_duty(self.current_deg))

    def set_angle(self, angle_deg):
        """Move to angle_deg, clamped to 0..180. Blocking eased move."""
        angle_deg = max(0.0, min(180.0, angle_deg))
        start = self.current_deg
        steps = max(1, Servo.MOVE_MS // 20)
        for i in range(1, steps + 1):
            t = i / steps
            eased = 0.5 * (1.0 - __import__("math").cos(t * 3.141592653589793))
            a = start + (angle_deg - start) * eased
            if ON_PI and self.pwm is not None:
                self.pwm.ChangeDutyCycle(angle_to_duty(a))
            time.sleep(Servo.MOVE_MS / steps / 1000.0)
        self.current_deg = angle_deg
        if not ON_PI:
            print(f"[servo {self.name}] -> {angle_deg:.1f} deg (stub)")

    def close(self):
        if self.pwm is not None:
            self.pwm.stop()
        if ON_PI:
            GPIO.cleanup(self.pin)


class ArmController:
    """
    Both arms. The controller calls apply(target) with one of:
    "down", "center", "up", or "random". Random picks a new angle each call
    within Servo.RANDOM_MIN_DEG..RANDOM_MAX_DEG, as the PDF specifies for look-down.
    """

    def __init__(self):
        self.left = ArmServo(Servo.LEFT_PIN_BCM, "left")
        self.right = ArmServo(Servo.RIGHT_PIN_BCM, "right")
        self.last_target = None

    def apply(self, target):
        if target == self.last_target:
            return
        self.last_target = target
        if target == "random":
            a = random.uniform(Servo.RANDOM_MIN_DEG, Servo.RANDOM_MAX_DEG)
        else:
            a = TARGET_ANGLES[target]
        self.left.set_angle(a)
        self.right.set_angle(a)

    def close(self):
        self.left.close()
        self.right.close()