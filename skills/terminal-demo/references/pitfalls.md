# Pitfalls

Each of these cost at least one full take to learn.

## The story

- **Focus moves under you.** After a popup closes, after a help or history
  screen, or after opening a row, focus is often in a different panel than the
  tape assumes, so the next `h` or `j` acts on the wrong thing and every scene
  after it drifts. Probe the stretch first, and prefer jumps (`g`, `G`, a `/`
  filter) to counting rows.
- **Rows aren't where you think.** Lists sort by rules you didn't check: name,
  status, source. Find a row by filtering for it, or probe to learn the order.
- **Tabs stick.** Opening a new row often shows the tab the last one had. A
  caption about the overview needs the key that opens the overview.
- **A caption that's true in general but not on screen.** "exit code 3 means at
  risk" with no exit code visible. Show it (`; echo exit $?`) or cut the claim.
- **An action that does nothing here.** A "link it" step on a machine where the
  link already exists shows "nothing to do". Make the made-up state need the
  action, or drop the step.
- **Too long.** A walkthrough of every feature runs for minutes. One workflow,
  the UI, a filter: about a minute.

## The machine

- **The app reads more than you faked.** Read the fakeweb and fake-call logs
  after every take; a new scene reaches new endpoints.
- **A miss on screen is worse than a miss in the log.** A versions tab showing
  "404 Not Found" ruins the scene; validation fails on it for that reason.
- **Two answers where one belongs.** A fake that ignores a flag (formula and
  cask searches) returns its list twice.
- **Settings by environment.** Unset the real tokens, proxies and XDG paths in
  `env.sh`, or the app reaches the real world.

## The recording

- **tmux without UTF-8** draws every emoji and wide sign as `_`. The template
  runs `tmux -u` and `env.sh` sets `LANG=C.UTF-8`.
- **tmux's escape-time** delays `esc` by half a second. The template's
  tmux.conf sets it to 0.
- **The shell prompt** inside tmux comes from `env.sh`, which tmux runs as the
  shell's rc file. Without it the prompt is `bash-5.2#`.
- **A layout that depends on size** only appears if the app sees the right
  columns and rows. Check the app's own thresholds and VHS's row height.
- **The subtitle band, not an overlay.** Subtitles over the app cover what the
  scene shows. Record at 940 high and let the band take the rest.

## The checks

- **Timing can be perfect and the caption still wrong.** The tools prove that
  keys and subtitles line up; only the contact sheets show whether the caption
  describes the frame. Look at every one, every take.
- **Look at a final frame with the marker on.** The patch over the status row
  must hide all of it and none of the app's last line.
- **Render only validated subtitles.** `render.py` refuses a take without them.
