"""Render one sentence in several voices, so the human can pick one by ear.

Usage: <venv python> voice_samples.py ["a sentence from the script"] [--voices a,b,c] [--out samples/]

Writes samples/<voice>.wav and prints each file. Send them to the human; an
agent usually cannot listen. The chosen id goes in demo.json "voice.id".
"""

import argparse
from pathlib import Path

import soundfile as sf

from tts import kokoro

# American and British, female and male: a spread to start from.
DEFAULT_VOICES = ["af_heart", "af_bella", "am_michael", "am_fenrir", "bf_emma", "bm_george"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sentence",
        nargs="?",
        default="This is the order queue. Every new order lands here, with its status.",
    )
    parser.add_argument("--voices", default=",".join(DEFAULT_VOICES))
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--out", default="samples")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    engine = kokoro()
    for voice in args.voices.split(","):
        audio, rate = engine.create(args.sentence, voice=voice.strip(), speed=args.speed, lang="en-us")
        path = out / f"{voice.strip()}.wav"
        sf.write(path, audio, rate)
        print(path, f"{len(audio) / rate:.1f} s")


if __name__ == "__main__":
    main()
