# terminal-demo

Make a demo video of a terminal app, a TUI or a CLI, that a viewer can follow
with the sound off. Each key press gets a subtitle with the key and what it
does. The app is the real build, running in a container on a made-up machine,
so nothing private reaches the screen. Quiet synthesized music is optional.

## Use it with a prompt

- "Make a one-minute README demo of this TUI: the main workflow and the filters"
- "Record a release walkthrough of the new search, with subtitles"
- "The demo's third scene opens the wrong panel; fix the tape and record again"

You approve the story (the captions) and the final. The agent builds the
made-up machine, writes the tape, records, checks every take on its frames,
and renders.

## Prerequisites

- Docker. The recording image builds from `scripts/Dockerfile`: VHS 0.12.1,
  tmux, and a small HTTPS server for made-up web answers, compiled inside the
  build, so the host needs no Go.
- Python 3 and ffmpeg (with `ffprobe`) on the host.
- The app under test, added by the project's own Dockerfile `FROM` the
  recording image, or as a static Linux binary.

## How it works

The tape types into `script`, which logs every key with its time, and the app
runs inside tmux. A helper flips a white block in tmux's otherwise blank status
row at each subtitle's first key. After recording, the flips give each subtitle
its exact frame, the row is painted over, and the subtitles go in a band under
the app. `references/timing.md` explains why the video's own clock can't be
trusted.

Every take is checked: each logged key must match its tape line, the flips must
match the captions one for one, no real identifier from a deny list may appear,
and the app's every web request and command call must have been answered by
the made-up machine. Contact sheets show one frame per subtitle for a person to
check each caption.

## Files

- `scripts/`: the image, `record.sh`, `run.sh`, `timeline.py`, `validate.py`,
  `render.py`, `probe.py`, `fakes.py`, `music.py`, and what runs inside the
  container (`marker.py`, `tmux.conf`, `fakeweb/`)
- `templates/`: a tape, `env.sh`, `setup.py` and a project Dockerfile to start
  from
- `references/`: the tape syntax, building the made-up machine, timing, and
  pitfalls
