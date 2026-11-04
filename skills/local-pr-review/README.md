# local-pr-review

Works through review notes in a live [Hunk](https://github.com/modem-dev/hunk)
session. The notes can come from you or from other agents, for example when
you run several harnesses to review the same diff. Built as a fast, lean loop
between you and agents: the Hunk threads are the record.

## When it applies

Use when a Hunk review session has notes to address, or run
`/local-pr-review`.

## What it produces

- Easy notes get confirmed, fixed, or dismissed with proof right away.
- Unclear notes get a clarifying question back to the commenter.
- Hard notes get framed as a short picture plus options with a recommended
  one, posted in Hunk and listed in chat for you to decide.
- Every thread gets a reply inside Hunk, tagged `[confirmed]`, `[fixed]`,
  `[dismissed]`, `[noted]`, `[clarify]`, or `[decide]`.
- A short chat summary. No doc by default: a round file at
  `.pr-feedback/local-<branch>/round-<NN>.md` (kept out of git) is written
  only when a run makes a big change, such as a design decision or a public
  interface change.

Fixes stay in the working tree. Needs Hunk running in your terminal. It uses
`hunk-review` for anything beyond basic note commands, loaded at most once per
session. For GitHub PR comments, use `github-pr-review`.
