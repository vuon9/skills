---
name: github-pr-review
description: "Use when a pull request has review comments to handle, from agents (GitHub Copilot, Claude, OpenCode, CodeRabbit, any bot) or people, or when asked to go through, answer, or resolve PR feedback. Works one comment at a time, fixes easy ones, frames hard ones as options with a recommendation, records every consideration and decision in a numbered round file, then replies and resolves agent threads and drafts answers for human ones."
---

# Receive PR Feedback

Handle one review round of a pull request. A PR can get reviewed several times as the code improves, so each run is a new numbered round with its own markdown file. The round file is the record: every consideration and every decision goes there before anything is posted.

The helper script is `scripts/pr_threads.py` (run it with `python3`). `PR` defaults to the pull request of the current branch.

## Round files

- Location: `<main worktree>/.pr-feedback/pr-<N>/round-<NN>.md`, excluded from git by the script. Never commit them.
- Format: `references/round-template.md`. Follow it exactly, including the `<!-- ids: ... -->` line under each item. Those ids are how later rounds know what is already handled.
- Write each item's consideration into the file as you finish it, not at the end.

## Steps

1. **Open the round.**
   Run `pr_threads.py open-round [PR]`. It prints the round number, the file path, the head commit, and earlier round files. Read every earlier round file first, so a comment that repeats an earlier one reuses that decision. Create the round file with the template header.
2. **Fetch what is new.**
   Run `pr_threads.py fetch [PR]`. It returns unresolved threads, review bodies, and top-level comments not recorded in earlier rounds, skipping threads where you (the PR author) replied last. Each item has `agent: true|false`. Nothing new? Write "No new feedback" in the round file and stop.
3. **Go through items one by one.**
   For each item, read the code it points at (and the current version, since `outdated: true` means the line moved or changed). Check the claim against the code before believing it. Then write the consideration and pick a class:
   - `fix`: the comment is right. Change the code.
   - `dismiss`: false positive, intentional, or out of scope. Needs concrete proof (file and line, test, or doc).
   - `ask`: needs your call.
   Skip pure summaries with nothing actionable (a review overview, a CI pass report). Record them as `note` and move on.
4. **Decide: easy-to-go or frame it.**
   Easy-to-go means one obvious right answer, local, low risk. A typo, a missing guard the code clearly needs, a dead import, a dismiss with hard proof. Do it now, verify it (run the relevant test), and write the decision.
   Frame it when any of these hold:
   - more than one reasonable fix
   - a product, UX, or API tradeoff
   - it touches auth, permissions, payments, data migrations, or public interfaces
   - the fix reaches beyond the comment's scope
   - you disagree with a human reviewer
   Framing means writing a **Picture** (what the code does now, what the comment claims, what is at stake) and 2 to 4 **Options**, one marked `(Recommended)` with the reason. Then leave the Decision open and continue to the next item. Do not block on it.
5. **Ask once, in one batch.**
   After the last item, put every framed item to the user in a single message, numbered, each with its options and your recommended one. When the answers come back, write each one into that item's **Decision**, then apply it and verify. An item still unanswered stays `waiting on you` and nothing is posted for it.
6. **Push the round's fixes.**
   Invoking this skill is the ask to commit and push the round's fixes to the PR branch. Run the project's checks, then one commit (Conventional Commits, for example `fix: address review round 2`) and one push. Never force-push. No code changes? Skip this step.
7. **Answer.**
   Write every item's **Answer** into the round file first. Then act by author:
   - **Agent** (`agent: true`): post the answer and resolve. Threads use `pr_threads.py reply THREAD_ID BODY_FILE` then `pr_threads.py resolve THREAD_ID`. Top-level agent comments and review bodies cannot be resolved, so answer them together in one `gh pr comment <N> --body-file <file>` only when something in them was actionable.
   - **Human** (`agent: false`): post nothing. The Answer in the round file is a draft for the user to post and resolve by hand.
   A fix answer cites the commit (`Fixed in abc1234: ...`). A dismiss answer cites the proof. Keep answers short and plain, and run `unslop` on them.
   Record what happened in each item's **Action**: `replied + resolved`, `drafted for you`, `waiting on you`, or `no reply needed`.
8. **Close the round.**
   Fill the Summary table and the "For you" list (drafts to post, open questions). Report the round file path and those two lists to the user.

## Rules

- Never post a reply for a human reviewer. Draft only.
- Never resolve a thread whose Decision is still open.
- Do not dismiss a security or data-integrity comment without concrete proof it cannot happen.
- For notes in a live Hunk review session, use `local-pr-review` instead.
- Extra agent logins (agents that post through a personal account) go in `PR_FEEDBACK_AGENTS`, comma separated.
