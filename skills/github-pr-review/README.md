# github-pr-review

Works through a pull request's review comments, from agents like GitHub
Copilot, Claude, OpenCode, or CodeRabbit, and from people. Each run is a
numbered round, since a PR often gets reviewed again after the code changes.

## When it applies

Use when a PR has review comments to handle, or you want to go through,
answer, or resolve PR feedback.

## What it produces

- A round file at `.pr-feedback/pr-<N>/round-<NN>.md` in the main worktree,
  kept out of git. It records each comment, the reasoning, the decision, and
  the answer.
- Easy comments get fixed (or dismissed with proof) right away.
- Hard comments get framed as a short picture plus options with a
  recommended one, then asked in one batch.
- Agent threads get a reply and are resolved. Human threads get a drafted
  answer in the round file for you to post yourself.

Needs the GitHub CLI (`gh`) signed in. See `SKILL.md` for the full contract.
