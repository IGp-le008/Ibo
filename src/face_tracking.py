import cv2
import os
import sys
import time
from typing import Optional, Tuple, Dict, Any

# Window dimensions
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 640
WINDOW_NAME = "Collexa - Face Tracking (640x640)"

# Model paths (in app/models/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MEDIAPIPE_MODEL = os.path.join(MODELS_DIR, "blaze_face_short_range.tflite")
HAAR_CASCADE_PATH = os.path.join(MODELS_DIR, "haarcascade_frontalface_default.xml")


class FaceTracker:
    """Detects and tracks human faces using MediaPipe or OpenCV Haar Cascades."""

    def __init__(self, prefer_mediapipe: bool = True):
        self.use_mediapipe = False
        self.detector = None
        self.cascade = None

        # 1. Try MediaPipe FaceDetector
        if prefer_mediapipe and os.path.exists(MEDIAPIPE_MODEL):
            try:
                import mediapipe as mp
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision

                self.mp = mp
                base_options = python.BaseOptions(model_asset_path=MEDIAPIPE_MODEL)
                options = vision.FaceDetectorOptions(
                    base_options=base_options,
                    min_detection_confidence=0.5,
                )
                self.detector = vision.FaceDetector.create_from_options(options)
                self.use_mediapipe = True
                print(f"[FaceTracker] Initialized with MediaPipe Vision ({MEDIAPIPE_MODEL})")
            except Exception as e:
                print(f"[FaceTracker] MediaPipe init failed ({e}), falling back to Haar Cascade.")

        # 2. Fallback to OpenCV Haar Cascade
        if not self.use_mediapipe:
            if os.path.exists(HAAR_CASCADE_PATH):
                self.cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
                print(f"[FaceTracker] Initialized with OpenCV Haar Cascade ({HAAR_CASCADE_PATH})")
            else:
                print(f"[FaceTracker] Warning: Haar cascade model not found at {HAAR_CASCADE_PATH}")

    def detect(self, frame_bgr) -> Optional[Dict[str, Any]]:
        """
        Detects the primary (largest) face in a frame.

        Returns:
            dict with:
                - 'box': (x, y, w, h)
                - 'center': (center_x, center_y) in pixels (0..width, 0..height)
                - 'ratio': (ratio_x, ratio_y) normalized [0.0..1.0] from top-left (0,0)
            or None if no face is detected.
        """
        h, w, _ = frame_bgr.shape
        boxes = []

        if self.use_mediapipe and self.detector is not None:
            rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = self.mp.Image(
                image_format=self.mp.ImageFormat.SRGB,
                data=rgb_frame,
            )
            detection_result = self.detector.detect(mp_image)
            for detection in detection_result.detections:
                bbox = detection.bounding_box
                bx = max(0, int(bbox.origin_x))
                by = max(0, int(bbox.origin_y))
                bw = min(w - bx, int(bbox.width))
                bh = min(h - by, int(bbox.height))
                if bw > 0 and bh > 0:
                    boxes.append((bx, by, bw, bh))

        elif self.cascade is not None and not self.cascade.empty():
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
            )
            for (bx, by, bw, bh) in faces:
                boxes.append((int(bx), int(by), int(bw), int(bh)))

        if not boxes:
            return None

        # Select largest face (closest/primary user)
        best_box = max(boxes, key=lambda b: b[2] * b[3])
        bx, by, bw, bh = best_box

        center_x = bx + bw // 2
        center_y = by + bh // 2

        ratio_x = round(center_x / float(w), 4)
        ratio_y = round(center_y / float(h), 4)

        return {
            "box": (bx, by, bw, bh),
            "center": (center_x, center_y),
            "ratio": (ratio_x, ratio_y),
        }

    def close(self):
        """Clean up detector resources."""
        if self.use_mediapipe and self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass


def prepare_display_frame(frame, target_w=640, target_h=640):
    """
    Center-crops the frame to 1:1 aspect ratio without stretching,
    then resizes to target_w x target_h.
    """
    h, w, _ = frame.shape
    crop_size = min(h, w)
    start_x = (w - crop_size) // 2
    start_y = (h - crop_size) // 2
    cropped = frame[start_y : start_y + crop_size, start_x : start_x + crop_size]
    resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    return resized


def main():
    tracker = FaceTracker(prefer_mediapipe=True)

    # Open webcam (device 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FaceTracker] Error: Could not open video device 0. Checking simulated mode...")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT)

    last_terminal_report = time.time()
    REPORT_INTERVAL = 2.0  # Output to terminal every 2.0 seconds

    print("=" * 65)
    print(" Collexa Face Tracking Active")
    print(f" Window: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print(" Terminal output interval: Every 2.0 seconds")
    print(" Press 'q' or 'ESC' to exit")
    print("=" * 65)

    try:
        while True:
            ret, raw_frame = cap.read() if cap.isOpened() else (False, None)

            if not ret or raw_frame is None:
                # Fallback: display blank canvas if no camera is available
                frame = 20 * (cv2.UMat(DISPLAY_HEIGHT, DISPLAY_WIDTH, cv2.CV_8UC3).get() if hasattr(cv2, 'UMat') else None)
                if frame is None:
                    import numpy as np
                    frame = np.full((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), 25, dtype=np.uint8)
                cv2.putText(
                    frame,
                    "Camera feed not available. Press 'q' to exit.",
                    (30, DISPLAY_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 165, 255),
                    2,
                )
            else:
                # Mirror frame for natural interaction
                raw_frame = cv2.flip(raw_frame, 1)
                # Crop and resize to 640x640
                frame = prepare_display_frame(raw_frame, DISPLAY_WIDTH, DISPLAY_HEIGHT)

            # Detect face
            result = tracker.detect(frame)

            # Periodically print coordinates every 2 seconds
            now = time.time()
            if now - last_terminal_report >= REPORT_INTERVAL:
                last_terminal_report = now
                if result is not None:
                    cx, cy = result["center"]
                    rx, ry = result["ratio"]
                    print(
                        f"[Face Tracking] Center: ({cx:3d}, {cy:3d}) | "
                        f"Normalized from (0,0): (x={rx:.3f}, y={ry:.3f})"
                    )
                else:
                    print("[Face Tracking] Searching... No face detected.")

            # Draw visual tracking cues on display frame
            if result is not None:
                bx, by, bw, bh = result["box"]
                cx, cy = result["center"]
                rx, ry = result["ratio"]

                # 1. Bounding box (vibrant cyan/green)
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 240, 200), 2)

                # 2. Center dot & crosshair
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.line(frame, (cx - 12, cy), (cx + 12, cy), (0, 0, 255), 2)
                cv2.line(frame, (cx, cy - 12), (cx, cy + 12), (0, 0, 255), 2)

                # 3. On-screen HUD readout
                hud_text_1 = f"Center (x, y): ({cx}, {cy})"
                hud_text_2 = f"Normalized: ({rx:.3f}, {ry:.3f})"
                cv2.putText(
                    frame,
                    hud_text_1,
                    (bx, max(25, by - 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 240, 200),
                    2,
                )
                cv2.putText(
                    frame,
                    hud_text_2,
                    (bx, max(45, by - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.50,
                    (255, 255, 255),
                    1,
                )

            # Show window
            cv2.imshow(WINDOW_NAME, frame)

            # Check keypress for exit
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # 27 is ESC
                print("[FaceTracker] Exiting face tracking loop.")
                break

    finally:
        if cap.isOpened():
            cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
