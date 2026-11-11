from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

WHISPER_MODEL_PATH = str(PROJECT_ROOT / "whisper.cpp/models/ggml-tiny.bin")


#Different states of the bot
class State:
    IDLE_LOOK = "idle_look"
    BORED = "bored"
    SLEEP = "sleep"
    LISTENING = "listening"
    TRACKING = "tracking"
    GRATEFUL = "grateful"
    ACTIVE = "active"
    

class Chat:
    WIDTH = 640
    HEIGHT = 640
    FPS = 30
    FONT_PATH = None          # Path to a TTF. None = pygame default, which has no Devanagari.
    FONT_SIZE = 20
    PAD = 16
    LINE_GAP = 6
    BACKGROUND = (20, 25, 32)
    USER_COLOR = (150, 200, 255)
    ASSISTANT_COLOR = (240, 250, 255)
    SOURCE_COLOR = (140, 140, 160)
    ERROR_COLOR = (255, 120, 120)
    USER_LABEL = "You:"
    ASSISTANT_LABEL = "Collexa:"


class Servo:
    LEFT_PIN_BCM = 12                       # hardware PWM
    RIGHT_PIN_BCM = 13                      # hardware PWM
    PWM_HZ = 50
    # Angle convention: 0 = down, 90 = centre, 180 = up
    DOWN_DEG = 0
    CENTER_DEG = 90
    UP_DEG = 180
    MIN_PULSE_MS = 0.5                      # typical 9g servo, tune if jittery
    MAX_PULSE_MS = 2.5
    RANDOM_MIN_DEG = 60         # random arm position range for look-down (PDF)
    RANDOM_MAX_DEG = 150
    MOVE_MS = 400               # time to move between angles, eased



class Camera:
    DEVICE_INDEX = 0
    FRAME_W = 640
    FRAME_H = 640
    SEND_INTERVAL_MS = 33        # about 30 updates per second to the controller
    PERSON_LOST_GRACE_MS = 500   # keep the last target this long before sending None




class Audio:
    SAMPLE_RATE = 16000
    CHUNK_MS = 80                           # openWakeWord frame size
    WHISPER_MODEL_PATH = str(PROJECT_ROOT / "whisper.cpp/models/ggml-tiny.bin")   # whisper.cpp tiny, quantized
    WHISPER_LANGUAGES = ("en", "ne", "hi")
    WAKE_MODEL_PATH = None                  # hook: path to your custom openWakeWord model
    WAKE_THRESHOLD = 0.5
    # Wake words for transcript matching and grateful trigger
    WAKE_WORDS = [
        "hello allexa", "allexa", "hi", "hello", "excuse me", "wakeup",
        "wake up", "k xa", "sunata", "oi", "oih",
    ]
    GRATEFUL_WORDS = [
        "thank you", "thanks", "welcome", "great", "nice", "wow",
        "cute", "pretty",
    ]
    WHISPER_CLI = str(PROJECT_ROOT / "whisper.cpp/build/bin/whisper-cli")              # whisper.cpp binary, must be on PATH or give full path
    SILENCE_RMS = 500                    # int16 RMS below this counts as silence
    SILENCE_END_MS = 800                 # silence this long ends the utterance
    MAX_UTTERANCE_MS = 10000             # hard cap on one utterance
    WAKE_COOLDOWN_MS = 1500              # ignore wake detections right after one fires
    TMP_WAV_PATH = "/tmp/collexa_utt.wav"
    INPUT_DEVICE = 2

#Timing preset of dirrent states
class Timing:
    IDLE_BEFORE_RANDOM_MS = 2 * 60 * 1000
    RANDOM_LOOK_MS = 2 * 60 * 1000
    BORED_MS = 2 * 60 * 1000
    SLEEP_MS = 5 * 1000          # owner: 5 s for now
    TRACK_TO_ACTIVE_MS = 15 * 1000
    LOOP_LIMIT = 3
    GRATEFUL_MS = 2500