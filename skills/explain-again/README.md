# explain-again

Restate the last message so it can be followed, and draw it when a picture
helps. When a message comes out dense, skips steps, or leans on terms nobody
explained, explain-again says the same thing the way one human talks to
another.

## When it applies

Use whenever the last message needs another pass. Ask for a diagram, or let it
draw one when the message is about states, a flow, or calls between parts.

## What it produces

A restatement of the last message, not a summary or a new answer. It names the
problem first, keeps the real names from the code or the UI and explains each
one, and puts back the steps the first version skipped. It may be longer than
the original.

A diagram goes in a pane beside the agent's, in the same tab, drawn with the
kitty graphics protocol. It checks the terminal first: Rex and Ghostty get a
picture, anything else gets the Mermaid text in the reply.

## Needs

- For the picture: macOS (Quick Look turns the SVG into a PNG), Node, and
  [Pele](https://pele.run) in `~/.cache/vstack/pele` (or `VSTACK_PELE_DIR`).
- In Rex: nothing else. In Ghostty: the `use-ghostty` skill to open the split.

See `SKILL.md` for the full contract.
