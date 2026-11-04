"""
control/controller.py
State machine for the CUDO / Collexa face.
Runs on the main process. Reads worker messages without blocking, updates the
state, and returns a Frame description that main.py passes to the drawing functions.
Does not draw and does not touch hardware directly.

States (from the PDF):
  IDLE_LOOK (1a) -> BORED (1b) -> SLEEP (1c) -> IDLE_LOOK ...
  Wake word or face in frame for 15 s (from 1a only) -> ACTIVE
  ACTIVE: LISTENING face while speech is being handled, TRACKING eyes on face
  GRATEFUL: short reaction to a grateful phrase, then returns to the previous state
"""

import queue
from dataclasses import dataclass, field
from typing import Optional

from control.control_config import State, Timing


@dataclass
class Frame:
    """Everything main.py needs to draw one frame and drive the arm."""
    state: str
    now_ms: float
    target_x: Optional[float] = None     # normalized 0..1, largest face, or None
    target_y: Optional[float] = None
    grateful_elapsed_ms: float = 0.0     # only meaningful when state == GRATEFUL
    arm_target: str = "down"             # "down", "center", "up", "random"


@dataclass
class Controller:
    face_queue: queue.Queue
    voice_queue: queue.Queue

    state: str = State.IDLE_LOOK
    previous_state: str = State.IDLE_LOOK
    state_start_ms: float = 0.0
    last_voice_ms: float = 0.0           # time of last speech (resets idle timer)
    loop_count: int = 0                  # completed 1a->1b->1c cycles
    active_since_ms: Optional[float] = None
    grateful_start_ms: Optional[float] = None
    face_seen_ms: Optional[float] = None # when a face first appeared, for 15 s rule
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    face_present: bool = False
    stuck_in_sleep: bool = False         # set after LOOP_LIMIT cycles

    def start(self, now_ms: float) -> None:
        self.state = State.IDLE_LOOK
        self.state_start_ms = now_ms
        self.last_voice_ms = now_ms

    # ----------------------------------------------------------- input
    def _drain_face(self) -> None:
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

    def _drain_voice(self, now_ms: float) -> list:
        """Return voice events this frame. Updates voice-driven flags."""
        events = []
        while True:
            try:
                ev = self.voice_queue.get_nowait()
            except queue.Empty:
                break
            events.append(ev)
            kind = ev.get("type")
            if kind == "wake":
                self._wake(now_ms)
            elif kind == "speech":
                self.last_voice_ms = now_ms
            elif kind == "grateful":
                self._grateful(now_ms)
        return events

    # ------------------------------------------------------- transitions
    def _set_state(self, new_state: str, now_ms: float) -> None:
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            self.state_start_ms = now_ms

    def _wake(self, now_ms: float) -> None:
        """Wake word: reset loop count and idle timer, go to ACTIVE."""
        self.loop_count = 0
        self.stuck_in_sleep = False
        self.last_voice_ms = now_ms
        self.active_since_ms = now_ms
        self._set_state(State.ACTIVE, now_ms)

    def _grateful(self, now_ms: float) -> None:
        if self.state == State.GRATEFUL:
            return
        self.grateful_start_ms = now_ms
        self.previous_state = self.state
        self.state = State.GRATEFUL
        self.state_start_ms = now_ms

    def _advance_idle(self, now_ms: float) -> None:
        """Run the 1a -> 1b -> 1c -> 1a loop with the timing from the PDF."""
        elapsed = now_ms - self.state_start_ms

        if self.state == State.IDLE_LOOK:
            if now_ms - self.last_voice_ms < Timing.IDLE_BEFORE_RANDOM_MS and self.loop_count == 0 \
                    and self.last_voice_ms != 0.0 and elapsed < Timing.RANDOM_LOOK_MS:
                pass
            if elapsed >= Timing.RANDOM_LOOK_MS:
                self._set_state(State.BORED, now_ms)

        elif self.state == State.BORED:
            if elapsed >= Timing.BORED_MS:
                self.loop_count += 1
                if self.loop_count > Timing.LOOP_LIMIT - 1:
                    self.stuck_in_sleep = True
                self._set_state(State.SLEEP, now_ms)

        elif self.state == State.SLEEP:
            if self.stuck_in_sleep:
                return                         # stay asleep until a wake word
            if elapsed >= Timing.SLEEP_MS:
                self._set_state(State.IDLE_LOOK, now_ms)

    def _advance_active(self, now_ms: float) -> None:
        """
        ACTIVE stays until 2 min with no voice, then the bot returns to 1a
        (Timing.IDLE_BEFORE_RANDOM_MS). Tracking and listening run inside ACTIVE.
        """
        if now_ms - self.last_voice_ms >= Timing.IDLE_BEFORE_RANDOM_MS:
            self.loop_count = 0
            self._set_state(State.IDLE_LOOK, now_ms)

    def _advance_grateful(self, now_ms: float) -> None:
        if self.grateful_start_ms is None:
            return
        if now_ms - self.grateful_start_ms >= Timing.GRATEFUL_MS:
            self.grateful_start_ms = None
            self.state = self.previous_state
            self.state_start_ms = now_ms

    def _check_face_trigger(self, now_ms: float) -> None:
        """A person in frame for 15 s moves 1a to ACTIVE. Only from 1a."""
        if self.state != State.IDLE_LOOK:
            return
        if self.face_seen_ms is None:
            return
        if now_ms - self.face_seen_ms >= Timing.TRACK_TO_ACTIVE_MS:
            self.last_voice_ms = now_ms
            self._set_state(State.ACTIVE, now_ms)

    # ------------------------------------------------------------ frame
    def step(self, now_ms: float) -> Frame:
        """Advance one frame and return what main.py should draw."""
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
        state = self.state
        if state == State.IDLE_LOOK:
            arm = "random_or_down"       # controller passes to idle_look's GazeSource
        elif state == State.BORED:
            arm = "down"
        elif state == State.SLEEP:
            arm = "down"
        elif state == State.LISTENING:
            arm = "down"
        elif state == State.TRACKING:
            arm = "down"
        else:
            arm = "down"

        # Tracking-only eyes: visible face drives the eyes when ACTIVE or GRATEFUL.
        track_x = self.target_x if self.face_present else None
        track_y = self.target_y if self.face_present else None

        return Frame(
            state=state,
            now_ms=now_ms,
            target_x=track_x,
            target_y=track_y,
            grateful_elapsed_ms=(now_ms - self.grateful_start_ms)
                                if state == State.GRATEFUL and self.grateful_start_ms else 0.0,
            arm_target=arm,
        )