#!/usr/bin/env python3
"""Hunk review notes helper for the pr-review skill.

Usage:
  hunk_notes.py fetch --me LABEL [SELECTOR...]                Print note threads waiting on you as JSON.
  hunk_notes.py wait --me LABEL [--timeout S] [SELECTOR...]   Wait until a thread waits on you, then print them.
  hunk_notes.py load FILE --author LABEL [SELECTOR...]        Load a reviewer's findings into Hunk as notes.
  hunk_notes.py open-round [SELECTOR...]                      Print the next round file path and session facts as JSON.

SELECTOR is passed to `hunk session` as is: `--repo <path>` or a session id.
It defaults to `--repo .`. A thread waits on you until your reply is its last
note. `wait` gives up after S seconds (default 900) and prints an empty list.
`load` reads the reviewer's reply, which may wrap the JSON in other text.
Round files, written only for big changes, live in
<main worktree>/.pr-feedback/local-<branch>/round-<NN>.md, excluded from git.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

from rounds import feedback_dir, next_round, round_facts, run  # noqa: F401

POLL_SECONDS = 5


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


def parse_findings(text: str) -> list:
    """The findings in a reviewer's reply: `{"comments": [...]}` or a bare list.

    A reviewer often wraps the JSON in a sentence or a code fence, so the
    outermost object or list in the text is read.
    """
    spans = [(text.find(o), text.rfind(c)) for o, c in ("{}", "[]")]
    start, end = min((s for s in spans if s[0] != -1 and s[1] > s[0]), default=(-1, -1))
    if start == -1:
        raise ValueError("no JSON found in the findings")
    data = json.loads(text[start : end + 1])
    return data["comments"] if isinstance(data, dict) else data


def batch(findings: list, author: str) -> dict:
    """Hunk's `comment apply` batch for the findings, each signed by ``author``."""
    comments = []
    for index, finding in enumerate(findings, 1):
        missing = [key for key in ("filePath", "summary") if not finding.get(key)]
        if not any(key in finding for key in ("newLine", "oldLine", "hunk", "hunkNumber")):
            missing.append("newLine")
        if missing:
            raise ValueError(f"finding {index} has no {', '.join(missing)}")
        comments.append({**finding, "author": author})
    return {"comments": comments}


def take(rest: list, flag: str, default=None):
    """Remove ``flag VALUE`` from ``rest`` and return the value."""
    if flag not in rest:
        return default
    i = rest.index(flag)
    value = rest[i + 1]
    del rest[i : i + 2]
    return value


def fetch(selector: list, me: str) -> list:
    notes = json.loads(run("hunk", "session", "comment", "list", *selector, "--type", "all", "--json"))["comments"]
    return pending_threads(notes, me)


def main(argv):
    if not argv or argv[0] not in ("open-round", "fetch", "wait", "load"):
        sys.exit(__doc__)
    command, rest = argv[0], argv[1:]
    me = take(rest, "--me")
    author = take(rest, "--author")
    timeout = int(take(rest, "--timeout", 900))
    if command in ("fetch", "wait") and not me:
        sys.exit(f"{command} needs --me LABEL")
    if command == "load" and not (author and rest):
        sys.exit("load needs FILE and --author LABEL")
    findings_file = rest.pop(0) if command == "load" else None
    selector = rest or ["--repo", "."]

    if command == "open-round":
        branch = run("git", "rev-parse", "--abbrev-ref", "HEAD").replace("/", "-")
        session = json.loads(run("hunk", "session", "get", *selector, "--json"))["session"]
        print(json.dumps({
            "session": session["sessionId"],
            "title": session.get("title"),
            "head": run("git", "rev-parse", "--short", "HEAD"),
            **round_facts(feedback_dir(f"local-{branch}")),
        }, indent=2))
    elif command == "fetch":
        print(json.dumps(fetch(selector, me), indent=2))
    elif command == "wait":
        deadline = time.monotonic() + timeout
        threads = fetch(selector, me)
        while not threads and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
            threads = fetch(selector, me)
        print(json.dumps(threads, indent=2))
    else:
        try:
            payload = batch(parse_findings(Path(findings_file).read_text(encoding="utf-8")), author)
        except ValueError as error:
            sys.exit(f"{findings_file}: {error}")
        if not payload["comments"]:
            print("no findings to load")
            return
        applied = subprocess.run(
            ["hunk", "session", "comment", "apply", *selector, "--stdin", "--focus", "--json"],
            input=json.dumps(payload), check=True, capture_output=True, text=True,
        )
        print(applied.stdout.strip() or f"loaded {len(payload['comments'])} findings")


if __name__ == "__main__":
    main(sys.argv[1:])
