---
name: use-ghostty
description: "Use when the user asks you to look at, read, check, or fix something in another Ghostty pane, split, tab, or window; to open, split, or close Ghostty panes or tabs; to run a command in a separate pane and watch its output; or to send keys or text to another terminal. Drives Ghostty's native AppleScript API on macOS, no tmux and no screenshots."
---

# Use Ghostty

Ghostty (1.3+ on macOS) ships an AppleScript dictionary. `scripts/ghostty.js` wraps it so you can see and drive the user's real panes by id. Every call is a plain shell command and takes well under a second.

```bash
G=scripts/ghostty.js   # resolve against this skill's folder; it is executable
$G ls                  # id  w<window>:t<tab>  flags  title  cwd
```

`ls` flags: `>` the tab is the visible one in its window, `*` the pane is focused in its tab. Ids are stable for a pane's life, and any unique prefix works (`$G read 481a`). Window numbers follow front-to-back order and change when focus moves, so target panes by id, never by `w1:t2`.

## Find the right pane first

- Identify panes by title and cwd from `ls`. Claude Code and most shells keep the title current (`✳ <session name>`, `user@host:dir`).
- **Your own pane is one of them.** It is usually the one whose title is this session's name. Never `send` or `key` into it, and never close it.
- When two panes could match, ask the user which one. Do not guess before typing into a pane.

## Read

```bash
$G read <id>                 # visible screen
$G read <id> --all --tail 200  # scrollback + screen, last 200 lines
$G wait <id> 'PASS|FAIL' --timeout 120   # poll the screen until the regex matches, prints it
```

Ghostty can only dump a pane through `write_*_file:copy`, which puts a temp path on the clipboard. The script snapshots every clipboard item and type first and restores them after, then deletes the temp file. If the user copies something during that half second, it can be lost.

## Act

```bash
$G send <id> 'make test' --enter     # types as a paste, then presses enter
$G key <id> c --mods control         # Ctrl-C; keys: enter, escape, tab, up, a, ...
$G split <id> right --cwd ~/repo --cmd 'npm run dev' --wait-after   # prints new pane id
$G tab --near <id> --cwd ~/repo      # new tab in that pane's window, prints new pane id
$G window --input $'git status\n'    # new window, initial input typed after launch
$G focus <id>
$G close <id>                        # also close-tab <id>, close-window <id>
$G action <id> <ghostty-action>      # any keybind action, e.g. clear_screen, toggle_split_zoom
```

`--cmd` replaces the shell, so the pane closes when the command exits unless `--wait-after` is set. To keep a shell after the command, use `--input $'cmd\n'` instead.

## Rules

- **Read before you type.** Run `read <id> --tail 20` and check that the pane is at the prompt you expect. A pane running Claude, a REPL, `less`, or an editor takes your text as input to that program.
- **Closing is instant.** `close`, `close-tab` and `close-window` kill running processes with no confirmation. Close only panes you created in this session, or ones the user named.
- **Verify by reading back.** After `send`, use `wait` or `read` to confirm what happened, and report what the pane showed.
- The first call may trigger a macOS Automation prompt ("allow <terminal> to control Ghostty"). The user has to accept it once.
