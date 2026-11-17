---
name: terminal-demo
description: "Use when making a demo video of a terminal app (a TUI or a CLI), such as a README clip or a release walkthrough, that should show what each key does with subtitles, run on made-up data instead of a real machine, and optionally carry quiet music. Records the real build in a container with VHS, times each subtitle to the frame, checks every take, and renders the final."
---

# Terminal demo

A video of a terminal app that someone can follow with the sound off. Each key press gets a subtitle: the key, and what it does. The app is the real build, it runs on a made-up machine, and every take is checked before anyone watches it.

## Rules

- **Made up only.** Every name, version, path, URL, host and person on screen is invented. Public names the app needs to work (a base image, a language runtime) may stay real. Keep a deny list of real identifiers outside the demo folder and point `TD_DENY` at it.
- **The real build, unchanged.** Never add a demo mode, a slower spinner or a click effect to the app. Anything extra goes on the video afterwards.
- **Every key has a subtitle, and every subtitle matches its frame.** The tools prove the first. Only looking at the stills proves the second, so look at every one.
- **Never overwrite a take or a final.** Each recording gets a new name; the human may already like the last one.
- **Short wins.** A README clip is about a minute: one workflow, the UI, one or two filters. Cut anything a viewer can learn later.
- **Videos, tapes and scratch stay out of the repo** unless the human asks.

## Pipeline

Work in a demo folder outside the repo. `<skill>` is this skill's folder.

1. **Image, once:** `docker build -t terminal-demo:1 <skill>/scripts`. A project adds its app with its own Dockerfile `FROM terminal-demo:1` (`<skill>/templates/Dockerfile`), or mounts a static Linux binary through the made-up machine.
2. **Story first.** Write the scenes as captions: what the viewer should learn, and the keys that show it. Agree on them with the human before building anything.
3. **Made-up machine.** Copy `<skill>/templates/setup.py` and `env.sh`. Fake every command the app runs and every web answer it asks for with `scripts/fakes.py`. Read `references/machine.md`.
4. **Tape.** Copy `<skill>/templates/demo.tape`. Keep its hidden setup as it is, renaming only the file name. Put a `#> caption` line above the keys each subtitle covers. Read `references/tape.md`.
5. **Record:** `python3 setup.py && <skill>/scripts/record.sh demo.tape` (with `TD_IMAGE` for a project image). It refuses a take name that exists.
6. **Time:** `python3 <skill>/scripts/timeline.py demo.tape <take>`. It refuses a take whose key log doesn't match the tape, or whose subtitle marker flips don't match the captions.
7. **Check:** `TD_DENY=<deny list> python3 <skill>/scripts/validate.py <take>`, then open every contact sheet with its index and check each caption against its frame. A mismatch is a story bug: fix the tape, bump the take name, record again.
8. **Render:** `python3 <skill>/scripts/render.py <final> <take> [<take>...]`, then validate again with `--final <final> [--with <other takes>]`. Give the human the file.

When the navigation of a scene is in doubt (which row a key lands on, where focus goes after a popup), probe it before recording a full take: `<skill>/scripts/probe.py demo.tape steps.txt`, then `run.sh 'vhs probe.tape'` and `probe.py --tile`. One screenshot per key, in a minute.

## Timing

Never time subtitles from VHS's clock: its video runs faster than real time in one take and slower in the next, unevenly. The tape's hidden setup runs the app inside tmux with a blank status row, and `marker.py` flips a white block there at each subtitle's first key, read live from `script`'s key log. `timeline.py` finds the flips in the video, then paints the row over. `references/timing.md` says why every other method failed.

## Before you hand it over

- `validate.py` passes, and you have looked at every contact sheet.
- The final plays with subtitles in a band under the app, never over it.
- Say how long it is and how big, what it shows, what was cut, and anything shown that isn't made up.
- Read `references/pitfalls.md` once per project: most of its entries cost a full take to learn.
