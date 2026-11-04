# sidequest

Dig into one question without derailing the main chat. `/sidequest` forks the
current conversation into a Ghostty split beside your pane and leaves a
drafted deep-dive prompt in its input box. You edit it and send it when you
are ready, so nothing runs until you do.

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

## Requirements

- Claude Code (for `--fork-session`) or pi (for `--fork`).
- Ghostty 1.3+ on macOS, and the `use-ghostty` skill installed next to this one.
- `jq`.

## Relationship to built-ins

- `/fork <prompt>` copies the chat into a background session you check in agent view (Claude Code).
- `/branch` switches this terminal into a copy.
- `/subtask <task>` runs a forked subagent and returns its result here.
- `/btw` answers one side question with no tools.

`/sidequest` is for a live, interactive copy side by side with the main chat.
