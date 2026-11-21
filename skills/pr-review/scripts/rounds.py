"""Round files, shared by the GitHub and Hunk helpers of the pr-review skill.

Round files live in <main worktree>/.pr-feedback/<name>/round-<NN>.md, excluded from git.
"""

import re
import subprocess
from pathlib import Path

ROUND_RE = re.compile(r"^round-(\d+)\.md$")


def run(*args) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def next_round(directory: Path) -> int:
    if not directory.is_dir():
        return 1
    numbers = [int(m.group(1)) for p in directory.iterdir() if (m := ROUND_RE.match(p.name))]
    return max(numbers, default=0) + 1


def feedback_dir(name: str) -> Path:
    """The folder for one PR's or one branch's round files, kept out of git."""
    common = Path(run("git", "rev-parse", "--path-format=absolute", "--git-common-dir"))
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
    if "/.pr-feedback/" not in lines:
        exclude.write_text("\n".join(lines + ["/.pr-feedback/"]) + "\n", encoding="utf-8")
    return common.parent / ".pr-feedback" / name


def round_facts(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    number = next_round(directory)
    return {
        "round": number,
        "path": str(directory / f"round-{number:02d}.md"),
        "previous": [str(p) for p in sorted(directory.glob("round-*.md"))],
    }
