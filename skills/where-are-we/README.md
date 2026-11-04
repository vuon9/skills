# where-are-we

Coming back to a long session, it is hard to tell whether you and the agent
are still on the goal or got lost on the way. `where-are-we` sends a fresh
subagent to read the session's whole transcript from the outside. It reports
the goal in your words, the arc of the work as numbered phases from the first
message to now, loose ends left earlier, where things stand, and whether the
work drifted. It zooms out on purpose: you can already see the last few
messages, so the recap spends its lines on the start and the middle.

## Use it with a prompt

- `/where-are-we` -> checks the current session
- `/where-are-we <session-id>` -> checks another session, such as one left
  open in another terminal
- "Where were we?" / "Are we still on track?" -> the agent runs it for you

## How it works

The reading happens in a context that never saw the work, on both harnesses:

| | Claude Code | pi |
| --- | --- | --- |
| fresh reader | `context: fork` in the skill frontmatter | one `delegate` subagent, handed the extracted transcript |
| transcript | `~/.claude/projects/*/<id>.jsonl` | `$PI_SESSION_FILE`, or `~/.pi/agent/sessions/*/*<id>*.jsonl` |
| compaction | `isCompactSummary` entries | `compaction` and `branch_summary` entries |

Either way the extract keeps the full history even after compaction has
squashed the live context into a summary. It writes one numbered turn per user
message, drops task notifications and system noise, collapses tool calls into a
count, and turns a pasted skill body into a single `/skill-name` line with the
request that followed it. The judging rules live in `SKILL.md`, so the subagent
reads them from there.

## Requirements

- Claude Code, for `context: fork`, or pi, for `subagent`.
- `jq`.

## TODO

- OpenCode support.
