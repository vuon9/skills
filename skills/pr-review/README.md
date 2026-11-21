# pr-review

Handles code review feedback wherever it is: on a GitHub pull request, or on
your machine before a PR exists. It replaces `github-pr-review` and
`local-pr-review`.

## Use it with a prompt

- `/pr-review` -> looks for feedback and works on it. A PR with new comments
  comes first, then notes in a live Hunk session. When nothing is waiting, it
  asks whether you want a review with an agent, a review with you in Hunk, or
  nothing.
- `/pr-review do it with devin` -> Devin reviews the local diff, and the agent
  fixes and answers what it finds.
- `/pr-review do it local` -> the same, with the default reviewer: Devin when
  it is available, otherwise a fresh subagent.
- `/pr-review start a hunk session for me` -> opens Hunk on this branch's diff
  in a pane beside you, in Rex or Ghostty.
- `/pr-review follow and answer my feedback on hunk` -> answers your Hunk
  notes, and waits for new ones.

## What it does with a finding

- Checks the claim against the code first.
- Fixes an easy one right away, or dismisses it with proof.
- Frames a hard one as a short picture plus options with a recommended one,
  and asks all of those in one batch.
- Answers every thread. On GitHub it replies to and resolves agent threads,
  and drafts answers to people for you to post.

## What it writes

- On GitHub, a round file at `.pr-feedback/pr-<N>/round-<NN>.md` in the main
  worktree, kept out of git, and one commit and one push per round.
- Locally, only the fixes, left in the working tree. A round file is written
  only when a round makes a big change.

## Needs

- Python 3.
- GitHub: the GitHub CLI (`gh`), signed in.
- Local: [Hunk](https://github.com/modem-dev/hunk) for a review with you. A
  review with an agent works without it.
- Optional: the `use-devin` skill and the `devin` CLI, for Devin as the
  reviewer.

See `SKILL.md` for the full contract.
