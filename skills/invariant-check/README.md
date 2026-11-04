# invariant-check

Keep a rule your code must never break under a formal check, not just tests.
Tests check the cases someone thought of. A formal check covers every case in
a stated scope, such as every order in which two workers can run, and returns
the shortest sequence of steps that breaks the rule.

## Use it with a prompt

- `/invariant-check stock can never go negative` -> finds the code, models it,
  and either shows the steps that break the rule or confirms it holds
- `/invariant-check new a customer is charged at most once` -> adds a rule,
  extending an existing check when one already covers that code
- `/invariant-check recheck` -> rechecks the check this conversation just set
  up or ran. In a new conversation, it lists every check it created, with
  whether each one's code changed since it was last checked, and asks you to
  pick: recheck some or all, set up a new one, or talk it through
- `/invariant-check recheck stock` -> finds the checks that cover that code.
  One match runs straight away; several ask you which; none asks whether to
  set up a new one

A recheck brings a check back in line with the code after merges or
refactors, and says whether each failure is a stale model or a real bug.

One command does all of it. It finds its checks by a `created-by:
invariant-check` marker, and matches a request to them by the code they
cover, so "stock reservation" and "negative stock" find the same check.

## What it leaves behind

Each check is one folder in the repo, a `verify-<area>` skill next to its
model, with a Coverage section: the rule, the files and functions, the tool
and bounds, the run command, and the commit it was last confirmed against.
Nothing lives in the conversation, so commit the folder and any later
conversation, or a teammate, picks the check up. An agent that changes the covered
code loads that skill and reruns the check, so you only need `/invariant-check`
again for changes that skipped it.

## When not to use it

Plain CRUD, UI layout, or a bug you can already reproduce with a test. Use
`diagnosing-bugs` for those.

## Relationship

TLA+ checks are read with `statechart`, which draws the flow and the path to
each broken rule. Reach for it on a timing or ordering bug that no test
reproduces.

## Source

Merged from `create-formal-verification-skill` and
`maintain-formal-verification-skill` in
[cursor/plugins](https://github.com/cursor/plugins/tree/main/harness/pstack/claude-code/skills)
(pstack, by Lauren Tan). Edited: one skill that decides whether to set up,
rerun, or recheck; matching on covered code before anything else; a fixed
`verify-<area>` shape with a Coverage section; the Claude Code adapter link
removed.
