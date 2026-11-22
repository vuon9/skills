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

## 2. Run the script

`scripts/sidequest.py` does the whole job: it detects the terminal app and the harness, drafts the prompt, finds this pane, opens the fork in a split to its right, pastes the draft, and sends it. Run it in your session's working directory.

```bash
python3 <this skill's folder>/scripts/sidequest.py \
  --question "<the question, sharpened>" \
  --context "<one or two lines: why it came up, what we already know or tried>" \
  --topic "<three to six words naming the question>"
```

- Add `--draft-only` only when the user asked to edit the prompt first. The draft is then pasted and left unsent.
- Keep the question and the context short. The fork already has the whole conversation.
- The script ends by printing the fork's screen, and a `sidequest pane:` line with the ids of the new pane.

## 3. When it stops

The script exits 1 in six cases. Each one is worth a reply, not a retry loop. It prints why, then the draft it could not deliver.

- **No transcript for the session id.** Say which id it read, and give the draft in your reply.
- **No Ghostty or Rex terminal.** Say which app it found, and give the draft in your reply so the user can paste it into a fork by hand.
- **No live Rex session to pick.** The pane's own session is gone and Rex has none or several. Show the list it printed and ask which session to split. Then run the script again with `--rex-session <id>`.
- **No single pane matched.** In Ghostty, the user has more than one terminal holding this project, or the session has no name yet. Ask which pane to use. Then run the script again with `--pane <id>`.
- **The fork never reached its input box.** Read the screen it printed. A startup dialog may be open. Leave it for the user, and give them the draft in your reply.
- **The split failed.** Rex prints the reason, or returns no block id. Report it and hand over the draft.

## 4. Check what it opened

Read the screen the script printed.

- **Sent (the default).** The fork should be working on the prompt, and its input box should be empty. If the draft is still sitting in the box, the enter did not land. Press it once more, with the ids from the `sidequest pane:` line: `rex send-key -s <session> -b <block> enter` in Rex, or the use-ghostty script's `key <pane> enter` in Ghostty. A `[Pasted text #N]` chip in Claude Code sends the whole draft, so leave it.
- **With `--draft-only`.** The draft should be in the input box as text the user can edit. Claude Code collapses a long paste into a `[Pasted text #N]` chip, and the script pastes once more to open it. pi shows the whole draft the first time. Do not press enter in that pane.

## 5. Report

One line: the question, and that the side chat is working on it in the new split. With `--draft-only`, say that the draft is waiting there for the user to edit and send.

## 6. In the fork, when the dig is done

This step is for the forked copy, not the session that ran the script. The draft's last line sends you here.

Give your findings in the side chat first. Then ask the user one question with two choices, using the question tool when the harness has one:

- **Send the summary to the main chat.** Only on this answer, send a short summary to the session the draft names. In Claude Code, list the peer sessions, find that name, and send with the session message tool. The first line says it is the sidequest's summary and names the question. Then say in the side chat that it was sent.
- **Keep digging here.** Send nothing. Carry on in the side chat, and ask the same question again at the next natural stop.

Never send to the main chat without that yes, and never tell the user to copy the summary across by hand. When the main chat is not listed, or the harness has no way to message another session (pi), say so and put the summary in your reply.
