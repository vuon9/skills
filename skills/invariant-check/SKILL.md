---
name: invariant-check
description: "Use when a rule the code must never break needs more than tests, such as a race, a retry, a double charge, or a state that should be impossible, or when code covered by an existing invariant check changed without the check being rerun. Sets up a formal check of the rule, reruns it, or brings it back in line with the code, and decides which from the checks already in the repo. Use for /invariant-check."
disable-model-invocation: true
---

# Invariant check

A test checks the cases that someone thought to write. A formal check covers every case in a stated scope: every order of steps in a model, every input up to a bound, or every input. An invariant is a rule the code promises to keep, such as "stock never goes below zero" or "a customer is charged at most once per order".

Each check lives in the repo as a project skill named `verify-<area>`. The next agent that changes the covered code loads that skill and reruns the check. This skill sets checks up, and brings them back in line with the code when changes skipped them.

```
/invariant-check [new | recheck] [what]
```

`what` is a rule, an area, a bug, or a piece of code, in any words. `new` and `recheck` force a path. With `what`, Match on code finds the check. Without it, Pick the check does.

## Find the existing checks

Do this first, on every run, with or without a mode word.

1. List the project skills that this skill created: the ones whose frontmatter has `created-by: invariant-check` under `metadata`, in the repo's skill folders (`.claude/skills/` in Claude Code).
2. From each one, read its Coverage: the rules, the files and functions, the last confirmed commit, and the run command. When a check has no Coverage section, or its last confirmed commit is not in the current branch's history (`git merge-base --is-ancestor <commit> HEAD` fails, as after a squash merge or a rebase), use the last commit that changed the check's folder instead. Say so in the report.
3. For each one, see whether its covered code changed since the last confirmed commit: `git log <commit>..HEAD` on the covered files, following renames.

## Pick the check

When `what` is missing, with or without `recheck`:

- This conversation already set up or ran a check: use the latest one, and say which.
- Otherwise, and the repo has checks: show them, each with its area, its rule in one plain sentence, its last confirmed commit, and whether its covered code changed since. List the changed ones first. Then ask the user to pick: recheck one or more of them, recheck all of them, set up a new check for something else, or just talk it through. Use the harness's question tool when it has one, and plain text otherwise. Do nothing until the user picks.
- The repo has no checks: say so, then choose the target from the code with `references/setup.md`.

## Match on code, not on words

The same check can be asked for in different words: "stock reservation", "reserve stock", and "negative stock" can all mean one check. Wording drifts. The code that a check covers does not.

1. Resolve `what` to code: the files and functions that keep or break the rule. When `what` is a rule, find the code that writes the state the rule is about. A check whose area or rule reads like `what` is a lead: follow it to its covered code, and confirm it there. When `what` points clearly at specific code, go on without asking. When it is too vague to point at specific code, such as a whole subsystem or a word that fits several unrelated places, ask the user one short question that offers your best readings, and go on with the answer.
2. Compare that code with the Coverage of each check. A renamed, moved, or split function is still the same code. Follow it with `git log --follow` or by searching for its body.
3. Decide:
   - Exactly one check covers this code and this rule: use it, and say which.
   - More than one check overlaps, or a check covers only part of the code: list the candidates and what each covers, and ask the user which ones. Never pick by name alone.
   - One check covers this code, and the rule is new: with `new`, add the rule to that check with `references/setup.md`. Otherwise ask the user whether to recheck that check as it is or add the rule to it. One area has one check skill, never two.
   - No check covers any of the code: say so, with the list of checks you compared against. With `new`, set one up. Otherwise ask the user whether to set up a new check for it.

`new` still runs the match, so that it extends a check rather than writing a second skill for code that a check already covers.

## Route

For each check that was picked or matched:

- Nothing changed in the covered code since the last confirmed commit: run the check as its skill says, report the result, and stop.
- The covered code changed, or `recheck` was given: follow `references/recheck.md`.
- A new check, or a new rule on an existing check: follow `references/setup.md`.

## The check skill

Every check skill uses this shape. The `created-by` marker lets the next run find it, and the Coverage lets it match a request to it:

```markdown
---
name: verify-<area>
description: Use when changing <the covered code, in this repo's words>, or before merging a change to it. Checks that <the rule, in one plain sentence> with <tool>.
metadata:
  created-by: invariant-check
---

# Verify <area>

<The rule, in one plain sentence. The harm when it breaks, in one plain sentence.>

## Coverage

- Rule: <the rule> (`<property name in the model or harness>`)
- Code: `<path>`: `<function>`, `<function>`
- Tool and bounds: <tool and version, the bounds, the assumptions>
- Last confirmed: `<commit>`
- Run: `<one command>`

## Run

<How to run the check, how to tell a real bug from a modeling error, and how to update the check when a change to the promise is intended. When the check is a TLA+ model, read every result with the statechart skill.>

## Findings

<Each open bug the check reports on the current code, as steps in the code's words, or "none".>
```

`<area>` is a short noun from this repo, such as `stock-reservation`. Keep the model, its config, and any harness in the same folder as the check skill, so that one folder holds the whole check. Fill every placeholder with the real value. Move "Last confirmed" forward only after you confirm that the verification describes the code at the new commit.

## Hand off

Tell the user, in plain words, which path ran and why: the checks you found, the match you made, and for each check the outcome, what it covers, and how to run it. When no check covered the request, name the checks you compared it against.
