#!/usr/bin/env python3
"""Pull the conversation out of a session's transcript, for the where-are-we skill.

Usage:
  extract_transcript.py [SESSION_ID]

Most of a transcript is tool output. This writes only the conversation to a
temp file: one numbered turn per user message, the agent's text, and tool calls
collapsed to a count. It prints the line count, every user turn cut to 200
characters, and `OUT=<file>` last.

SESSION_ID defaults to this session's id, from the environment: pi's when
`PI_SESSION_FILE` is set, otherwise Claude Code's. Claude Code keeps
transcripts in ~/.claude/projects/*/<id>.jsonl and pi in
~/.pi/agent/sessions/*/*<id>*.jsonl.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

NOISE = re.compile(r"<(task-notification|local-command|system-reminder)")
COMMAND = re.compile(r"<command-name>/?([^<]*)</command-name>")
COMMAND_ARGS = re.compile(r"<command-args>([^<]*)</command-args>")
PI_SKILL = re.compile(r'<skill name="([^"]*)"')


def text_of(content, joiner="\n") -> str:
    """The text of a message whose content is a string or a list of blocks."""
    if isinstance(content, str):
        return content
    return joiner.join(block["text"] for block in content if block.get("type") == "text")


def claude_events(entries):
    """(kind, text) for each part of a Claude Code transcript worth reading."""
    for entry in entries:
        if entry.get("type") not in ("user", "assistant") or entry.get("isMeta") or entry.get("isSidechain"):
            continue
        content = entry["message"]["content"]
        if entry.get("isCompactSummary"):
            yield "summary", text_of(content, " ")
        elif entry["type"] == "user":
            text = text_of(content).lstrip()
            if not text or NOISE.match(text):
                continue
            command = COMMAND.search(text)
            if command:
                args = COMMAND_ARGS.search(text)
                text = f"/{command.group(1)} {args.group(1) if args else ''}"
            yield "user", f"[{entry['timestamp'][:16]}]: {text}"
        else:
            for block in content:
                if block.get("type") == "text":
                    yield "agent", block["text"]
                elif block.get("type") == "tool_use":
                    yield "tool", ""


def pi_events(entries):
    """(kind, text) for each part of a pi transcript worth reading."""
    for entry in entries:
        if entry.get("type") in ("compaction", "branch_summary"):
            yield "summary", entry["summary"]
        elif entry.get("type") == "message":
            message = entry["message"]
            if message["role"] == "user":
                text = text_of(message["content"]).lstrip()
                if not text:
                    continue
                if text.startswith("<skill ") and "</skill>" in text:
                    rest = text.split("</skill>")[-1].strip()
                    text = f"/{PI_SKILL.search(text).group(1)} {rest}".rstrip()
                yield "user", f"[{entry['timestamp'][:16]}]: {text}"
            elif message["role"] == "assistant":
                for block in message["content"]:
                    if block.get("type") == "text":
                        yield "agent", block["text"]
                    elif block.get("type") == "toolCall":
                        yield "tool", ""


def number(events) -> str:
    """The extract: numbered user turns, agent text, and tool calls as counts."""
    out, tools, turn = [], 0, 0
    for kind, text in events:
        if kind == "tool":
            tools += 1
            continue
        if tools:
            out.append(f"  ({tools} tool calls)\n")
            tools = 0
        if kind == "user":
            turn += 1
            out.append(f"\n[turn {turn}] USER {text}\n")
        elif kind == "summary":
            out.append(f"\nsummary: {text}\n")
        else:
            out.append(f"agent: {text}\n")
    if tools:
        out.append(f"  ({tools} tool calls)\n")
    return "".join(out)


def newest(paths):
    return max(paths, key=lambda path: path.stat().st_mtime, default=None)


def main(argv):
    in_pi = bool(os.environ.get("PI_SESSION_FILE"))
    own = os.environ.get("PI_SESSION_ID") if in_pi else os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    session = argv[0] if argv else own
    if not session:
        sys.exit("no session id: pass one, or run inside Claude Code or pi")
    if in_pi:
        path = newest((Path.home() / ".pi" / "agent" / "sessions").glob(f"*/*{session}*.jsonl"))
    else:
        path = newest((Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl"))
    if not path:
        sys.exit(f"no transcript found for session {session}")
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    extract = number((pi_events if in_pi else claude_events)(entries))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as out:
        out.write(extract)
    print(len(extract.splitlines()))
    for line in extract.splitlines():
        if line.startswith("[turn "):
            print(line[:200])
    print(f"OUT={out.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
