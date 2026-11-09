"""
face_worker.py
Camera process. Reads the webcam, detects the largest face, and sends
its normalized center to the controller through a multiprocessing queue.
Message format: {"t": timestamp_ms, "x": float|None, "y": float|None, "present": bool}
Runs in its own process so camera and detection never block the pygame loop.
Does not draw and does not decide states.
"""

import time
import multiprocessing as mp

import cv2

from control.control_config import Camera
from control.face_tracking import FaceTracker, prepare_display_frame


def run_face_worker(out_queue, stop_event):
    """Process entry point. Puts one message per SEND_INTERVAL_MS into out_queue."""
    tracker = FaceTracker(prefer_mediapipe=True)
    cap = cv2.VideoCapture(Camera.DEVICE_INDEX)
    if not cap.isOpened():
        print("[face_worker] Could not open camera; sending no-face messages.")

    last_seen_ms = None
    last_x, last_y = None, None
    last_send_ms = 0.0

    try:
        while not stop_event.is_set():
            now_ms = time.time() * 1000.0

            ret, raw = cap.read() if cap.isOpened() else (False, None)
            result = None
            if ret and raw is not None:
                raw = cv2.flip(raw, 1)   # mirror, as face_tracking.py does
                frame = prepare_display_frame(raw, Camera.FRAME_W, Camera.FRAME_H)
                result = tracker.detect(frame)

            if result is not None:
                #potential guess of:
                x, y = result["ratio"]
                last_x, last_y = x, y

                # rx, ry = result["ratio"]
                # last_x, last_y = rx, ry
                last_seen_ms = now_ms
                present = True
            else:
                present = False

            # Keep the last position for a short grace period so brief
            # detection misses do not make the eyes jump to center.
            if not present and last_seen_ms is not None \
                    and now_ms - last_seen_ms <= Camera.PERSON_LOST_GRACE_MS:
                x, y = last_x, last_y
                present = True
            elif not present:
                x, y = None, None
            else:
                x, y = last_x, last_y

            if now_ms - last_send_ms >= Camera.SEND_INTERVAL_MS:
                last_send_ms = now_ms
                msg = {"t": now_ms, "x": x, "y": y, "present": present}
                try:
                    out_queue.put_nowait(msg)
                except Exception:
                    pass   # queue full: drop this sample, the next one is fresher
    finally:
        if cap.isOpened():
            cap.release()
        tracker.close()


def start_face_worker(out_queue, stop_event):
    """Create and start the camera process. Returns the Process object."""
    proc = mp.Process(target=run_face_worker, args=(out_queue, stop_event), daemon=True)
    proc.start()
    return proc