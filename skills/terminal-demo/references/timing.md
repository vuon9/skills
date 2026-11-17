# Timing subtitles

## What works

The tape's hidden setup runs `script --log-in --log-timing`, which logs every
byte typed, and runs the app's shell inside tmux. tmux's status row is blank in
the terminal's own background, except for a white block. `marker.py` follows
the key log as it is written and flips the block at each subtitle's first key.

`timeline.py` then:

1. pairs every logged key with its tape line, and refuses the take if the two
   differ;
2. finds the status row as the lowest bright run of pixels in the bottom left
   once the block is on, and the flips by the row's brightness;
3. refuses the take unless the flips and the captions match one for one;
4. paints the row over with the terminal's background, a few pixels wider than
   the block, and adds the subtitles in a band under the app.

Each subtitle starts at its flip, to the frame, whatever VHS's clock does.

## Why nothing else works

VHS captures frames on a timer and writes them at a fixed rate, so its video
clock drifts from real time: about 8% fast in one take, 4% slow in the next,
and up to a second or two lost at busy moments such as an app starting or a
popup streaming output. Every attempt to recover the mapping after the fact
failed on real frames:

- **The tape's sleeps.** Off by seconds within a minute.
- **ffmpeg's scene score.** A dark TUI where one row's highlight moves barely
  registers.
- **Matching each key to the next repaint** (largest pixel change between
  frames). Spinners and popups repaint constantly, and the tracker drifts onto
  them.
- **Anchors on full-screen changes** (an app opening, a popup). Several look
  alike, and a near-sighted match takes the wrong one.
- **Cross-correlating the app's output with repaints** (`script --log-out`).
  No stable lag shows up at all.
- **A lower frame rate.** It changes the drift's direction, not its existence.

## The key log

- The terminal's replies to the app's questions arrive on the same input stream
  as the keys: mode reports (`ESC[?2026;0$y`), colors (`ESC]11;rgb:...`),
  cursor positions (`ESC[12;1R`). `timeline.py` strips them.
- An app in application cursor mode gets arrows as `ESC O B`, not `ESC [ B`.
  They are the same key.
