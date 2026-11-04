# use-ghostty

Let an agent see and drive your Ghostty panes: list windows, tabs and splits, read what another pane shows, type or send keys into it, and open or close splits, tabs and windows. It uses Ghostty's native AppleScript API through `osascript`, so there is no tmux, no screenshots, and no computer-use.

Requires Ghostty 1.3+ on macOS.

## Use it with a prompt

- "What's failing in my other pane?" -> `ls`, then `read <id> --all`
- "Run the tests in a split on the right and tell me when they finish" -> `split`, `send`, `wait`
- "Stop the dev server in tab 2" -> `key <id> c --mods control`
- "Close the panes you opened" -> `close <id>`

## Try it

```bash
skills/use-ghostty/scripts/ghostty.js ls
skills/use-ghostty/scripts/ghostty.js read <id-prefix> --tail 20
```

## Relationship

`SKILL.md` holds the commands and the safety rules (read before typing, never type into your own pane, closing is instant). `scripts/ghostty.js` is a single JXA script with no dependencies.
