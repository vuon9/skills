"""Make each beat's voice clip and find where the voice is active.

Usage: <venv python> tts.py [narration.json] [out/] [--config demo.json]

demo.json "voice.engine" decides where the clips come from:
- "kokoro": voiced here, with "voice.id" and "voice.speed".
- "recorded": out/<beat>.wav already exists (a person's voice, or a hosted
  voice the human agreed to); this only measures them.
- "none": silent clips as long as it takes to read each caption.

Writes out/<beat>.wav (unless recorded) and out/voice.json: each beat's
length, its loud phrases ("voiced", which light the avatar's ring) and its
syllables ("mouth", which open its mouth), in seconds from the clip's start.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from webdemo import HOME, load_config


def loud_runs(audio, rate, window, share_of_p90, merge_gap):
    """Intervals where the clip is louder than a share of its 90th percentile
    loudness, with runs closer than merge_gap joined."""
    size = int(window * rate)
    rms = np.array([np.sqrt(np.mean(audio[i : i + size] ** 2)) for i in range(0, len(audio), size)])
    runs = []
    for index, loud in enumerate(rms > share_of_p90 * np.percentile(rms, 90)):
        if not loud:
            continue
        start, end = index * window, (index + 1) * window
        if runs and start - runs[-1][1] <= merge_gap + 1e-9:
            runs[-1][1] = end
        else:
            runs.append([start, end])
    return [[round(a, 3), round(b, 3)] for a, b in runs]


def reading_seconds(caption):
    """How long a caption stays up with no voice: about 2.5 words a second,
    never under 2.5 seconds."""
    return max(2.5, len(caption.split()) / 2.5)


def kokoro():
    from kokoro_onnx import Kokoro  # only the kokoro engine needs it

    return Kokoro(str(HOME / "kokoro-q8.onnx"), str(HOME / "voices.npz"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("narration", nargs="?", default="narration.json")
    parser.add_argument("out", nargs="?", default="out")
    parser.add_argument("--config", default="demo.json")
    args = parser.parse_args()

    config = load_config(args.config)
    engine_name = config["voice"]["engine"]
    if engine_name not in ("kokoro", "recorded", "none"):
        raise SystemExit(f"voice engine {engine_name!r}: use kokoro, recorded or none")
    narration = json.loads(Path(args.narration).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    engine = kokoro() if engine_name == "kokoro" else None

    result = {}
    for beat in narration["beats"]:
        path = out / f"{beat['id']}.wav"
        if engine_name == "kokoro":
            audio, rate = engine.create(
                beat["say"], voice=config["voice"]["id"], speed=config["voice"]["speed"], lang="en-us"
            )
            sf.write(path, audio, rate)
        elif engine_name == "recorded":
            if not path.exists():
                raise SystemExit(f"{path} is missing: record one WAV per beat")
            audio, rate = sf.read(path, dtype="float32", always_2d=True)
            audio = audio.mean(axis=1)
        else:
            rate = 24000
            audio = np.zeros(int(reading_seconds(beat["caption"]) * rate), dtype=np.float32)
            sf.write(path, audio, rate)
        silent = engine_name == "none"
        result[beat["id"]] = {
            "duration": round(len(audio) / rate, 3),
            "voiced": [] if silent else loud_runs(audio, rate, 0.05, 0.25, 0.08),
            "mouth": [] if silent else loud_runs(audio, rate, 0.03, 0.6, 0.0),
            "peak": round(float(np.max(np.abs(audio))), 3) if len(audio) else 0.0,
        }
        print(beat["id"], result[beat["id"]]["duration"], "s")

    (out / "voice.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    total = sum(beat["duration"] for beat in result.values())
    print(round(total, 1), "s of voice in", len(result), "clips")


if __name__ == "__main__":
    main()
