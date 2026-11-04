#!/usr/bin/env python3
"""Hunk review notes helper for the local-pr-review skill.

Usage:
  hunk_notes.py fetch --me LABEL [SELECTOR...]  Print note threads waiting on you as JSON.
  hunk_notes.py open-round [SELECTOR...]        Print the next round file path and session facts as JSON.

SELECTOR is passed to `hunk session` as is: `--repo <path>` or a session id.
It defaults to `--repo .`. A thread waits on you until your reply is its last
note. Round files, written only for big changes, live in
<main worktree>/.pr-feedback/local-<branch>/round-<NN>.md, excluded from git.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROUND_RE = re.compile(r"^round-(\d+)\.md$")


def next_round(round_dir: Path) -> int:
    if not round_dir.is_dir():
        return 1
    numbers = [int(m.group(1)) for p in round_dir.iterdir() if (m := ROUND_RE.match(p.name))]
    return max(numbers, default=0) + 1


def _where(n):
    side, span = ("new", n["newRange"]) if n.get("newRange") else ("old", n.get("oldRange") or [0])
    return f"{n['filePath']}:{span[0]} ({side})"


def pending_threads(notes: list, me: str) -> list:
    by_id = {n["noteId"]: n for n in notes}

    def root(n):
        while n.get("parentId") in by_id:
            n = by_id[n["parentId"]]
        return n["noteId"]

    threads = {}
    for n in notes:
        threads.setdefault(root(n), []).append(n)

    items = []
    for root_id, thread in threads.items():
        last = thread[-1]
        if last.get("author") == me:
            continue
        first = thread[0]
        items.append({
            "thread": root_id,
            "reply_to": last["noteId"],
            "where": _where(first),
            "from": "human" if first["source"] == "user" else "agent",
            "author": first.get("author", ""),
            "notes": [{"id": n["noteId"], "author": n.get("author", ""), "body": n["body"]} for n in thread],
        })
    return items


def run(*args) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def round_dir() -> Path:
    common = Path(run("git", "rev-parse", "--path-format=absolute", "--git-common-dir"))
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
    if "/.pr-feedback/" not in lines:
        exclude.write_text("\n".join(lines + ["/.pr-feedback/"]) + "\n", encoding="utf-8")
    branch = run("git", "rev-parse", "--abbrev-ref", "HEAD").replace("/", "-")
    return common.parent / ".pr-feedback" / f"local-{branch}"


def main(argv):
    if not argv or argv[0] not in ("open-round", "fetch"):
        sys.exit(__doc__)
    command, rest = argv[0], argv[1:]
    me = None
    if command == "fetch":
        if "--me" not in rest:
            sys.exit("fetch needs --me LABEL")
        i = rest.index("--me")
        me = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    selector = rest or ["--repo", "."]
    if command == "open-round":
        directory = round_dir()
        directory.mkdir(parents=True, exist_ok=True)
        n = next_round(directory)
        session = json.loads(run("hunk", "session", "get", *selector, "--json"))["session"]
        print(json.dumps({
            "session": session["sessionId"],
            "title": session.get("title"),
            "head": run("git", "rev-parse", "--short", "HEAD"),
            "round": n,
            "path": str(directory / f"round-{n:02d}.md"),
            "previous": [str(p) for p in sorted(directory.glob("round-*.md"))],
        }, indent=2))
    else:
        notes = json.loads(run("hunk", "session", "comment", "list", *selector, "--type", "all", "--json"))["comments"]
        print(json.dumps(pending_threads(notes, me), indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
