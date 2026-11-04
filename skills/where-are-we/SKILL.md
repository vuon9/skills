---
name: where-are-we
description: "Use when the user comes back to a session and asks where we are, what the goal was, whether we are still on track or got lost, or for a recap of the session so far. A fresh subagent reads the session's whole transcript from the outside and reports the session's goal, the arc of work so far, where things stand, and whether the work drifted."
context: fork
---

# Where are we

You were not in this session. Read its transcript from the outside and give the user the big picture: what the session is for, the path the work took from the first message to now, and whether it is still heading there. You have no stake in how it went, so if it got lost, say so.

The user can already see the last few messages. What they lost is the start and the middle. Spend your effort there.

## Fresh eyes

Claude Code runs this skill with `context: fork`, so the reading happens in a subagent that never saw the work. pi has no such flag.

- **In a pi session, do not read the transcript here.** Run the extraction, then hand the file to one `delegate` subagent and return its report unchanged. The transcript stays out of this session and a reader with no stake does the judging.
- **In a launched subagent, skip this section** and go straight to the transcript. You already have the fresh eyes it asks for.

## Read the transcript

The user's arguments, if any: `$ARGUMENTS` in Claude Code, the appended request in pi. When they hold another session id, set `SID=<that id>` in the block below and extract that session instead.

Most of the file is tool output. Pull out the conversation, one numbered turn per user message, with tool calls collapsed to a count. Each harness stores its transcript in its own shape and both are read into the same extract.

```bash
out=$(mktemp)
if [ -n "${PI_SESSION_FILE:-}" ]; then
  f=$(ls -t ~/.pi/agent/sessions/*/*"${SID:-$PI_SESSION_ID}"*.jsonl | head -1)
  jq -r '
    if .type == "compaction" or .type == "branch_summary" then
      "\nsummary: \(.summary)"
    elif .type == "message" then
      .timestamp[0:16] as $at
      | .message as $m
      | if $m.role == "user" then
          ($m.content | if type == "string" then . else map(select(.type == "text") | .text) | join("\n") end)
          | sub("^\\s+"; "")
          | select(. != "")
          | if startswith("<skill ") and test("</skill>") then
              ("/" + (capture("<skill name=\"(?<n>[^\"]*)\"").n) + " " + (sub("[\\s\\S]*</skill>[ \\t\\n]*"; "")))
              | sub("\\s+$"; "")
            else . end
          | "\nUSER [\($at)]: \(.)"
        elif $m.role == "assistant" then
          $m.content[]? | if .type == "text" then "agent: \(.text)" elif .type == "toolCall" then "  tool" else empty end
        else empty end
    else empty end' "$f"
else
  f=$(ls -t ~/.claude/projects/*/"${SID:-$CLAUDE_SESSION_ID}".jsonl | head -1)
  jq -r '
    select((.type == "user" or .type == "assistant") and .isMeta != true and .isSidechain != true)
    | if .isCompactSummary then "\nsummary: \(.message.content | if type == "string" then . else map(.text? // empty) | join(" ") end)"
      elif .type == "user" then
        .timestamp[0:16] as $at
        | (.message.content | if type == "string" then . else map(select(.type == "text") | .text) | join("\n") end)
        | sub("^\\s+"; "")
        | select(. != "" and (test("^<(task-notification|local-command|system-reminder)") | not))
        | if test("<command-name>") then "/" + capture("<command-name>/?(?<n>[^<]*)</command-name>").n + " " + ((capture("<command-args>(?<a>[^<]*)</command-args>") // {a: ""}).a) else . end
        | "\nUSER [\($at)]: \(.)"
      else .message.content[]? | if .type == "text" then "agent: \(.text)" elif .type == "tool_use" then "  tool" else empty end
      end' "$f"
fi | awk '
  /^  tool$/ { n++; next }
  { if (n) { print "  (" n " tool calls)"; n = 0 } if (/^USER /) printf "\n[turn %d] ", ++t; print }
  END { if (n) print "  (" n " tool calls)" }' > "$out"
wc -l "$out"; grep '^\[turn' "$out" | cut -c1-200; echo "OUT=$out"
```

The `grep` prints every user turn. That list is your table of contents. Then read the whole file from the top, in order. Do not skip ahead to the end, and do not read only the turns that look relevant. The last turn is the request for this check, so leave it out.

In pi, that read is the subagent's job:

```text
subagent({agent: "delegate", task: "Read <OUT> in full, from the top. It is one other session's transcript, already extracted: one numbered turn per user message, tool calls collapsed to a count. You were not in that session. Judge it with the `## Judge` and `## Report` sections of ~/.agents/skills/where-are-we/SKILL.md, and return only that report block. Do not edit anything."})
```

Read only this one transcript. If it holds no conversation, report that and stop. Never search other sessions' transcripts to make up for it.

## Judge

Build the picture from the whole session before you look at where it stopped.

- **Session goal.** Why this session exists, in the user's words. Usually the first real request. When a session runs through several separate asks, the goal is what they add up to, or say plainly that it has more than one.
- **Arc.** Group the turns into phases. A phase is one ask and the work it took: "set up X" (turns 1-4), "fix the bug it exposed" (turns 5-7). Give each one its outcome: done (with the result), dropped, or still open. Keep earlier phases even when they are finished. They are the part the user forgot.
- **Their changes vs. the agent's detours.** A new ask, or a "now", "instead", "also", or "forget that" from the user, starts a phase or changes one. That is not drift. Work the user never asked for is a detour: an unrelated fix, scope that grew, a rewrite of something that worked, a long side investigation.
- **Loose ends.** Things asked earlier and never finished or answered, anywhere in the session, not just at the end.
- **Signs of being lost.** The same command or error coming back, edits that undo earlier edits, a hypothesis that keeps changing with no test behind it, long runs of tool calls with no result the user would care about, the user correcting the same thing twice.
- **Where it stands.** The last concrete result (a passing test, a commit, a PR, an answer), what was in progress, and any question to the user still unanswered.

A `summary:` line is the agent's paraphrase after compaction. Use it to fill gaps, but trust the user's own words over it.

## Report

Return only this, addressed to the user, in under 25 lines:

```text
Goal: "<their words>" <one line on what the session is for, if the quote alone does not say it>

Arc:
1. <phase> (turns a-b): <outcome>
2. ...

Loose ends: <earlier asks still open, or "none">
Now: <what was in progress when the session stopped>
Waiting on you: <an unanswered question, or "nothing">
Verdict: on track | detour | lost. <one sentence, with the evidence>
Next: <the one step that moves toward the goal>
```

Quote the goal, never paraphrase it. Keep each arc line to one line, and use at most 8 phases. Merge small ones. Name a detour plainly.
