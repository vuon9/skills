---
name: web-demo
description: "Use when making a narrated demo video of a web app, such as a feature walkthrough for stakeholders or a release demo, with a voiceover, captions, a visible cursor and a small bot avatar that shows who is talking. Aligns audience, depth, cases, layout, style and voice with the human first, drives the real app with a Playwright script, voices each beat with a free offline voice (Kokoro) or a recorded one, times the voice to the clicks, checks frames from every beat, and renders the video with ffmpeg."
---

# Web demo

A video of a real web app that someone can follow with or without sound. A script clicks through the app while a voice explains each step; captions and a bot avatar that lights up while it talks sit in a band beside the app. The demo answers what its audience wants to know, and nothing on screen is invented.

## Rules

- **Align before building.** Ask the questions in `references/questions.md` and get a yes on the storyboard before recording anything. A polished video of the wrong cases costs more than the questions.
- **The real app, unchanged.** No demo mode, no slower animations, no fake screens in the final. A cursor, highlights, captions and the avatar go on afterwards or are injected by the recorder. A stand-in page is fine for a first proof of the pipeline; say so on screen and in your message.
- **Data you can reset.** Every take starts from the same seeded data. Write the seed and a reset script before the first take.
- **Say only what the screen shows.** Each sentence must be true of what is on screen while it is spoken. A step done off camera is said, not implied. Check by looking at frames, not by reading the script.
- **The voice stays offline unless the human agrees.** A hosted voice sends the script to a vendor.
- **Never overwrite a final.** Each render gets a new name; the human may like the last one.
- **Videos, audio, seeds and scratch stay out of the repo** unless the human asks.

## Pipeline

Work in a demo folder outside the repo. `<skill>` is this skill's folder; `$PY` is `~/.cache/web-demo/.venv/bin/python` once step 2 has run.

1. **Align.** Look at the feature (code, tests, tickets), then ask the rounds in `references/questions.md`. Copy `<skill>/templates/demo.json` and record the answers in it. Write the storyboard, one line per scene with its narration, and get a yes.
2. **Install, once per machine:** `python3 <skill>/scripts/install.py` (Node, Python 3.10+). It installs the Kokoro voice from npm and PyPI and checks its checksum, Playwright for Python, and Chromium (set `WEB_DEMO_CHROMIUM` to use a browser already installed). Read `references/voice.md`.
3. **Voice samples**, when the voice is Kokoro: `$PY <skill>/scripts/voice_samples.py "<a line from the script>"`, send the files, and put the chosen id in `demo.json`.
4. **Narration.** Copy `<skill>/templates/narration.json`: one beat per voice clip, `say` for the voice (spell out what it misreads, like `V-two`) and `caption` for the viewer. Then `$PY <skill>/scripts/tts.py`. It writes a clip per beat and `out/voice.json`. With a recorded voice, put one `out/<beat>.wav` per beat first.
5. **Avatar:** `$PY <skill>/scripts/avatar.py` draws it with the name and accent from `demo.json`.
6. **Seed and reset.** Script the data each scene needs and a reset that rebuilds it from a clean copy. Dry-run every scene's outcome in code before recording it.
7. **Recorder.** Copy `<skill>/templates/record.py` and `title.html`, then write one scene function per beat. Call `demo.speak()` once the scene's page has loaded; `demo.at(seconds)` waits for a moment in the voice. Read `references/recorder.md`.
8. **Take:** reset the data, then `PYTHONPATH=<skill>/scripts $PY record.py [storage-state.json]`. A failed scene saves `out/fail_<beat>.png`; fix, reset, record again. Share one scene as a proof clip before the full take, if the human asked for review points.
9. **Render:** `python3 <skill>/scripts/build.py <final>.mp4`. It follows `demo.json` (layout, captions, avatar, colours) and writes `<final>.srt` beside it.
10. **Check:** `python3 <skill>/scripts/frames.py <final>.mp4`, then open every contact sheet. Each beat has a frame early and late in its voice; the caption must be true of the screen above it. A mismatch is a story or timing bug: fix, reset, take again.

## Before you hand it over

- You have looked at every contact sheet, and nothing covers the data a sentence talks about.
- The voice is not silent (`build.py` prints the loudness; about -16 to -18 dB mean is right), and you said you could not listen to it, if you could not.
- Say how long it is and how big, what it shows against what was agreed in step 1, which steps happened off camera, and anything on screen that is not the real app or real behaviour.
- Read `references/pitfalls.md` once per project: most of its entries cost a full take to learn.
