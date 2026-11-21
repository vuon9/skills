---
name: sidequest
description: "Use when the user types /sidequest, with or without a question, to dig into one question in a forked copy of this conversation. Opens the fork in a split beside the current pane, in Ghostty or Rex, and sends a drafted deep-dive prompt there, so the dig starts at once. When the user asks to edit the prompt first, it is left unsent in the input box."
disable-model-invocation: true
---

# Sidequest

Open a forked copy of this conversation in a split beside the current pane, paste a drafted prompt into its input box, and send it, so the dig starts without waiting for the user.

When the user asks to see the prompt first, with a word such as "draft" or "let me edit", leave it unsent in the input box for them to edit and send.

## 1. Pick the question

The question follows the command: `$ARGUMENTS` in Claude Code, the appended request in pi. When it is empty, take the open question from the last few turns and say it in one line.

## 2. Fill in the script

One script below does the whole job, in your session's working directory: detect the terminal app, read the harness, draft the prompt, find this pane, open the fork, paste the draft, and send it. Run it as a single shell call, because the steps share variables.

Replace three placeholders:

- `send=1`. Make it `send=0` only when the user asked to edit the prompt first.

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
  dir=$PWD
else
  sid=${CLAUDE_CODE_SESSION_ID:-${CLAUDE_SESSION_ID:-}}
  f=$(ls -t ~/.claude/projects/*/"$sid".jsonl | head -1)
  if [ -z "$sid" ] || [ -z "$f" ]; then
    printf 'no transcript found for session id "%s"; give the draft to the user in the reply instead\n' "$sid"
    exit 1
  fi
  parent_name=$(jq -r 'select(.type == "agent-name") | .agentName' "$f" | tail -1)
  # claude looks a session up under the folder it started in, and the shell
  # may have moved since.
  dir=$(jq -rn 'first(inputs | .cwd // empty)' "$f")
  fork=(claude --resume "$sid" --fork-session)
  ready='shift\+tab to cycle|\? for shortcuts'
fi

# 1 sends the draft once it is pasted. 0 leaves it in the input box for the user.
send=1

draft=$(cat <<'EOF'
Sidequest: <the question, sharpened>

Context: <one or two lines: why it came up, what we already know or tried>
Go deep on this question only. Read code, docs, and logs as needed. Do not edit files; if a change is needed, make your own worktree first.
EOF
)
# The main chat's name goes into the draft so the fork knows where to send its
# summary. An unnamed Claude Code session is addressed by its id.
main_chat=${parent_name:-${sid:-$(basename "$PWD")}}
draft="$draft
When done, follow step 6 of the sidequest skill: ask me whether to send your summary to the main chat \"$main_chat\" or to keep digging here."

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
    new=$("$G" split "$panes" right --cwd "$dir" --wait-after --env "PATH=$PATH" --cmd "$(printf '%q ' "${fork[@]}")")
  else
    new=$("$G" split "$panes" right --cwd "$dir" --input "$(printf '%q ' "${fork[@]}")"$'\n')
  fi
  if ! "$G" wait "$new" "$ready" --timeout 60 >/dev/null; then
    printf 'the fork did not reach its input box, read it and hand the draft to the user:\n'
    "$G" read "$new" --tail 20
    exit 1
  fi
  "$G" send "$new" "$draft"
  sleep 2
  if [ "$send" = 1 ]; then
    "$G" key "$new" enter
    sleep 2
  fi
  "$G" read "$new" --tail 12
else
  # REX_SESSION and REX_BLOCK name the pane this process started in. After a Rex
  # restart, or in a background session, the server no longer has them, so
  # split the focused block of the one live session instead.
  rs=${REX_SESSION:-}
  anchor=(-b "${REX_BLOCK:-}")
  if [ -z "$rs" ] || [ -z "${REX_BLOCK:-}" ] || ! "$R" block inspect -s "$rs" "$REX_BLOCK" >/dev/null 2>&1; then
    live=$("$R" session list --json 2>/dev/null | jq -r '.sessions[]?.session_id')
    if [ "$(printf '%s' "$live" | grep -c .)" -ne 1 ]; then
      printf 'this pane is not in a live Rex session and no single session is left to pick, ask the user which one:\n'
      "$R" session list 2>&1
      exit 1
    fi
    rs=$live
    anchor=()
  fi
  split=$("$R" split -s "$rs" "${anchor[@]}" --split=right --cwd "$dir" --json -- "${fork[@]}" 2>&1) || {
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
    title=$("$R" block call -s "$rs" -b "$new" title 2>/dev/null | jq -r '.title // empty' 2>/dev/null)
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
    "$R" capture -s "$rs" -b "$new" --trim 2>&1 | tail -20
    exit 1
  fi
  # The paste markers below only work when the app asked for bracketed paste.
  # A pane that did not ask would show them as literal text.
  paste=$("$R" block call -s "$rs" -b "$new" modes 2>/dev/null | jq -r '.modes[]? | select(.name == "bracketed_paste") | .set' 2>/dev/null)
  if [ "$paste" = false ]; then
    printf 'the fork did not enable bracketed paste, so the draft cannot be pasted unsent; hand it to the user in the reply:\n'
    exit 1
  fi
  printf '\033[200~%s\033[201~' "$draft" | "$R" send -s "$rs" -b "$new"
  sleep 2
  if [ "$send" = 1 ]; then
    "$R" send-key -s "$rs" -b "$new" enter
    sleep 2
  fi
  "$R" capture -s "$rs" -b "$new" --trim 2>&1 | tail -12
fi
```

## 4. Check what it opened

The script exits non-zero in six cases worth a reply, not a retry loop.

- **No transcript for the session id.** Say which id it read, and give the draft in your reply.
- **No live Rex session to pick.** The pane's own session is gone and Rex has none or several. Show the list it printed and ask which session to split, then run the script again with `rs` set to that id.
- **No Ghostty or Rex terminal.** Say which app it found, and give the draft in your reply so the user can paste it into a fork by hand.
- **No single pane matched.** The user has more than one terminal holding this project, or the session has no name yet. Ask which pane to use, then run the script again with that id in place of `$panes`.
- **The fork never reached its input box.** Read the pane it printed. A startup dialog may be open. Leave it for the user, and give them the draft in your reply instead.
- **The split failed.** Rex prints the reason, or returns JSON with no `block_ids`. Report it and hand over the draft.

Otherwise read what the pane printed.

- **With `send=1`,** the fork should be working on the prompt, and its input box should be empty. If the draft is still sitting in the box, the enter did not land. Press it once more: `"$G" key <pane> enter` in Ghostty, `rex send-key -s <session> -b <block> enter` in Rex. A `[Pasted text #N]` chip in Claude Code sends the whole draft, so leave it.
- **With `send=0`,** Claude Code collapses a long paste into a `[Pasted text #N]` chip. When you see one, send the same draft again, which expands it into editable text. pi takes the whole draft the first time. Do not press enter in that pane.

## 5. Report

One line: the question, and that the side chat is working on it in the new split. With `send=0`, say that the draft is waiting there for the user to edit and send.

## 6. In the fork, when the dig is done

This step is for the forked copy, not the session that ran the script. The draft's last line sends you here.

Give your findings in the side chat first. Then ask the user one question with two choices, using the question tool when the harness has one:

- **Send the summary to the main chat.** Only on this answer, send a short summary to the session the draft names. In Claude Code, list the peer sessions, find that name, and send with the session message tool. The first line says it is the sidequest's summary and names the question. Then say in the side chat that it was sent.
- **Keep digging here.** Send nothing. Carry on in the side chat, and ask the same question again at the next natural stop.

Never send to the main chat without that yes, and never tell the user to copy the summary across by hand. When the main chat is not listed, or the harness has no way to message another session (pi), say so and put the summary in your reply.
