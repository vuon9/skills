# find-real-cases

Ground the conversation in real data without typing the request out.
`/find-real-cases` pulls a few real cases of what you are discussing (records,
logs, errors, traces, requests) from production.

## Use it with a prompt

- `/find-real-cases` -> takes the topic from the conversation
- `/find-real-cases <hint>` -> narrows it, for example with an id or a time window

## What it produces

A few cases, each with its id, its source, and what it shows, then a yes/no
next step so you can reply in a word. It reads only, keeps queries small, and
says so when it cannot reach real data instead of making cases up.

See `SKILL.md` for the full contract.
