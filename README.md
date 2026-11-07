# skills

Agent skills by Vuong. They work in any harness that reads `SKILL.md` folders, such as Claude Code, OpenCode, and pi.

## Install

```bash
npx skills add -g vuon9/skills
```

The `skills` CLI asks which skills and agents to install. To install one skill:

```bash
npx skills add -g vuon9/skills --skill diagnosing-bugs
```

## Skills

| Skill | Use it for | Needs |
|---|---|---|
| [apple-ship](skills/apple-ship) | Building, signing, notarizing, and releasing iOS and macOS apps | macOS with Xcode; `gh` for the release workflows |
| [bro](skills/bro) | Restating the last message in plain language | Nothing extra |
| [diagnosing-bugs](skills/diagnosing-bugs) | A diagnosis loop for hard bugs and performance regressions | Nothing extra |
| [find-real-cases](skills/find-real-cases) | Grounding a topic in a few real cases | Read access to your production data (logs, errors, database), through MCP servers or CLIs |
| [find-state-machine](skills/find-state-machine) | Finding the state machines an app encodes implicitly | Nothing extra |
| [github-pr-review](skills/github-pr-review) | Working through review comments on a GitHub PR, one at a time | `gh` (signed in), Python 3 |
| [how](skills/how) | Explaining how a subsystem works, with evidence from the code | A harness with subagents |
| [invariant-check](skills/invariant-check) | Checking a rule tests can't cover (races, retries, double charges) with TLA+ | `statechart` skill, for TLA+ checks |
| [local-pr-review](skills/local-pr-review) | Answering notes in a live Hunk review session | [Hunk](https://github.com/modem-dev/hunk), Python 3; the `hunk-review` skill (ships with Hunk) for less common commands |
| [sidequest](skills/sidequest) | Digging into one question in a forked session | `use-ghostty` skill, Ghostty 1.3+ on macOS, `jq`, Claude Code or pi |
| [statechart](skills/statechart) | Drawing a TLA+ model as a statechart and the path to each broken rule | Node 22.18+ (or Bun 1.1.5+, Deno 2+), [mise](https://mise.jdx.dev) to fetch TLC and Java on first run |
| [teach](skills/teach) | Teaching a body of work plainly, at the person's pace | The `how` and `why` skills, plus `unslop` |
| [unslop](skills/unslop) | Removing AI tells from any writing | Nothing extra |
| [use-ghostty](skills/use-ghostty) | Reading and driving other Ghostty panes, tabs, and windows | Ghostty 1.3+ on macOS |
| [use-siyuan](skills/use-siyuan) | Driving SiYuan notes from the `siyuan` CLI: notebooks, documents, blocks, search, export, sync | The `siyuan` CLI and a workspace |
| [walk-me](skills/walk-me) | Working through questions or open decisions one item at a time | A harness with subagents; optional `how` and `why` skills from [pstack](https://github.com/cursor/plugins/tree/main/pstack) |
| [where-are-we](skills/where-are-we) | A recap of a session's goal, progress, and drift | `jq`, Claude Code or pi |
| [why](skills/why) | Investigating why a change was made or a design was picked | Optional source access: git history, tracker, docs, chat, observability, analytics |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Credits

Skills based on other people's work keep their copyright lines in the root `LICENSE`:

- [diagnosing-bugs](skills/diagnosing-bugs) is based on `diagnosing-bugs` from [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock.
- [invariant-check](skills/invariant-check) merges `create-formal-verification-skill` and `maintain-formal-verification-skill` from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan.
- [statechart](skills/statechart) is based on `statechart` from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan, edited so agents can load it.
- `bro`, `teach`, `how`, `unslop`, and `why` are based on skills from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan. `bro`, `teach`, and `unslop` are unchanged; `how` and `why` have Cursor-specific wording normalized.

`find-state-machine` uses a prompt posted by [Steve Ruiz](https://x.com/steveruizok/status/2116552016218710389) on 31 October 2026.

## License

MIT. Skills based on other authors' work keep their copyright lines in the root `LICENSE`, and their sources are named in Credits.
