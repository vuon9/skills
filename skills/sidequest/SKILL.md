---
name: sidequest
description: "Use when the user types /sidequest, with or without a question, to dig into one question in a forked copy of this conversation. Opens the fork in a split beside the current pane, in Ghostty or Rex, with a drafted deep-dive prompt in its input box for the user to edit and send."
disable-model-invocation: true
---

# Sidequest

Open a forked copy of this conversation in a split beside the current pane, with a drafted prompt waiting in its input box. The user edits it and sends it. You never send it.

## 1. Pick the question

The question follows the command: `$ARGUMENTS` in Claude Code, the appended request in pi. When it is empty, take the open question from the last few turns and say it in one line.

## 2. Fill in the script

One script below does the whole job, in your session's working directory: detect the terminal app, read the harness, draft the prompt, find this pane, open the fork, and paste the draft unsent. Run it as a single shell call, because the steps share variables.

Replace two placeholders:

- `<the question, sharpened>` and the `Context:` line in the draft.
- `<topic>`, three to six words naming the question, with no quotes in it.

The draft stays short because the fork already has the whole conversation.

## 3. Run it

```bash
# The app you are running in decides how the pane gets driven. Ghostty goes
# through the use-ghostty skill's script. Rex goes through its own `rex`
# command, which already knows this session and pane from the environment.
G=${SIDEQUEST_GHOSTTY:-$HOME/.agents/skills/use-ghostty/scripts/ghostty.js}
if [ -n "${REX_BIN_DIR:-}" ]; then R="$REX_BIN_DIR/rex"; else R=$(command -v rex || printf rex); fi

case "${TERM_PROGRAM:-}" in
  ghostty) app=ghostty ;;
  rex) app=rex ;;
  *) if [ -n "${REX_BLOCK:-}" ]; then app=rex; else app=unknown; fi ;;
esac

if [ "$app" = unknown ]; then
  printf 'no Ghostty or Rex terminal here (TERM_PROGRAM=%s); give the draft to the user in the reply instead\n' "${TERM_PROGRAM:-unset}"
  exit 1
fi

if [ -n "${PI_SESSION_FILE:-}" ]; then
  fork=(pi --fork "$PI_SESSION_FILE")
  parent_name=$(jq -r 'select(.type == "session_info") | .name // empty' "$PI_SESSION_FILE" | tail -1)
  parent_title="π - ${parent_name:-$(basename "$PWD")}"
  ready='escape interrupt|\([a-z0-9._-]+\) [^ ]+ •'
else
  sid=$CLAUDE_SESSION_ID
  f=$(ls -t ~/.claude/projects/*/"$sid".jsonl | head -1)
  parent_name=$(jq -r 'select(.type == "agent-name") | .agentName' "$f" | tail -1)
  fork=(claude --resume "$sid" --fork-session)
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
fork+=(--name "$forkname")

if [ "$app" = ghostty ]; then
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
    new=$("$G" split "$panes" right --cwd "$PWD" --wait-after --env "PATH=$PATH" --cmd "$(printf '%q ' "${fork[@]}")")
  else
    new=$("$G" split "$panes" right --cwd "$PWD" --input "$(printf '%q ' "${fork[@]}")"$'\n')
  fi
  if ! "$G" wait "$new" "$ready" --timeout 60 >/dev/null; then
    printf 'the fork did not reach its input box, read it and hand the draft to the user:\n'
    "$G" read "$new" --tail 20
    exit 1
  fi
  "$G" send "$new" "$draft"
  sleep 2
  "$G" read "$new" --tail 12
else
  if [ -z "${REX_SESSION:-}" ] || [ -z "${REX_BLOCK:-}" ]; then
    printf 'REX_SESSION or REX_BLOCK is missing; give the draft to the user in the reply instead\n'
    exit 1
  fi
  split=$("$R" split -s "$REX_SESSION" -b "$REX_BLOCK" --split=right --cwd "$PWD" --json -- "${fork[@]}" 2>&1) || {
    printf 'the split failed, read the message and hand the draft to the user:\n%s\n' "$split"
    exit 1
  }
  new=$(printf '%s' "$split" | jq -er '.block_ids[0]') || {
    printf 'the split returned no block id, read it and hand the draft to the user:\n%s\n' "$split"
    exit 1
  }
  # Pi and Claude Code put their session name in the terminal title once the
  # input box is up, so read the title off the block. Grepping the screen is not
  # safe here: the forked conversation repeats the words the screen markers use.
  title_ready=
  for _ in $(seq 1 60); do
    title=$("$R" block call -s "$REX_SESSION" -b "$new" title 2>/dev/null | jq -r '.title // empty' 2>/dev/null)
    if [ -n "${PI_SESSION_FILE:-}" ]; then
      [ "${title#π - }" != "$title" ] && title_ready=1 && break
    elif [ -n "$parent_name" ] && [ "${title#*"$parent_name"}" != "$title" ]; then
      title_ready=1
      break
    fi
    sleep 1
  done
  if [ -z "$title_ready" ]; then
    printf 'the fork did not reach its input box, read it and hand the draft to the user:\n'
    "$R" capture -s "$REX_SESSION" -b "$new" --trim 2>&1 | tail -20
    exit 1
  fi
  # The paste markers below only work when the app asked for bracketed paste.
  # A pane that did not ask would show them as literal text.
  paste=$("$R" block call -s "$REX_SESSION" -b "$new" modes 2>/dev/null | jq -r '.modes[]? | select(.name == "bracketed_paste") | .set' 2>/dev/null)
  if [ "$paste" = false ]; then
    printf 'the fork did not enable bracketed paste, so the draft cannot be pasted unsent; hand it to the user in the reply:\n'
    exit 1
  fi
  printf '\033[200~%s\033[201~' "$draft" | "$R" send -s "$REX_SESSION" -b "$new"
  sleep 2
  "$R" capture -s "$REX_SESSION" -b "$new" --trim 2>&1 | tail -12
fi
```

## 4. Check what it opened

The script exits non-zero in four cases worth a reply, not a retry loop.

- **No Ghostty or Rex terminal.** Say which app it found, and give the draft in your reply so the user can paste it into a fork by hand.
- **No single pane matched.** The user has more than one terminal holding this project, or the session has no name yet. Ask which pane to use, then run the script again with that id in place of `$panes`.
- **The fork never reached its input box.** Read the pane it printed. A startup dialog may be open. Leave it for the user, and give them the draft in your reply instead.
- **The split failed.** Rex prints the reason, or returns JSON with no `block_ids`. Report it and hand over the draft.

Otherwise read the printed input box. Claude Code collapses a long paste into a `[Pasted text #N]` chip; when you see one, send the same draft again, which expands it into editable text. pi takes the whole draft the first time. Never press enter in that pane.

## 5. Report

One line: the question, and that the draft is waiting in the new split for the user to edit and send.
