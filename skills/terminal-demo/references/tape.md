# The tape

A VHS tape with two additions: `#! keylog` marks where the key log starts, and
`#> caption` lines say what each subtitle shows.

## Captions

```
#> open diffkit: what it is, what it pulls in
Enter
Sleep 2s
#> its advisories
Type "a"
Sleep 2.5s
```

- A caption covers the key lines after it, up to the next caption.
- The keys on screen come from those lines: `Type "a"` shows `a`, `Enter` shows
  `enter`, `Down 3` shows `↓  ↓  ↓`, `Type "jjjjjjjj"` shows `j ×8`, and a typed
  command shows as typed. Never write the keys by hand.
- Every key after `Show` needs a caption above it; `timeline.py` refuses a tape
  where one doesn't.
- Write the caption for the viewer, in the app's words: what the key does, or
  what the screen now shows. "its advisories", not "press a".
- Ctrl keys are not paired with the key log yet. Keep them in the hidden setup.

## Pace

- `Sleep` after every key that changes the screen, longer after a busy one:
  about 1.5s for a cursor move, 2.5s for a new panel or a popup, 3s or more for
  text worth reading. `validate.py` lists a subtitle shown under 0.8s.
- `Set PlaybackSpeed 0.8` gives the viewer time to read.
- VHS's video doesn't run at real time, so a take's length differs from the
  sum of its sleeps; that's fine, the marker carries the timing.

## Size

- Record at 1920x940 and leave the 140px band below for the subtitles; the
  final is 1920x1080.
- VHS's rows are about 1.37 times the font size, its columns about 0.6. Work out
  the app's columns and rows before picking a font: a layout that changes with
  width (a sidebar that moves, columns that drop) only shows if the size is
  right. tmux's status row takes one row.
- A smaller window for a narrow-screen scene: record that tape at a smaller
  `Width` and the same `Height`; `render.py` centers it on the wider take.
- A README scales the video down. Font 22 at 1920 wide stays readable there.

## Hidden setup

Keep the template's `Hide` block as it is: it starts `script` to log the keys,
starts `marker.py`, runs the app's shell inside tmux, and clears the screen.
Change only the file names to the tape's own name: `demo.keys`, `demo.timing`
and `/vhs/demo.tape` become `<name>.keys`, `<name>.timing`, `/vhs/<name>.tape`.
