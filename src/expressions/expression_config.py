"""
config.py
Central tuning values for the CUDO / Collexa face.
Expressions import from here. Expressions never import other expressions.
All ratios are relative to face_diameter (= face_radius * 2) unless noted.
"""


class Window:
    WIDTH = 640
    HEIGHT = 640
    BACKGROUND = (20, 25, 32)
    FACE_RADIUS_RATIO = 0.36          # relative to min(WIDTH, HEIGHT)
    FPS = 30


class Colors:
    BLACK = (0, 0, 0)
    CYAN = (185, 235, 255)
    WHITE = (240, 250, 255)
    GLOW_BLUE = (70, 180, 255)
    BLUSH_PINK = (255, 130, 175)
    BLUSH_GLOW = (255, 100, 150)


class Eye:
    WIDTH_RATIO = 0.122
    HEIGHT_RATIO = 0.130
    SPACING_RATIO = 0.163
    Y_OFFSET_RATIO = -0.076
    GLOW_RATIO = 0.039
    CORE_INSET_RATIO = 0.009
    ARCH_HEIGHT_RATIO = 0.065   # happy arch eye height, from appreciate.py
    ARCH_Y_OFFSET_RATIO = -0.065


class Gaze:
    # Horizontal shift for left/right, vertical shift for up/down
    MAX_X_RATIO = 0.035
    MAX_Y_RATIO = 0.025
    # Tracking dead zone (normalized frame x, 0..1)
    LEFT_THRESHOLD = 0.40
    RIGHT_THRESHOLD = 0.60
    EASE_MS = 400


class Mouth:
    Y_OFFSET_RATIO = 0.140
    GLOW_W_RATIO = 0.152
    GLOW_H_RATIO = 0.083
    SMILE_SIZE = 1.65
    # Normalized smile polygon, relative to face_diameter, anchor = mouth center
    POINTS_RATIOS = [
        (-0.0587, -0.0174),
        ( 0.0587, -0.0174),
        ( 0.0522,  0.0022),
        ( 0.0370,  0.0196),
        ( 0.0174,  0.0283),
        ( 0.0000,  0.0304),
        (-0.0174,  0.0283),
        (-0.0370,  0.0196),
        (-0.0522,  0.0022),
    ]


class Blink:
    INTERVAL_MS = 5000        #5 s, change here later if needed
    DURATION_MS = 240
    MIN_OPEN_SCALE = 0.08


class Timing:
    LOOK_HOLD_MIN_MS = 2000                 # random look hold, 2–4 s
    LOOK_HOLD_MAX_MS = 4000
    SLEEP_Z_CYCLE_MS = 2500     # one drifting Z completes its rise in this time
    GRATEFUL_MS = 2500          # one grateful reaction, then return to previous state



class Expression:
    """Stored-state names shared by controller and expressions."""
    IDLE_LOOK = "idle_look"
    BORED = "bored"
    SLEEP = "sleep"
    LISTENING = "listening"
    TRACKING = "tracking"
    GRATEFUL = "grateful"
    ACTIVE = "active"
