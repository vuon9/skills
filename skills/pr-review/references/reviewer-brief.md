# Reviewer brief

The request you send to the agent that reviews. Open it in the `review` state of `references/local.md`. Fill the angle brackets, and send the text between the lines.

---

Review a code change. Change nothing: no edits, no commits, no comments posted anywhere.

**The change.** In `<repo path>`, run `git diff <base>`. It shows the commits on this branch and the uncommitted work.

**What it is meant to do.** <one or two sentences, in the user's words. No claims about whether it works.>

**What to look for.** Report only what you would stake your name on:

- wrong results, and cases the code does not handle
- data loss, and writes that can leave data half done
- security: input trusted too far, missing permission checks, secrets
- races, retries, and steps that can run twice
- a test that would still pass if the code were wrong

Leave out style, naming, and anything a formatter or linter decides.

**How to answer.** Check each finding against the code before you report it. Reply with JSON only, in this shape:

```json
{"comments": [{"filePath": "src/app.py", "newLine": 42, "summary": "One sentence: what is wrong.", "rationale": "Why it is wrong, the input or order of steps that shows it, and the fix you would make."}]}
```

- `filePath` is relative to the repo root. `newLine` is a line in the new version of the file, inside the diff. Use `oldLine` for a line that was removed.
- No findings is a fine answer: `{"comments": []}`.

**Earlier rounds.** <from round 2 on: each earlier finding, with the author's answer. Otherwise delete this part.>

- Do not repeat a finding the author fixed.
- Where an answer is wrong, say so once, with the evidence.

---
