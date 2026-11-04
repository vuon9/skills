---
name: local-pr-review
description: "Use when a live Hunk review session has notes to address, from the user or from other agents reviewing in other harnesses, or when asked to run /local-pr-review, go through Hunk notes, or answer review notes locally. Works one note thread at a time, fixes easy ones, frames hard ones as options with a recommendation, and replies to every thread inside Hunk. Lean by default: writes a numbered round file only when a round makes a big change."
---

# Local PR Review

Address review notes in a live Hunk session. The notes come from the user or from other agents (the user may run several harnesses to review the same diff). Everything is local, so reply to every thread directly in Hunk: confirm, fix, dismiss, clarify, or put a decision to the user.

This is the fast loop between the user and agents. The Hunk thread is the record. A normal run writes nothing to disk except the fixes. Write a round file only when the run makes a big change (see Round files).

The helper script is `scripts/hunk_notes.py` (run it with `python3`). `SELECTOR` is `--repo <path>` or a Hunk session id, default `--repo .`.

## Hunk CLI

`hunk-review` is the full guide to the Hunk CLI. This skill needs only the commands below, so do not load `hunk-review` for them. Load it only for something not listed here (navigate, highlight, STML markup, an error message not covered below), and at most once per session: if its content is already in your context from earlier in this session, use that copy instead of loading it again.

```bash
hunk session list --json
hunk session comment list SELECTOR --type all --json
printf '%s' "$BATCH_JSON" | hunk session comment apply SELECTOR --stdin --focus --json
hunk session comment add SELECTOR --reply-to NOTE_ID --summary "..." --rationale "..." --author LABEL
hunk session comment add SELECTOR --file PATH --new-line N --summary "..." --author LABEL
```

- A reply batch is `{"comments":[{"replyTo":"<note id>","summary":"...","rationale":"...","author":"LABEL"}]}`. Hunk validates the whole batch before writing any of it.
- `rationale` renders under the summary in the same note. Put options and longer reasoning there.
- Agent notes are hidden in Hunk by default. `--focus` lands the user on the first reply; mention the agent-notes toggle in your report.
- "No active Hunk sessions" means ask the user to open Hunk. "Multiple active sessions match" means pass the session id from `hunk session list`.
- Hunk has no resolve state. A thread counts as handled once your reply is its last note.

## Your label

Pick one author label for this harness and use it on every note, for example `claude-code`, `opencode`, `codex`, or `pi`. Add a suffix if two instances of the same harness address notes at once. The label is how `fetch` tells your notes from the user's and other agents', so never change it mid-review.

## Steps

1. **Fetch what is waiting on you.**
   Run `hunk_notes.py fetch --me LABEL [SELECTOR]`. It returns note threads, grouped by root, whose last note is not yours. `from` is `human` or `agent`. `reply_to` is the note to reply to. Nothing waiting? Say so in one line and stop.
2. **Go through threads one by one.**
   Read the code at `where` and the whole thread. Check the claim against the code before believing it. Then pick a class:
   - `confirm`: the note is right and needs no change, or it is a question with a clear answer. Answer it.
   - `fix`: the note is right. Change the code.
   - `dismiss`: false positive, intentional, or out of scope. Needs concrete proof (file and line, test, or doc).
   - `clarify`: you cannot tell what the note means. Ask the commenter a specific question in the thread.
   - `decide`: needs the user's call.
   - `noted`: nothing to act on (praise, a summary). Acknowledge it in one line.
3. **Decide: easy-to-go or frame it.**
   Easy-to-go means one obvious right answer, local, low risk. Do it now and verify it (run the relevant test).
   Frame it as `decide` when any of these hold:
   - more than one reasonable fix
   - a product, UX, or API tradeoff
   - it touches auth, permissions, payments, data migrations, or public interfaces
   - the fix reaches beyond the note's scope
   - you disagree with the user
   - another agent pushes back on your earlier answer in the same thread. Do not argue a second time. Hand it to the user.
   Framing means a short **Picture** (what the code does now, what the note claims, what is at stake) and 2 to 4 **Options**, one marked `(Recommended)` with the reason. Continue with the next thread. Do not block on it.
4. **Reply in Hunk.**
   Reply to every thread, including `noted` ones, so the thread stops waiting on you. Post all replies as one `comment apply` batch with `--focus`, each `replyTo` set to the thread's `reply_to`. Start each summary with its tag so the thread reads at a glance:
   - `[confirmed]`, `[fixed]`, `[dismissed]`, `[noted]`: closes the thread. A fix cites the file and line it changed. A dismiss cites the proof.
   - `[clarify]`: the question for the commenter.
   - `[decide]`: the question for the user, with the Picture and Options in `rationale` and the recommended one first.
   Keep summaries short and plain, and run `unslop` on them.
5. **Report briefly.**
   In chat: a count per tag, the files you changed, and the open `decide` items, numbered, each with its recommended option. No per-thread recap; the replies are in Hunk. The user can answer in chat or by replying in Hunk. An answer in chat: apply it and reply in the thread. An answer in Hunk: the next run picks it up.
6. **Write the round file, only if big.**
   If the run made a big change (see Round files), write it now. Otherwise skip this step.

## Round files

Only for a run with a big change. A change is big when any of these hold:
- the user settled a `decide` item that changes design or behavior
- a fix changes a public interface, a data shape, or behavior a user would notice
- a fix spans several files or reaches beyond the note's lines
- the user asks for the doc

Run `hunk_notes.py open-round [SELECTOR]`. It prints the next sequential round file path (`<main worktree>/.pr-feedback/local-<branch>/round-<NN>.md`, excluded from version control) and the earlier rounds. Write it with `references/round-template.md`, covering only the big items. Never commit round files.

## Rules

- Do not commit. Fixes stay in the working tree unless the user asks for a commit.
- Do not reload the Hunk session to show fixes unless you know the command it was launched with. Hunk does not report it. Tell the user the fixes are in instead.
- Never delete or clear notes. Notes are the user's and other agents' record.
- Do not dismiss a security or data-integrity note without concrete proof it cannot happen.
- For review comments on a GitHub pull request, use `github-pr-review` instead.
