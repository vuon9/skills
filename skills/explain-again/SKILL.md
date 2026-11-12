---
name: explain-again
description: Use when the last message was unclear, too dense, or full of unexplained terms and needs restating so a reader new to the topic can follow it, with a diagram drawn in a terminal pane when a picture helps or is asked for.
disable-model-invocation: true
---

Restate your last message so a reader who has not seen this session can follow it, like one human talking to another.

- Start with which problem this is about and where things stand, then the point.
- Keep the real names from the code or the UI, and explain each one the first time: what it is and where it lives. Do not swap a real name for a simpler word you made up.
- Put back the steps you skipped: what you saw, what it means, what follows.
- Say again what each option, item, or ID refers to. Give every number the thing it counts.
- Use simple words and whole sentences. Longer is fine when it is clearer.

## Draw it

Draw a diagram when the person asks for one, or when the message is about states, a flow, or calls between parts that a picture shows better than prose. Write it as Mermaid in a `.mmd` file in a scratch folder outside the repo, then pick where it goes:

| State | Check | Next |
|---|---|---|
| detect | `TERM_PROGRAM` is `rex` and `REX_SESSION` and `REX_BLOCK` are set | rex |
| detect | `TERM_PROGRAM` is `ghostty` | ghostty |
| detect | anything else, or not macOS | text |
| rex | `rex split -s "$REX_SESSION" -b "$REX_BLOCK" --split=right --focus=false --keep-open -- python3 <skill>/scripts/draw.py <file.mmd>` | check |
| ghostty | open a split beside this one with the `use-ghostty` skill and run `python3 <skill>/scripts/draw.py <file.mmd>` in it | check |
| check | the pane shows no error text (read it with `rex capture` or `use-ghostty`) | done |
| check | the pane shows an error | text |
| text | put the Mermaid in the reply as a code block, and say why it wasn't drawn | done |

`<skill>` is this skill's folder. The pane belongs to the person's current tab, so they see the picture next to the reply. The picture itself never shows up in a text capture; ask the person to look when it matters.
