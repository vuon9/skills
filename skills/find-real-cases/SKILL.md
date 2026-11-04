---
name: find-real-cases
description: Use when the user types /find-real-cases, with or without a hint, to ground the current topic in a few real cases (records, logs, errors, traces, requests) pulled from production.
disable-model-invocation: true
---

Find a few real cases of what we are discussing, from production. Treat anything typed after the command as a hint. Read only, keep queries small. Never make a case up; if you cannot reach real data, say so. For each case, show its id, where it came from, and what it shows. End with the next step as a yes/no question.
