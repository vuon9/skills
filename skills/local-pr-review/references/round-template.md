# Round file template

Only for runs with a big change. Copy this shape into `round-<NN>.md` and include only the big items, not every thread.

```markdown
# Local review round <NN> (<branch>)

- Hunk session: <session id> (<title>)
- Head: <short sha at round start>
- Date: <YYYY-MM-DD>
- Label: <your author label>

## Changes

### 1. <short title of the change>

- From: agent (opencode) | human
- Where: src/app.py:42 (new), plus other files touched

> <the note, quoted, trimmed to the point>

**Why it is big.** Which rule made it big (design decision, public interface, behavior, spans files).

**Options.** Only when it was a decide item.
1. <option> (Recommended). <why>
2. <option>. <tradeoff>

**Decision.** What was decided and by whom.

**Change.** What changed, file by file, and how it was verified.
```
