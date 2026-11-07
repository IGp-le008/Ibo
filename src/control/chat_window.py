"""
control/chat_window.py
Separate 640x640 window showing the conversation. Runs in its own process
with its own pygame display. Does not touch the face window.
Messages arrive on chat_queue:
  {"type": "user", "text": str}
  {"type": "assistant_start"}
  {"type": "token", "text": str}          streamed piece of the answer
  {"type": "sources", "items": [{"source": str, "page": int}, ...]}
  {"type": "error", "text": str}
"""

import multiprocessing as mp
import queue

import pygame

from control.control_config import Chat


def wrap_text(text, font, max_width):
    """Word-wrap text to max_width pixels. Keeps existing line breaks."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            trial = word if not current else current + " " + word
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


class Transcript:
    """Ordered list of (speaker, text). Streaming tokens extend the last assistant entry."""

    def __init__(self):
        self.entries = []
        self.dirty = True

    def _add(self, speaker, text):
        self.entries.append([speaker, text])
        self.dirty = True

    def apply(self, msg):
        kind = msg.get("type")
        if kind == "user":
            self._add("user", msg.get("text", ""))
        elif kind == "assistant_start":
            self._add("assistant", "")
        elif kind == "token":
            if not self.entries or self.entries[-1][0] != "assistant":
                self._add("assistant", "")
            self.entries[-1][1] += msg.get("text", "")
            self.dirty = True
        elif kind == "sources":
            items = msg.get("items") or []
            if items:
                text = "Sources: " + ", ".join(f"{s['source']}, p. {s['page']}" for s in items)
                self._add("sources", text)
        elif kind == "error":
            self._add("error", msg.get("text", "Unknown error"))


SPEAKER_STYLE = {
    "user": (Chat.USER_LABEL, Chat.USER_COLOR),
    "assistant": (Chat.ASSISTANT_LABEL, Chat.ASSISTANT_COLOR),
    "sources": ("", Chat.SOURCE_COLOR),
    "error": ("Error:", Chat.ERROR_COLOR),
}


def build_lines(entries, font, max_width):
    """Return a list of (text, color) lines for all entries."""
    lines = []
    for speaker, text in entries:
        label, color = SPEAKER_STYLE[speaker]
        prefix = f"{label} " if label else ""
        for line in wrap_text(prefix + text, font, max_width):
            lines.append((line, color))
        lines.append(("", color))
    return lines


def run_chat_window(chat_queue, stop_event):
    """Process entry point. Shows the newest lines (auto-scroll to bottom)."""
    pygame.init()
    screen = pygame.display.set_mode((Chat.WIDTH, Chat.HEIGHT))
    pygame.display.set_caption("Collexa Chat")
    font = pygame.font.Font(Chat.FONT_PATH, Chat.FONT_SIZE)
    clock = pygame.time.Clock()

    transcript = Transcript()
    max_width = Chat.WIDTH - 2 * Chat.PAD
    line_h = font.get_linesize() + Chat.LINE_GAP
    max_lines = max(1, (Chat.HEIGHT - 2 * Chat.PAD) // line_h)
    cached_lines = []

    running = True
    while running and not stop_event.is_set():
        for event in pygame.event.get():

            #----------HOW DOES pygame.QUIT WORK? -------------

            if event.type == pygame.QUIT:
                running = False

        while True:
            try:

                # --------------HOW IS chat_queue ELEMENTS DECIDED?--------------

                msg = chat_queue.get_nowait()
            except queue.Empty:
                break
            transcript.apply(msg)

        if transcript.dirty:
            cached_lines = build_lines(transcript.entries, font, max_width)
            transcript.dirty = False

        screen.fill(Chat.BACKGROUND)
        visible = cached_lines[-max_lines:]
        y = Chat.PAD
        for text, color in visible:
            if text:
                screen.blit(font.render(text, True, color), (Chat.PAD, y))
            y += line_h
        pygame.display.flip()
        clock.tick(Chat.FPS)

    pygame.quit()


def start_chat_window(chat_queue, stop_event):
    proc = mp.Process(target=run_chat_window, args=(chat_queue, stop_event), daemon=True)
    proc.start()
    return proc