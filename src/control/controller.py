"""
control/controller.py
State machine for the CUDO / Collexa face. Runs on the main process.
Reads worker queues without blocking, updates state, and returns a Frame.
Does not draw and does not touch hardware. Speech is handed to AnswerWorker.
"""

import queue
from dataclasses import dataclass
from typing import Optional

from control.control_config import State, Timing


@dataclass
class Frame:
    state: str
    now_ms: float
    target_x: Optional[float] = None       # normalized 0..1 of largest face, or None
    target_y: Optional[float] = None
    grateful_elapsed_ms: float = 0.0       # only meaningful when state == GRATEFUL


class Controller:
    def __init__(self, face_queue, voice_queue, answer_worker):
        self.face_queue = face_queue
        self.voice_queue = voice_queue
        self.answer = answer_worker

        self.state = State.IDLE_LOOK
        self.state_start_ms = 0.0
        self.previous_state = State.IDLE_LOOK
        self.previous_start_ms = 0.0

        self.last_voice_ms = 0.0
        self.loop_count = 0                 # completed 1a -> 1b -> 1c cycles
        self.stuck_in_sleep = False         # True after LOOP_LIMIT cycles, until wake

        self.grateful_start_ms = None

        self.face_present = False
        self.face_seen_ms = None            # controller clock when the face first appeared
        self.target_x = None
        self.target_y = None

    def start(self, now_ms: float) -> None:
        self.state_start_ms = now_ms
        self.last_voice_ms = now_ms

    # ------------------------------------------------------------ input
    def _drain_face(self, now_ms: float) -> None:
        """Keep only the newest face sample. Never blocks."""
        msg = None
        while True:
            try:
                msg = self.face_queue.get_nowait()
            except queue.Empty:
                break
        if msg is None:
            return
        self.face_present = bool(msg.get("present"))
        self.target_x = msg.get("x")
        self.target_y = msg.get("y")
        if self.face_present and self.face_seen_ms is None:
            self.face_seen_ms = now_ms
        if not self.face_present:
            self.face_seen_ms = None

    def _drain_voice(self, now_ms: float) -> None:
        while True:
            try:
                ev = self.voice_queue.get_nowait()
            except queue.Empty:
                break
            kind = ev.get("type")
            if kind == "wake":
                self._wake(now_ms)
            elif kind == "speech":
                self.last_voice_ms = now_ms
                text = ev.get("text", "").strip()
                if text:
                    self.answer.submit(text)
            elif kind == "grateful":
                self._grateful(now_ms)

    # ------------------------------------------------------ transitions
    def _set_state(self, new_state: str, now_ms: float) -> None:
        if new_state == self.state:
            return
        self.previous_state = self.state
        self.previous_start_ms = self.state_start_ms
        self.state = new_state
        self.state_start_ms = now_ms

    def _wake(self, now_ms: float) -> None:
        """Wake word: reset loop count and idle timer, go to ACTIVE."""
        self.loop_count = 0
        self.stuck_in_sleep = False
        self.last_voice_ms = now_ms
        self.grateful_start_ms = None
        self._set_state(State.ACTIVE, now_ms)

    def _grateful(self, now_ms: float) -> None:
        if self.state == State.GRATEFUL:
            return
        self.grateful_start_ms = now_ms
        self._set_state(State.GRATEFUL, now_ms)

    def _advance_idle(self, now_ms: float) -> None:
        """1a -> 1b -> 1c -> 1a, with the PDF timings and the loop limit."""
        elapsed = now_ms - self.state_start_ms

        if self.state == State.IDLE_LOOK:
            if elapsed >= Timing.RANDOM_LOOK_MS:
                self._set_state(State.BORED, now_ms)

        elif self.state == State.BORED:
            if elapsed >= Timing.BORED_MS:
                self.loop_count += 1
                self.stuck_in_sleep = self.loop_count >= Timing.LOOP_LIMIT
                self._set_state(State.SLEEP, now_ms)

        elif self.state == State.SLEEP:
            if self.stuck_in_sleep:
                return                       # stay asleep until a wake word
            if elapsed >= Timing.SLEEP_MS:
                self._set_state(State.IDLE_LOOK, now_ms)

    def _advance_active(self, now_ms: float) -> None:
        """ACTIVE returns to 1a after IDLE_BEFORE_RANDOM_MS with no speech."""
        if now_ms - self.last_voice_ms >= Timing.IDLE_BEFORE_RANDOM_MS:
            self.loop_count = 0
            self.stuck_in_sleep = False
            self._set_state(State.IDLE_LOOK, now_ms)

    def _advance_grateful(self, now_ms: float) -> None:
        if self.grateful_start_ms is None:
            self.state = self.previous_state
            self.state_start_ms = self.previous_start_ms
            return
        if now_ms - self.grateful_start_ms >= Timing.GRATEFUL_MS:
            self.grateful_start_ms = None
            self.state = self.previous_state
            self.state_start_ms = self.previous_start_ms

    def _check_face_trigger(self, now_ms: float) -> None:
        """A person in frame for TRACK_TO_ACTIVE_MS moves 1a to ACTIVE. Only from 1a."""
        if self.state != State.IDLE_LOOK or self.face_seen_ms is None:
            return
        if now_ms - self.face_seen_ms >= Timing.TRACK_TO_ACTIVE_MS:
            self.last_voice_ms = now_ms
            self._set_state(State.ACTIVE, now_ms)

    # ------------------------------------------------------------- step
    def step(self, now_ms: float) -> Frame:
        self._drain_face(now_ms)
        self._drain_voice(now_ms)

        if self.state == State.GRATEFUL:
            self._advance_grateful(now_ms)
        elif self.state == State.ACTIVE:
            self._advance_active(now_ms)
        else:
            self._advance_idle(now_ms)
            self._check_face_trigger(now_ms)

        return self._frame(now_ms)

    def _frame(self, now_ms: float) -> Frame:
        grateful_elapsed = 0.0
        if self.state == State.GRATEFUL and self.grateful_start_ms is not None:
            grateful_elapsed = now_ms - self.grateful_start_ms
        return Frame(
            state=self.state,
            now_ms=now_ms,
            target_x=self.target_x if self.face_present else None,
            target_y=self.target_y if self.face_present else None,
            grateful_elapsed_ms=grateful_elapsed,
        )