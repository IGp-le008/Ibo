"""
main.py
Entry point. Runs from src/.
Processes: face_worker (camera), voice_worker (mic + wake word + whisper),
           chat_window (separate 640x640 window).
Threads:   answer thread (RAG, inside AnswerWorker), arm thread (servo moves).
Main loop: controller.step -> draw one expression -> flip -> tick.
"""

import multiprocessing as mp
import queue
import threading

import pygame

from control.control_config import State
from control.controller import Controller
from control.answer_worker import AnswerWorker
from control.face_worker import start_face_worker
from control.voice_worker import start_voice_worker
from control.chat_window import start_chat_window
from control.servo import ArmController

from expressions.expression_config import Window
from expressions.idle_look import GazeSource, draw_idle_look
from expressions.bored import draw_bored
from expressions.sleep import draw_sleep
from expressions.listening import draw_listening
from expressions.grateful import draw_grateful


class ArmThread:
    """Runs blocking servo moves off the pygame loop. Keeps only the latest target."""

    def __init__(self):
        self.arm = ArmController()
        self.targets = queue.Queue(maxsize=1)
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def submit(self, target):
        try:
            self.targets.put_nowait(target)
        except queue.Full:
            try:
                self.targets.get_nowait()
            except queue.Empty:
                pass
            self.targets.put_nowait(target)

    def _run(self):
        while True:
            self.arm.apply(self.targets.get())


def draw_frame(surface, frame, gaze):
    """Pick the expression for the controller state. Caller owns flip()."""
    if frame.state == State.IDLE_LOOK:
        draw_idle_look(surface, gaze, frame.now_ms)
    elif frame.state == State.BORED:
        draw_bored(surface, gaze, frame.now_ms)
    elif frame.state == State.SLEEP:
        draw_sleep(surface, frame.now_ms)
    elif frame.state == State.ACTIVE:
        # Active: eyes follow the speaker's face centre (listening face).
        draw_listening(surface, frame.now_ms, frame.target_x, frame.target_y)
    elif frame.state == State.GRATEFUL:
        draw_grateful(surface, frame.grateful_elapsed_ms)


def arm_target_for(frame, gaze):
    """Only 1a moves the arms. Random look may lift them; everything else holds down."""
    if frame.state == State.IDLE_LOOK:
        return gaze.arm_target
    return "down"


def main():
    # Create processes before pygame.init() so forked children do not inherit a display.
    face_q = mp.Queue(maxsize=5)
    voice_q = mp.Queue()
    chat_q = mp.Queue()
    stop = mp.Event()

    start_face_worker(face_q, stop)
    start_voice_worker(voice_q, stop)
    start_chat_window(chat_q, stop)

    answers = AnswerWorker(chat_q)
    answers.start()
    controller = Controller(face_q, voice_q, answers)

    arm = ArmThread()
    arm.start()

    pygame.init()
    screen = pygame.display.set_mode((Window.WIDTH, Window.HEIGHT))
    pygame.display.set_caption("CUDO Robot - Face")
    clock = pygame.time.Clock()

    gaze = GazeSource()
    controller.start(pygame.time.get_ticks())
    last_arm_sent = None

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            now = pygame.time.get_ticks()
            frame = controller.step(now)
            draw_frame(screen, frame, gaze)
            pygame.display.flip()

            target = arm_target_for(frame, gaze)
            if target != last_arm_sent or target == "random":
                arm.submit(target)
                last_arm_sent = target

            clock.tick(Window.FPS)
    finally:
        stop.set()
        arm.arm.close()
        pygame.quit()


if __name__ == "__main__":
    main()