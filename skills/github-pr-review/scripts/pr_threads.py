#!/usr/bin/env python3
"""PR review feedback helper for the github-pr-review skill.

Usage:
  pr_threads.py open-round [PR]            Print the next round file path and PR facts as JSON.
  pr_threads.py fetch [PR]                 Print unhandled review items as JSON.
  pr_threads.py reply THREAD_ID BODY_FILE  Reply on a review thread.
  pr_threads.py resolve THREAD_ID          Resolve a review thread.

PR defaults to the pull request of the current branch. Round files live in
<main worktree>/.pr-feedback/pr-<N>/round-<NN>.md, excluded from git.
Set PR_FEEDBACK_AGENTS to a comma-separated list of extra logins to treat as
agents (for agents that post through a personal account).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROUND_RE = re.compile(r"^round-(\d+)\.md$")
NODE_ID_RE = re.compile(r"\b(?:PRRT|PRRC|PRR|IC)_[A-Za-z0-9_-]+")

PR_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  viewer { login }
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number url headRefOid
      reviewThreads(first: 100) {
        nodes {
          id isResolved isOutdated path line
          comments(first: 50) {
            nodes { id url body createdAt author { login __typename } }
          }
        }
      }
      reviews(first: 100) {
        nodes { id url body createdAt author { login __typename } }
      }
      comments(first: 100) {
        nodes { id url body createdAt author { login __typename } }
      }
    }
  }
}
"""

REPLY_MUTATION = """
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url }
  }
}
"""

RESOLVE_MUTATION = """
mutation($thread: ID!) {
  resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
}
"""


def next_round(pr_dir: Path) -> int:
    if not pr_dir.is_dir():
        return 1
    numbers = [int(m.group(1)) for p in pr_dir.iterdir() if (m := ROUND_RE.match(p.name))]
    return max(numbers, default=0) + 1


def seen_ids(pr_dir: Path) -> set:
    ids = set()
    for path in sorted(pr_dir.glob("round-*.md")):
        ids.update(NODE_ID_RE.findall(path.read_text(encoding="utf-8")))
    return ids


def is_agent(author, extra=frozenset()) -> bool:
    if not author:
        return False
    login = author.get("login", "")
    return author.get("__typename") == "Bot" or login.endswith("[bot]") or login in extra


def _login(node):
    return (node.get("author") or {}).get("login", "")


def _comment(node):
    return {"id": node["id"], "author": _login(node), "body": node["body"], "createdAt": node["createdAt"]}


def pending_items(pr: dict, viewer: str, seen: set, extra=frozenset()) -> list:
    items = []
    for t in pr["reviewThreads"]["nodes"]:
        comments = t["comments"]["nodes"]
        if t["isResolved"] or not comments or _login(comments[-1]) == viewer:
            continue
        ids = [t["id"]] + [c["id"] for c in comments]
        if set(ids) <= seen:
            continue
        items.append({
            "kind": "thread",
            "ids": ids,
            "thread_id": t["id"],
            "url": comments[0]["url"],
            "path": t["path"],
            "line": t["line"],
            "outdated": t["isOutdated"],
            "author": _login(comments[0]),
            "agent": is_agent(comments[0].get("author"), extra),
            "comments": [_comment(c) for c in comments],
        })
    for kind, key in (("review", "reviews"), ("comment", "comments")):
        for node in pr[key]["nodes"]:
            if not node["body"].strip() or _login(node) == viewer or node["id"] in seen:
                continue
            items.append({
                "kind": kind,
                "ids": [node["id"]],
                "url": node["url"],
                "author": _login(node),
                "agent": is_agent(node.get("author"), extra),
                "comments": [_comment(node)],
            })
    return items


def run(*args) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    return json.loads(run(*args))["data"]


def pr_number(arg):
    return int(arg) if arg else int(run("gh", "pr", "view", "--json", "number", "-q", ".number"))


def pr_dir(number: int) -> Path:
    common = Path(run("git", "rev-parse", "--path-format=absolute", "--git-common-dir"))
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
    if "/.pr-feedback/" not in lines:
        exclude.write_text("\n".join(lines + ["/.pr-feedback/"]) + "\n", encoding="utf-8")
    return common.parent / ".pr-feedback" / f"pr-{number}"


def fetch_pr(number: int):
    owner, repo = run("gh", "repo", "view", "--json", "owner,name", "-q", '.owner.login + " " + .name').split()
    data = graphql(PR_QUERY, owner=owner, repo=repo, number=number)
    return data["viewer"]["login"], data["repository"]["pullRequest"]


def main(argv):
    if not argv:
        sys.exit(__doc__)
    command, rest = argv[0], argv[1:]
    if command == "open-round":
        number = pr_number(rest[0] if rest else None)
        directory = pr_dir(number)
        directory.mkdir(parents=True, exist_ok=True)
        n = next_round(directory)
        _, pr = fetch_pr(number)
        print(json.dumps({
            "pr": number,
            "url": pr["url"],
            "head": pr["headRefOid"],
            "round": n,
            "path": str(directory / f"round-{n:02d}.md"),
            "previous": [str(p) for p in sorted(directory.glob("round-*.md"))],
        }, indent=2))
    elif command == "fetch":
        number = pr_number(rest[0] if rest else None)
        extra = {s.strip() for s in os.environ.get("PR_FEEDBACK_AGENTS", "").split(",") if s.strip()}
        viewer, pr = fetch_pr(number)
        print(json.dumps(pending_items(pr, viewer, seen_ids(pr_dir(number)), extra), indent=2))
    elif command == "reply":
        body = Path(rest[1]).read_text(encoding="utf-8")
        print(graphql(REPLY_MUTATION, thread=rest[0], body=body)["addPullRequestReviewThreadReply"]["comment"]["url"])
    elif command == "resolve":
        graphql(RESOLVE_MUTATION, thread=rest[0])
        print(f"resolved {rest[0]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
