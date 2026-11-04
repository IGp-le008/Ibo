"""
voice_worker.py
Voice process. Runs in its own process.
1. Listens continuously for wake words with openWakeWord (WAKE_MODEL_PATH or placeholder).
2. After a wake word, records one utterance until silence or MAX_UTTERANCE_MS.
3. Transcribes it with the whisper.cpp CLI (whisper-cli) on a WAV file.
4. Sends messages to the controller through out_queue:
   {"type": "wake", "word": str, "t": ms}
   {"type": "speech", "text": str, "t": ms}      (any speech after a wake word)
   {"type": "grateful", "word": str, "t": ms}    (transcript contains a grateful word)
Does not draw and does not decide states.
"""

import os
import subprocess
import time
import wave
import multiprocessing as mp

import numpy as np
import sounddevice as sd

from controlConfig import Audio

try:
    from openwakeword.model import Model as WakeModel
except ImportError:
    WakeModel = None


WAKE_PHRASES = sorted(Audio.WAKE_WORDS, key=len, reverse=True)  # longest first
GRATEFUL_PHRASES = sorted(Audio.GRATEFUL_WORDS, key=len, reverse=True)


def normalize_text(text):
    """Lowercase, strip punctuation, collapse spaces, so matches are whole-word."""
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text.lower())
    return " " + " ".join(cleaned.split()) + " "


def find_phrase(text, phrases):
    """Return the first phrase found as whole words in text, or None."""
    padded = normalize_text(text)
    for phrase in phrases:
        if f" {phrase} " in padded:
            return phrase
    return None


def load_wake_model():
    """Load a custom wake model if configured, else the pretrained placeholder."""
    if WakeModel is None:
        print("[voice_worker] openwakeword not installed; wake words disabled.")
        return None
    if Audio.WAKE_MODEL_PATH:
        return WakeModel(wakeword_models=[Audio.WAKE_MODEL_PATH])
    # Placeholder pretrained model, to be replaced with your own trained model.
    return WakeModel()


def wake_score(scores):
    """Return (name, score) of the highest score in the dict from model.predict()."""
    best_name, best_score = None, 0.0
    for name, score in scores.items():
        if score > best_score:
            best_name, best_score = name, score
    return best_name, best_score


def write_wav(path, samples):
    """Write int16 mono samples to a 16-bit WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(Audio.SAMPLE_RATE)
        wf.writeframes(samples.astype(np.int16).tobytes())


def transcribe(samples):
    """Run whisper-cli on the utterance and return the text (may be empty)."""
    write_wav(Audio.TMP_WAV_PATH, samples)
    cmd = [
        Audio.WHISPER_CLI,
        "-m", Audio.WHISPER_MODEL_PATH,
        "-f", Audio.TMP_WAV_PATH,
        "-nt",              # no timestamps
        "-np",              # no extra prints
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[voice_worker] whisper-cli failed: {e}")
        return ""
    return out.stdout.strip()


def record_utterance(stream):
    """
    Record from the open input stream until SILENCE_END_MS of quiet
    or MAX_UTTERANCE_MS. Returns int16 mono samples.
    """
    chunk_len = int(Audio.SAMPLE_RATE * Audio.CHUNK_MS / 1000)
    frames = []
    silent_ms = 0.0
    total_ms = 0.0
    while total_ms < Audio.MAX_UTTERANCE_MS:
        data, _ = stream.read(chunk_len)
        chunk = data[:, 0].astype(np.int16)
        frames.append(chunk)
        total_ms += Audio.CHUNK_MS
        rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
        if rms < Audio.SILENCE_RMS:
            silent_ms += Audio.CHUNK_MS
            if silent_ms >= Audio.SILENCE_END_MS and total_ms > Audio.SILENCE_END_MS:
                break
        else:
            silent_ms = 0.0
    return np.concatenate(frames) if frames else np.zeros(0, dtype=np.int16)


def run_voice_worker(out_queue, stop_event):
    """Process entry point."""
    model = load_wake_model()
    chunk_len = int(Audio.SAMPLE_RATE * Audio.CHUNK_MS / 1000)
    last_wake_ms = -1e9

    with sd.InputStream(samplerate=Audio.SAMPLE_RATE, channels=1,
                        dtype="int16", blocksize=chunk_len) as stream:
        while not stop_event.is_set():
            data, _ = stream.read(chunk_len)
            now_ms = time.time() * 1000.0
            pcm = data[:, 0].astype(np.int16)

            if model is None:
                continue

            scores = model.predict(pcm)
            name, score = wake_score(scores)
            if score < Audio.WAKE_THRESHOLD or now_ms - last_wake_ms < Audio.WAKE_COOLDOWN_MS:
                continue

            last_wake_ms = now_ms
            out_queue.put({"type": "wake", "word": name, "t": now_ms})

            # Record the rest of the utterance, then transcribe it.
            utt = record_utterance(stream)
            text = transcribe(utt)
            if not text:
                continue
            out_queue.put({"type": "speech", "text": text, "t": time.time() * 1000.0})

            grateful = find_phrase(text, GRATEFUL_PHRASES)
            if grateful:
                out_queue.put({"type": "grateful", "word": grateful, "t": time.time() * 1000.0})


def start_voice_worker(out_queue, stop_event):
    proc = mp.Process(target=run_voice_worker, args=(out_queue, stop_event), daemon=True)
    proc.start()
    return proc