# skills

Agent skills by Vuong Bui. They work in any harness that reads `SKILL.md` folders, such as Claude Code, OpenCode, and pi.

## Install

```bash
npx skills add -g vuon9/skills
```

The `skills` CLI asks which skills and agents to install. To install one skill:

```bash
npx skills add -g vuon9/skills --skill diagnosing-bugs
```

## Skills

| Skill | Use it for |
|---|---|
| [apple-ship](skills/apple-ship) | Building, signing, notarizing, and releasing iOS and macOS apps |
| [diagnosing-bugs](skills/diagnosing-bugs) | A diagnosis loop for hard bugs and performance regressions |
| [find-real-cases](skills/find-real-cases) | Grounding a topic in a few real cases |
| [github-pr-review](skills/github-pr-review) | Working through review comments on a GitHub PR, one at a time |
| [invariant-check](skills/invariant-check) | Checking a rule tests can't cover (races, retries, double charges) with TLA+ |
| [local-pr-review](skills/local-pr-review) | Answering notes in a live Hunk review session |
| [sidequest](skills/sidequest) | Digging into one question in a forked session |
| [statechart](skills/statechart) | Drawing a TLA+ model as a statechart and the path to each broken rule |
| [use-ghostty](skills/use-ghostty) | Reading and driving other Ghostty panes, tabs, and windows |
| [walk-me](skills/walk-me) | Working through questions or open decisions one item at a time |
| [where-are-we](skills/where-are-we) | A recap of a session's goal, progress, and drift |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
