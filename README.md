# skills

Agent skills by Vuong. They support Claude Code and pi. Each skill is one folder with a `SKILL.md`, and this is the only README.

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

- [walk-me](skills/walk-me). Work through questions or open decisions one item at a time. Needs a harness with subagents; optional `how` and `why` from [pstack](https://github.com/cursor/plugins/tree/main/pstack).
- [find-state-machine](skills/find-state-machine). Find every implicit state machine in an app, or dig into the one behind a named flow.
- [find-real-cases](skills/find-real-cases). Ground a topic in a few real cases. Needs read access to production data (logs, errors, database), through MCP servers or CLIs.

**Debug and verify**

- [diagnosing-bugs](skills/diagnosing-bugs). A diagnosis loop for hard bugs and performance regressions.

**Review and land**

- [pr-review](skills/pr-review). Handle review feedback on a GitHub PR or on your machine: fix easy findings, frame hard ones as options, answer every thread, and get a review from Devin or another agent before a PR exists. Needs Python 3, `gh` signed in for GitHub, and [Hunk](https://github.com/modem-dev/hunk) for a review with you; the `hunk-review` skill ships with Hunk.


**Sessions**

- [sidequest](skills/sidequest). Dig into one question in a forked session. Needs Ghostty 1.3+ on macOS with the `use-ghostty` skill, or Rex. Also needs Python 3, and Claude Code or pi.
- [where-are-we](skills/where-are-we). A recap of a session's goal, progress, and drift. Needs Python 3, and Claude Code or pi.

**Tools**

- [use-ghostty](skills/use-ghostty). Read and drive other Ghostty panes, tabs, and windows. Needs Ghostty 1.3+ on macOS.

**Build and ship**

- [apple-ship](skills/apple-ship). Build, sign, notarize, and release iOS and macOS apps. Needs macOS with Xcode, and `gh` for the release workflows.
- [terminal-demo](skills/terminal-demo). Record a demo video of a terminal app, with a subtitle for each key, on a made-up machine. Needs Docker, Python 3, and ffmpeg.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Credits

Skills based on other people's work keep their copyright lines in the root `LICENSE`:

- [diagnosing-bugs](skills/diagnosing-bugs) is based on `diagnosing-bugs` from [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock.
- from [pstack](https://github.com/cursor/plugins/tree/main/pstack)
  - `how`, `why`, `teach`, `bro`, `unslop`, and `statechart` are no longer copied here. Install them from pstack. Several skills here run `unslop`, `how`, or `why`, and pstack lets only the user start those, so remove the `disable-model-invocation` line from each after installing. [vstack](https://github.com/vuon9/vstack)'s installer does that.
- [find-state-machine](skills/find-state-machine) uses a prompt posted by [Steve Ruiz](https://x.com/steveruizok/status/2116552016218710389) on 31 October 2026.

## License

MIT. Skills based on other authors' work keep their copyright lines in the root `LICENSE`, and their sources are named in Credits.
