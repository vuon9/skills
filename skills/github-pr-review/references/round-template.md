# Round file template

Copy this shape into `round-<NN>.md`. One `###` block per item, in the order you handled them. Keep the `<!-- ids: ... -->` line exactly as the `ids` list from `fetch`, comma separated.

```markdown
# PR #<N> review round <NN>

- PR: <url>
- Head: <short sha at round start>
- Date: <YYYY-MM-DD>
- Previous: <round-(NN-1).md or none>

## Summary

| # | Author | Agent | Where | Class | Action |
|---|--------|-------|-------|-------|--------|
| 1 | copilot-pull-request-reviewer | yes | src/app.py:42 | fix | replied + resolved |
| 2 | alice | no | src/auth.py:10 | ask | waiting on you |

## For you

- Drafts to post: #3 (alice)
- Open questions: #2

## Items

### 1. <short title of the concern>

<!-- ids: PRRT_xxx, PRRC_yyy -->
- Author: copilot-pull-request-reviewer (agent)
- Link: <comment url>
- Where: src/app.py:42 (outdated: no)

> <the comment, quoted, trimmed to the point>

**Consideration.** What the code does at that line, whether the claim holds, and the evidence.

**Class.** fix | dismiss | ask | note. Easy-to-go: yes | no.

**Picture.** Only when framed. What the code does now, what the comment claims, what is at stake.

**Options.** Only when framed.
1. <option> (Recommended). <why>
2. <option>. <tradeoff>

**Decision.** What was decided and by whom (agent for easy-to-go, user for framed). Open items say `open`.

**Answer.** The reply text, as posted or as a draft for the user.

**Action.** replied + resolved | drafted for you | waiting on you | no reply needed
```
