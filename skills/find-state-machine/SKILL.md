---
name: find-state-machine
description: "Use when you want to find all of the implicit state machines in an app, or to find the one behind a named flow, model, or file and dig into it."
argument-hint: "[flow, model, or file to dig into]"
---

With nothing after the skill name:

find all of the implicit state machines in my app

When the request names one flow, model, or file, find the implicit state machine behind it and dig into that one:

- Each state, and the field, flag, or status string that holds it, with file and line.
- Each transition: what triggers it, where the code makes it, and what it checks first.
- States the code can reach but never names, and flag combinations that should be impossible.
- Transitions nothing guards, and states nothing leaves.
- The machine as a Mermaid `stateDiagram-v2`.
