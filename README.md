# CUDO / Collexa Robot Face

A Raspberry Pi 3B+ desk robot with an animated face, a voice interface, and a document question-answering assistant. The face shows idle, sleep, listening, tracking, and grateful expressions. Two 9g servos move the arms. The bot answers questions about a PDF using retrieval-augmented generation (RAG), and the answers stream into a separate chat window.

Status: expressions, state machine, voice input, camera tracking, servo control, and RAG chat are implemented. Text-to-speech (Chatterbox) is deferred.

## Features

- **Idle behaviour (State 1):** random looking with blinks (1a), bored eyes (1b), then sleep with drifting Zs (1c). After three full cycles the bot stays asleep until a wake word.
- **Listening (State 2):** eyes follow the speaker's face centre.
- **Tracking (State 3):** eyes follow the largest face in view. A face present for 15 s in 1a moves the bot to Active.
- **Voice input:** wake-word detection with openWakeWord, then transcription with whisper.cpp (tiny model).
- **Grateful reaction:** short happy face when the speaker says a thank-you or compliment word.
- **Arms:** two servos on hardware PWM. Look-down lifts them at random positions.
- **Chat window:** separate 640×640 window with streamed answers and page citations.
- **RAG:** LangGraph pipeline over a Chroma vector store, using an OpenAI-compatible API (OpenRouter by default).

## Project structure

```
Ibo/
├── main.py                  # not in src; see "Running" (entry point is src/main.py)
├── README.md
├── requirements.txt
├── .env                     # API keys (not committed)
├── data/
│   └── muse.pdf             # source document
├── storage/
│   └── chroma/              # vector index (created by ingest)
├── whisper.cpp/             # local clone, gitignored
└── src/
    ├── main.py              # entry point: starts workers and the face loop
    ├── control/
    │   ├── control_config.py   # state timers, camera, audio, chat settings
    │   ├── controller.py       # state machine (no drawing, no hardware)
    │   ├── face_worker.py      # camera process: largest face position
    │   ├── voice_worker.py     # mic process: wake word, record, whisper-cli
    │   ├── answer_worker.py    # thread: runs RAG, streams tokens
    │   ├── chat_window.py      # process: 640×640 chat window
    │   └── servo.py            # arm PWM (stub on laptop)
    ├── expression/
    │   ├── expression_config.py  # sizes, ratios, colours, blink
    │   ├── drawing.py            # shared eye, glow, mouth primitives
    │   ├── idle_look.py          # 1a
    │   ├── bored.py              # 1b
    │   ├── sleep.py              # 1c
    │   ├── listening.py          # State 2
    │   ├── tracking.py           # State 3 (horizontal only)
    │   └── grateful.py           # grateful reaction
    └── rag/
        ├── config.py           # reads .env, resolves paths from project root
        ├── cli.py              # terminal Q&A
        ├── embeddings.py
        ├── ingest.py           # PDF → chunks → Chroma
        ├── graph.py            # retrieve → grade → rewrite/answer (streams)
        ├── models.py
        └── vectorstore.py
```

Configuration lives in two places on purpose. `control/control_config.py` holds values the controller reads to decide transitions. `expression/expression_config.py` holds values only the drawing code uses. Expressions never import each other, and the controller never draws.

## Requirements

- Python 3.10 or newer
- Linux (tested on Ubuntu; Raspberry Pi OS for the device)
- A webcam at device index 0
- A microphone
- An OpenRouter (or compatible) API key
- Raspberry Pi 3B+ with `RPi.GPIO` for servos (optional on a laptop)

## Installation

```bash
cd Ibo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

System packages for audio (Debian/Ubuntu/Raspberry Pi OS):

```bash
sudo apt install libportaudio2
```

### whisper.cpp (speech-to-text)

whisper.cpp is built from source and kept inside the project folder, which is gitignored.

```bash
cd Ibo
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build && cmake --build build -j --config Release
sh ./models/download-ggml-model.sh tiny
```

Then set the absolute paths in `src/control/control_config.py`:

```python
WHISPER_CLI = "/full/path/to/Ibo/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL_PATH = "/full/path/to/Ibo/whisper.cpp/models/ggml-tiny.bin"
```

### Wake word model

The app uses openWakeWord's pretrained placeholder model. To use your own wake words, train a model and set `Audio.WAKE_MODEL_PATH` in `control_config.py` to its `.onnx` or `.tflite` file.

## Configuration

Create `Ibo/.env`:

```
CHAT_API_KEY=your_openrouter_key
EMBEDDING_API_KEY=your_openrouter_key
BASE_URL=https://openrouter.ai/api/v1
CHAT_MODEL=nvidia/nemotron-3.5-lightning:free
EMBEDDING_MODEL=nvidia/nemotron-3.5-embed-1b:free
```

Index the PDF once, and again whenever it changes:

```bash
cd src
python -m rag.ingest --pdf ../data/muse.pdf
```

Other settings:

- **Wake and grateful words:** `Audio.WAKE_WORDS` and `Audio.GRATEFUL_WORDS` in `control_config.py`.
- **Servo pins and angles:** `Servo` class in `control_config.py`. Angles: 0° down, 90° centre, 180° up.
- **Blink timing:** `Blink.INTERVAL_MS` in `expression_config.py`.
- **Chat font (for Nepali/Hindi):** `Chat.FONT_PATH`, set to a Devanagari TTF.

## Running

Run everything from `src/`:

```bash
cd src
python -m rag.cli      # optional: test the RAG path alone
python main.py         # full app
```

Press `Esc` in the face window, or close either window, to stop.

## Usage

1. Start the app. The face begins in random looking (1a).
2. Say a wake word such as "hello collexa". The face switches to listening, and the eyes follow you.
3. Ask a question. The answer streams into the chat window with page citations.
4. Say "thank you" to see the grateful reaction.
5. Stand in front of the camera for 15 s in 1a to start Active and tracking.
6. With no speech for 2 minutes, the bot returns to random looking and the cycle repeats.

## Troubleshooting

| Problem | Fix |
|---|---|
| Wake word never fires | The placeholder model only detects its built-in phrase. Train and set `WAKE_MODEL_PATH`. |
| `whisper-cli` not found | Set `WHISPER_CLI` to the full path. |
| Camera fails to open | Another app holds device 0. Close it, or change `Camera.DEVICE_INDEX`. |
| Nepali text shows as boxes | Set `Chat.FONT_PATH` to a Devanagari font. |
| `ModuleNotFoundError: config` | Use `control.control_config` and `expression.expression_config` imports. |
| Empty answers from RAG | Re-run `rag.ingest`, and check `.env`. |

## Roadmap

- Chatterbox text-to-speech for spoken answers (deferred, needs more compute than the Pi 3B+ provides)
- Choosing the Active-state face (listening or horizontal tracking)
- Startup idle face for the first two minutes
- Custom wake-word model for "hello collexa" and the Nepali words
- Whisper base or small for better Nepali accuracy, if the hardware allows

