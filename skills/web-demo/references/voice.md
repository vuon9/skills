# Voice

`demo.json` `voice.engine` picks where the narration comes from. `scripts/tts.py` handles all three; the rest of the pipeline only sees one WAV per beat and `out/voice.json`.

| Engine | What it is | Costs |
| --- | --- | --- |
| `kokoro` (default) | Kokoro-82M (Apache 2.0), free and offline, about four times faster than real time on a laptop CPU | Sounds synthetic to some ears |
| `recorded` | A person reads the timed script, one `out/<beat>.wav` per beat; or a hosted voice (ElevenLabs, OpenAI) the human agreed to | Their time and a quiet room; a hosted voice sends the script to a vendor |
| `none` | Captions only: silent beats as long as it takes to read each caption | No avatar talking; hide it |

## Install (`scripts/install.py`)

The usual downloads (Hugging Face, GitHub releases) are often blocked on locked-down machines and in cloud sandboxes, so the installer takes everything from package registries:

- **Weights:** the npm package `kokoro-q8-shards` holds the q8 ONNX model in six parts. Joined, its sha256 is `fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478`; the installer refuses another.
- **Voices:** the npm package `kokoro-js` ships `voices/*.bin`, one per voice, each 510 x 256 float32. `pack_voices.py` packs them into `voices.npz`.
- **Engine:** Python's `kokoro-onnx` (PyPI), whose `onnxruntime` and `espeakng-loader` wheels carry their binaries. Node's `kokoro-js` is not used to speak: its `onnxruntime-node` postinstall downloads a binary from GitHub and fails offline, so the npm packages install with `--ignore-scripts`.

## Choosing a Kokoro voice

Let the human choose by ear: `scripts/voice_samples.py "<a line from the script>"` renders it in six voices (American and British, female and male). Send the files. `af_heart` is a calm, clear default. The prefix is accent and gender: `a` American, `b` British, then `f` or `m`. Speed 0.9 is calmer, 1.0 suits a walkthrough, 1.1 is brisk.

## A recorded voice

Give the reader the storyboard with each beat's `say` text and id. They record one file per beat, `out/<beat>.wav`, any sample rate, with a second of silence trimmed at each end. Set `voice.engine` to `recorded` and run `tts.py`: it measures the files instead of voicing them, and the recorder and render work as with Kokoro.

## Writing for a voice

- Short sentences. Each beat is one or two of them, tied to one or two clicks.
- Spell out what it misreads: `V-two` for V2, numbers it would read as digits, acronyms as letters with hyphens. Keep the real form in `caption`.
- Commas make pauses. A list of screen names reads better with a comma before the last one.

## Loudness

`tts.py` writes each beat's length, its loud phrases (`voiced`, which light the avatar's ring) and its syllables (`mouth`, which open its mouth). `build.py` normalises the mixed voice to about -16 LUFS. You usually cannot listen from an agent: check that mean volume is around -16 to -18 dB and peaks stay under 0, and tell the human to listen once.
