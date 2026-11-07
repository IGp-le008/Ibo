"""
control/answer_worker.py
Background thread that runs the RAG graph for each recognised speech utterance.
Questions are handled one at a time, in order. Output goes to the chat window
through chat_queue. The face loop is never blocked.
"""

import queue
import threading

from rag.graph import ask


class AnswerWorker:
    def __init__(self, chat_queue):
        self.chat_queue = chat_queue
        self.questions = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def submit(self, text):
        self.questions.put(text)

    def _emit(self, msg):
        self.chat_queue.put(msg)

    def _run(self):
        while True:
            text = self.questions.get()
            self._emit({"type": "user", "text": text})
            self._emit({"type": "assistant_start"})
            try:
                result = ask(
                    text,
                    on_token=lambda piece: self._emit({"type": "token", "text": piece}),
                )

                #------- Currently result = {answer, cources, search_query, rewrite_count}. So when self._emit(type,result) why only return sources and not answer to chat_queue??------------------

                self._emit({"type": "sources", "items": result["sources"]})
            except Exception as exc:
                self._emit({"type": "error", "text": str(exc)})