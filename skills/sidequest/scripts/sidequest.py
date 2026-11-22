#!/usr/bin/env python3
"""Open a forked copy of this conversation in a split, and send it a drafted prompt.

Usage:
  sidequest.py --question TEXT --context TEXT --topic TEXT [--draft-only]
               [--rex-session ID] [--pane ID]

Run it in the session's working directory. It detects the terminal app
(Ghostty or Rex) and the harness (Claude Code or pi), finds this pane, opens
the fork in a split to its right, waits for the fork's input box, pastes the
draft, and presses enter. It ends by printing the fork's screen and a
`sidequest pane:` line with the ids of the new pane.

  --draft-only    paste the draft and leave it unsent, for the user to edit
  --rex-session   split this Rex session, when the script could not pick one
  --pane          split this Ghostty pane, when the script could not pick one

Every failure prints why, and the draft when it was not delivered, and exits 1.
Ghostty is driven through the use-ghostty skill's script, or the one named in
SIDEQUEST_GHOSTTY. Rex is driven through `rex`, from REX_BIN_DIR when set.
"""

import argparse
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

PAUSE = float(os.environ.get("SIDEQUEST_PAUSE", "2"))
POLLS = int(os.environ.get("SIDEQUEST_POLLS", "60"))


class Stop(Exception):
    """A failure worth a reply, not a retry."""


def detect_app(env):
    program = env.get("TERM_PROGRAM", "")
    if program in ("ghostty", "rex"):
        return program
    return "rex" if env.get("REX_BLOCK") else None


def draft_text(question, context, main_chat):
    return (
        f"Sidequest: {question}\n\n"
        f"Context: {context}\n"
        "Go deep on this question only. Read code, docs, and logs as needed. "
        "Do not edit files; if a change is needed, make your own worktree first.\n"
        "When done, follow step 6 of the sidequest skill: ask me whether to send your summary "
        f'to the main chat "{main_chat}" or to keep digging here.'
    )


def fork_name(topic, parent):
    return f"sq: {topic} ({parent})"


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def harness(env, cwd):
    """How to fork this session, and what its pane looks like once the fork is ready."""
    if env.get("PI_SESSION_FILE"):
        names = [e.get("name") for e in read_jsonl(env["PI_SESSION_FILE"]) if e.get("type") == "session_info" and e.get("name")]
        name = names[-1] if names else ""
        return {
            "pi": True, "name": name, "session_id": "", "dir": cwd,
            "fork": ["pi", "--fork", env["PI_SESSION_FILE"]],
            "ready": r"escape interrupt|\([a-z0-9._-]+\) [^ ]+ •",
        }
    sid = env.get("CLAUDE_CODE_SESSION_ID") or env.get("CLAUDE_SESSION_ID") or ""
    files = glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", f"{sid}.jsonl")) if sid else []
    if not files:
        raise Stop(f'no transcript found for session id "{sid}"; give the draft to the user in the reply instead')
    entries = read_jsonl(max(files, key=os.path.getmtime))
    names = [e.get("agentName") for e in entries if e.get("type") == "agent-name" and e.get("agentName")]
    # claude looks a session up under the folder it started in, and the shell may have moved since.
    started_in = next((e["cwd"] for e in entries if e.get("cwd")), cwd)
    return {
        "pi": False, "name": names[-1] if names else "", "session_id": sid, "dir": started_in,
        "fork": ["claude", "--resume", sid, "--fork-session"],
        "ready": r"shift\+tab to cycle|\? for shortcuts",
    }


def run(*args, stdin=None):
    return subprocess.run(args, input=stdin, capture_output=True, text=True)


CHIP = "[Pasted text #"


def tail(text, lines):
    return "\n".join(text.rstrip("\n").splitlines()[-lines:])


def via_ghostty(script, h, name, draft, send, pane, env):
    if not pane:
        rows = [line.split("\t") for line in run(script, "ls").stdout.splitlines() if line.strip()]
        titled = [row for row in rows if len(row) >= 4]
        if h["pi"]:
            title = f"π - {h['name'] or os.path.basename(h['dir'])}"
            panes = [row[0] for row in titled if row[3] == title]
        else:
            panes = [row[0] for row in titled if h["name"] and h["name"] in row[3]]
        if len(panes) != 1:
            raise Stop("no single pane matched, ask the user which one:\n" + "\n".join(panes))
        pane = panes[0]
    fork = shlex.join([*h["fork"], "--name", name])
    if h["pi"]:
        # pi runs --cmd through a login shell that reads no rc files, so PATH goes along.
        split = run(script, "split", pane, "right", "--cwd", h["dir"], "--wait-after", "--env", f"PATH={env.get('PATH', '')}", "--cmd", fork)
    else:
        split = run(script, "split", pane, "right", "--cwd", h["dir"], "--input", fork + "\n")
    new = split.stdout.strip()
    if split.returncode or not new:
        raise Stop(f"the split failed, read the message and hand the draft to the user:\n{split.stdout}{split.stderr}")
    if run(script, "wait", new, h["ready"], "--timeout", "60").returncode:
        raise Stop("the fork did not reach its input box, read it and hand the draft to the user:\n" + run(script, "read", new, "--tail", "20").stdout)
    run(script, "send", new, draft)
    time.sleep(PAUSE)
    if send:
        run(script, "key", new, "enter")
        time.sleep(PAUSE)
    elif CHIP in run(script, "read", new, "--tail", "12").stdout:
        # Claude Code shows a long paste as a chip. A second paste opens it into text the user can edit.
        run(script, "send", new, draft)
        time.sleep(PAUSE)
    print(run(script, "read", new, "--tail", "12").stdout.rstrip("\n"))
    print(f"sidequest pane: {new}")


def via_rex(rex, h, name, draft, send, session, env):
    # REX_SESSION and REX_BLOCK name the pane this process started in. After a Rex
    # restart, or in a background session, the server no longer has them, so the
    # focused block of the one live session is split instead.
    anchor = []
    if not session:
        session, block = env.get("REX_SESSION", ""), env.get("REX_BLOCK", "")
        if session and block and run(rex, "block", "inspect", "-s", session, block).returncode == 0:
            anchor = ["-b", block]
        else:
            listed = run(rex, "session", "list", "--json").stdout
            live = [s["session_id"] for s in json.loads(listed or "{}").get("sessions", [])]
            if len(live) != 1:
                shown = run(rex, "session", "list")
                raise Stop(
                    "this pane is not in a live Rex session and no single session is left to pick, ask the user which one:\n"
                    + shown.stdout + shown.stderr
                )
            session = live[0]
    split = run(rex, "split", "-s", session, *anchor, "--split=right", "--cwd", h["dir"], "--json", "--", *h["fork"], "--name", name)
    if split.returncode:
        raise Stop(f"the split failed, read the message and hand the draft to the user:\n{split.stdout}{split.stderr}")
    try:
        new = json.loads(split.stdout)["block_ids"][0]
    except (ValueError, KeyError, IndexError):
        raise Stop(f"the split returned no block id, read it and hand the draft to the user:\n{split.stdout}")
    # Pi and Claude Code put their session name in the terminal title once the input
    # box is up, so the title is read off the block. Searching the screen is not safe
    # here: the forked conversation repeats the words the screen markers use.
    expected = "π - " if h["pi"] else (h["name"] or name)
    for _ in range(POLLS):
        reply = run(rex, "block", "call", "-s", session, "-b", new, "title").stdout
        try:
            title = json.loads(reply).get("title") or ""
        except ValueError:
            title = ""
        if title.startswith(expected) if h["pi"] else expected in title:
            break
        time.sleep(PAUSE / 2)
    else:
        screen = run(rex, "capture", "-s", session, "-b", new, "--trim")
        raise Stop("the fork did not reach its input box, read it and hand the draft to the user:\n" + tail(screen.stdout + screen.stderr, 20))
    # The paste markers only work when the app asked for bracketed paste. A pane
    # that did not ask would show them as literal text.
    try:
        modes = json.loads(run(rex, "block", "call", "-s", session, "-b", new, "modes").stdout).get("modes", [])
    except ValueError:
        modes = []
    if any(mode.get("name") == "bracketed_paste" and mode.get("set") is False for mode in modes):
        raise Stop("the fork did not enable bracketed paste, so the draft cannot be pasted unsent; hand it to the user in the reply:")
    run(rex, "send", "-s", session, "-b", new, stdin=f"\x1b[200~{draft}\x1b[201~")
    time.sleep(PAUSE)
    if send:
        run(rex, "send-key", "-s", session, "-b", new, "enter")
        time.sleep(PAUSE)
    elif CHIP in run(rex, "capture", "-s", session, "-b", new, "--trim").stdout:
        # Claude Code shows a long paste as a chip. A second paste opens it into text the user can edit.
        run(rex, "send", "-s", session, "-b", new, stdin=f"\x1b[200~{draft}\x1b[201~")
        time.sleep(PAUSE)
    screen = run(rex, "capture", "-s", session, "-b", new, "--trim")
    print(tail(screen.stdout + screen.stderr, 12))
    print(f"sidequest pane: session={session} block={new}")


def main(argv):
    parser = argparse.ArgumentParser(description="Open a forked copy of this conversation in a split, and send it a drafted prompt.")
    parser.add_argument("--question", required=True, help="the question, sharpened")
    parser.add_argument("--context", required=True, help="one or two lines: why it came up, what is already known or tried")
    parser.add_argument("--topic", required=True, help="three to six words naming the question")
    parser.add_argument("--draft-only", action="store_true", help="leave the draft unsent in the input box")
    parser.add_argument("--rex-session", help="the Rex session to split")
    parser.add_argument("--pane", help="the Ghostty pane to split")
    args = parser.parse_args(argv)

    env, cwd = os.environ, os.getcwd()
    fallback = env.get("CLAUDE_CODE_SESSION_ID") or env.get("CLAUDE_SESSION_ID") or os.path.basename(cwd)
    draft = draft_text(args.question, args.context, fallback)
    try:
        app = detect_app(env)
        if not app:
            raise Stop(f"no Ghostty or Rex terminal here (TERM_PROGRAM={env.get('TERM_PROGRAM', 'unset')}); give the draft to the user in the reply instead")
        h = harness(env, cwd)
        # The main chat's name goes into the draft so the fork knows where to send its
        # summary. An unnamed Claude Code session is addressed by its id.
        draft = draft_text(args.question, args.context, h["name"] or h["session_id"] or os.path.basename(cwd))
        name = fork_name(args.topic, h["name"] or os.path.basename(cwd))
        if app == "ghostty":
            script = env.get("SIDEQUEST_GHOSTTY") or os.path.expanduser("~/.agents/skills/use-ghostty/scripts/ghostty.js")
            via_ghostty(script, h, name, draft, not args.draft_only, args.pane, env)
        else:
            rex = os.path.join(env["REX_BIN_DIR"], "rex") if env.get("REX_BIN_DIR") else shutil.which("rex") or "rex"
            via_rex(rex, h, name, draft, not args.draft_only, args.rex_session, env)
    except Stop as stop:
        print(stop)
        print(f"\nthe draft:\n{draft}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
