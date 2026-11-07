# sidequest

Dig into one question without derailing the main chat. `/sidequest` forks the
current conversation into a split beside your pane and leaves a drafted
deep-dive prompt in its input box. You edit it and send it when you are ready,
so nothing runs until you do.

## Use it with a prompt

- `/sidequest <question>` -> forks the chat and drafts a prompt for that question
- `/sidequest` -> takes the open question from the last few turns

The fork has the whole conversation and all tools. The draft asks it to stay
on the question, to explore without editing files (or to make its own
worktree if it must), and to end with a summary you can paste back.

## How it works

The skill opens a split with a forked copy of the current session, named
`sq: <topic> (<parent>)` so each sidequest stands apart in the session picker.
It waits for the input box and pastes the draft without pressing enter.

| | Claude Code | pi |
| --- | --- | --- |
| fork | `claude --resume <id> --fork-session` | `pi --fork <session file>` |
| launch | types the command into the new pane's shell | `--cmd`, with `PATH` passed through `--env` |
| pane title | carries the session name | `π - <name> - <folder>`, or `π - <folder>` while unnamed |
| paste | a long draft lands as a `[Pasted text]` chip, so it pastes twice | the whole draft lands as editable text once |

pi runs `--cmd` through a login shell that never reads your rc files, so the
skill passes `PATH` through and calls `pi` by absolute path. `--wait-after`
keeps a shell in the pane once pi exits.

## Terminal apps

The skill reads `TERM_PROGRAM` and drives whichever app it finds. It does not
guess: when neither Ghostty nor Rex is there, it hands you the draft instead.

| App | How it drives the pane |
| --- | --- |
| Ghostty | the `use-ghostty` skill's script, `scripts/ghostty.js` |
| Rex | the `rex` command, using `REX_SESSION` and `REX_BLOCK` from the environment |

Both branches split to the right, wait for the fork's input box, and paste the
draft as a bracketed paste so the app does not submit it. Ghostty's `send`
already pastes. Rex's `send` writes raw bytes, so the skill wraps the draft in
`\033[200~` and `\033[201~` itself.

## Requirements

- Claude Code (for `--fork-session`) or pi (for `--fork`).
- Ghostty 1.3+ on macOS with the `use-ghostty` skill installed next to this one,
  or Rex with its `rex` command on `PATH`.
- `jq`.

## Relationship to built-ins

- `/fork <prompt>` copies the chat into a background session you check in agent view (Claude Code).
- `/branch` switches this terminal into a copy.
- `/subtask <task>` runs a forked subagent and returns its result here.
- `/btw` answers one side question with no tools.

`/sidequest` is for a live, interactive copy side by side with the main chat.
