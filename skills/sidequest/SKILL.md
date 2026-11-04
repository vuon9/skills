---
name: sidequest
description: "Use when the user types /sidequest, with or without a question, to dig into one question in a forked copy of this conversation. Opens the fork in a Ghostty split beside the current pane, with a drafted deep-dive prompt in its input box for the user to edit and send."
disable-model-invocation: true
---

# Sidequest

Open a forked copy of this conversation in a Ghostty split, with a drafted prompt waiting in its input box. The user edits it and sends it. You never send it.

Drive Ghostty with the `use-ghostty` skill's script, `../use-ghostty/scripts/ghostty.js` from this skill's folder, usually `~/.agents/skills/use-ghostty/scripts/ghostty.js`.

## 1. Pick the question

The question follows the command: `$ARGUMENTS` in Claude Code, the appended request in pi. When it is empty, take the open question from the last few turns and say it in one line.

## 2. Fill in the script

One script below does the whole job, in your session's working directory: read the harness, draft the prompt, find this session's pane, open the fork, and paste the draft unsent. Run it as a single shell call, because the steps share variables.

Replace two placeholders:

- `<the question, sharpened>` and the `Context:` line in the draft.
- `<topic>`, three to six words naming the question, with no quotes in it.

The draft stays short because the fork already has the whole conversation.

## 3. Run it

```bash
G=${SIDEQUEST_GHOSTTY:-$HOME/.agents/skills/use-ghostty/scripts/ghostty.js}

if [ -n "${PI_SESSION_FILE:-}" ]; then
  fork_cmd="$(command -v pi) --fork \"$PI_SESSION_FILE\""
  parent_name=$(jq -r 'select(.type == "session_info") | .name // empty' "$PI_SESSION_FILE" | tail -1)
  parent_title="π - ${parent_name:-$(basename "$PWD")}"
  ready='escape interrupt|\([a-z0-9._-]+\) [^ ]+ •'
else
  sid=$CLAUDE_SESSION_ID
  f=$(ls -t ~/.claude/projects/*/"$sid".jsonl | head -1)
  parent_name=$(jq -r 'select(.type == "agent-name") | .agentName' "$f" | tail -1)
  fork_cmd="claude --resume $sid --fork-session"
  ready='shift\+tab to cycle|\? for shortcuts'
fi

draft=$(cat <<'EOF'
Sidequest: <the question, sharpened>

Context: <one or two lines: why it came up, what we already know or tried>
Go deep on this question only. Read code, docs, and logs as needed. Do not edit files; if a change is needed, make your own worktree first.
When done, end with a short summary I can paste back into the main chat.
EOF
)

forkname="sq: <topic> (${parent_name:-$(basename "$PWD")})"

if [ -n "${PI_SESSION_FILE:-}" ]; then
  panes=$("$G" ls | awk -F'\t' -v t="$parent_title" '$4 == t {print $1}')
else
  panes=$("$G" ls | awk -F'\t' -v t="$parent_name" 'length(t) && index($4, t) {print $1}')
fi
if [ "$(printf '%s' "$panes" | grep -c .)" -ne 1 ]; then
  printf 'no single pane matched, ask the user which one:\n%s\n' "$panes"
  exit 1
fi

if [ -n "${PI_SESSION_FILE:-}" ]; then
  new=$("$G" split "$panes" right --cwd "$PWD" --wait-after --env "PATH=$PATH" --cmd "$fork_cmd --name \"$forkname\"")
else
  new=$("$G" split "$panes" right --cwd "$PWD" --input "$fork_cmd --name \"$forkname\""$'\n')
fi

if ! "$G" wait "$new" "$ready" --timeout 60 >/dev/null; then
  printf 'the fork did not reach its input box, read it and hand the draft to the user:\n'
  "$G" read "$new" --tail 20
  exit 1
fi

"$G" send "$new" "$draft"
sleep 2
"$G" read "$new" --tail 12
```

## 4. Check what it opened

The script exits non-zero in two cases worth a reply, not a retry loop.

- **No single pane matched.** The user has more than one terminal holding this project, or the session has no name yet. Ask which pane to use, then run the script again with that id in place of `$panes`.
- **The fork never reached its input box.** Read the pane it printed. A startup dialog may be open. Leave it for the user, and give them the draft in your reply instead.

Otherwise read the printed input box. Claude Code collapses a long paste into a `[Pasted text #N]` chip; when you see one, send the same draft again, which expands it into editable text. pi takes the whole draft the first time. Never press enter in that pane.

## 5. Report

One line: the question, and that the draft is waiting in the new split for the user to edit and send.
