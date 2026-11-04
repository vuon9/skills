# diagnosing-bugs

A diagnosis loop for hard bugs and performance regressions: build a tight
feedback loop that goes red on the bug, reproduce and minimise, rank
falsifiable hypotheses, instrument one variable at a time, then fix with a
regression test and clean up.

## Use it with a prompt

- "Diagnose why the export endpoint returns 500 on large files" -> full loop
- "Debug this flaky checkout test" -> raise the reproduction rate, then narrow
- "The dashboard got slow after the last release" -> perf branch: baseline, then bisect

When the cause is already evident from the error, it says so and goes
straight to the fix and regression test.

## Relationship

Use it for hard or intermittent bugs. For questions about how or why code
works, with nothing broken, reach for an explanation skill instead.

## Source

Copied from
[mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/engineering/diagnosing-bugs).
Edited: the description starts with "Use when", the phase gate scales to the
bug, and pressure and repeated lines are removed.
