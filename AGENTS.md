# AGENTS.md

This repo holds agent skills: one folder per skill under `skills/`, each with a `SKILL.md`, and sometimes `scripts/` and `references/`. The root `README.md` is the only README.

## Commands

```bash
python3 -m unittest discover -s tests -v
```

## Proof is a real run

A change is not done until it ran for real, and the PR says what was run and what was seen.

- **A skill:** start it in a harness, such as Claude Code or pi, on a real task, and read what the agent did. `claude -p "/<skill> ..."` in a scratch folder is enough for most skills.
- **A script:** run it on the real thing it works on: a real transcript, a real pane, a real pull request.
- **Say what you saw,** in the PR description: the command, and the output that shows it worked. Say plainly what you could not run, and why.
- **A passing test is not this proof.** A test with fakes shows the script does what you wrote. Only the real run shows that what you wrote is right.

Tests are for scripts, and only for scripts:

- **Allowed:** a test that runs a script and checks its output for an input, against fakes. It costs no tokens and runs on every PR.
- **Banned:** a test that reads a `SKILL.md` or a reference and checks that it contains certain words. It passes whether or not an agent follows the rule, and it pins sentences in place that nobody can then improve.
- **Structure is the exception.** `tests/test_skills.py` checks what a skill file is and may not hold: front matter that matches the folder, no README inside a skill, no em dash. Add to it only for that kind of rule.

## Writing skills

- `description` starts with "Use when".
- Write list items, not long paragraphs, so a rule can be added, changed, or removed alone.
- Put a script in `scripts/` as a file, with tests. Do not put a long script inline in `SKILL.md` for the agent to edit and run.
- No em dashes anywhere.
