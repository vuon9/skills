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

**Understand**

- [how](skills/how). Explain how a subsystem works, with evidence from the code. Needs a harness with subagents.
- [why](skills/why). Investigate why a change was made or a design was picked. Needs optional source access: git history, tracker, docs, chat, observability, analytics.
- [teach](skills/teach). Teach a body of work plainly, at the person's pace. Needs `how` and `why`, plus `unslop`.
- [walk-me](skills/walk-me). Work through questions or open decisions one item at a time. Needs a harness with subagents; optional `how` and `why` from [pstack](https://github.com/cursor/plugins/tree/main/pstack).
- [bro](skills/bro). Restate the last message in plain language.
- [find-real-cases](skills/find-real-cases). Ground a topic in a few real cases. Needs read access to production data (logs, errors, database), through MCP servers or CLIs.
- [find-state-machine](skills/find-state-machine). Find the state machines an app encodes implicitly.

**Debug and verify**

- [diagnosing-bugs](skills/diagnosing-bugs). A diagnosis loop for hard bugs and performance regressions.
- [invariant-check](skills/invariant-check). Check a rule tests can't cover (races, retries, double charges) with TLA+. Needs the `statechart` skill.
- [statechart](skills/statechart). Draw a TLA+ model as a statechart and the path to each broken rule. Needs Node 22.18+ and [mise](https://mise.jdx.dev) to fetch TLC and Java on first run.

**Review and land**

- [local-pr-review](skills/local-pr-review). Answer notes in a live Hunk review session. Needs [Hunk](https://github.com/modem-dev/hunk) and Python 3; the `hunk-review` skill ships with Hunk.
- [github-pr-review](skills/github-pr-review). Work through review comments on a GitHub PR, one at a time. Needs `gh`, signed in, and Python 3.

**Write**

- [unslop](skills/unslop). Remove AI tells from any writing.

**Sessions**

- [sidequest](skills/sidequest). Dig into one question in a forked session. Needs Ghostty 1.3+ on macOS or Rex, `jq`, and Claude Code or pi.
- [where-are-we](skills/where-are-we). A recap of a session's goal, progress, and drift. Needs `jq`, and Claude Code or pi.

**Tools**

- [use-ghostty](skills/use-ghostty). Read and drive other Ghostty panes, tabs, and windows. Needs Ghostty 1.3+ on macOS.
- [use-siyuan](skills/use-siyuan). Drive SiYuan notes from the `siyuan` CLI: notebooks, documents, blocks, search, export, sync. Needs the `siyuan` CLI and a workspace.

**Build and ship**

- [apple-ship](skills/apple-ship). Build, sign, notarize, and release iOS and macOS apps. Needs macOS with Xcode, and `gh` for the release workflows.

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
