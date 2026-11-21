#!/usr/bin/env python3
"""Where review feedback is waiting, for the pr-review skill.

Usage:
  review_state.py --me LABEL

Prints JSON: the current branch's pull request and how many of its review
items are unhandled, how many note threads wait on LABEL in this repo's live
Hunk session, and the route that follows. `pr` is null when the branch has no
pull request. `hunk` is null when no Hunk session is live for this repo.
"""

import json
import subprocess
import sys

import hunk_notes
import pr_threads


def route(pr_pending: int, hunk_pending: int) -> str:
    """`github` when the PR has feedback, else `local` when Hunk has notes, else `choose`."""
    if pr_pending:
        return "github"
    if hunk_pending:
        return "local"
    return "choose"


def pr_state():
    try:
        number = pr_threads.pr_number(None)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    viewer, pr = pr_threads.fetch_pr(number)
    pending = pr_threads.pending_items(pr, viewer, pr_threads.seen_ids(pr_threads.pr_dir(number)), pr_threads.extra_agents())
    return {"number": number, "url": pr["url"], "pending": len(pending)}


def hunk_state(me: str):
    try:
        return {"pending": len(hunk_notes.fetch(["--repo", "."], me))}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main(argv):
    if len(argv) != 2 or argv[0] != "--me":
        sys.exit(__doc__)
    pr, hunk = pr_state(), hunk_state(argv[1])
    print(json.dumps({
        "route": route(pr["pending"] if pr else 0, hunk["pending"] if hunk else 0),
        "pr": pr,
        "hunk": hunk,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
