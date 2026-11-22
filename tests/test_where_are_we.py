import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "where-are-we" / "scripts" / "extract_transcript.py"
sys.path.insert(0, str(SCRIPT.parent))

from extract_transcript import claude_events, number, pi_events

AT = "2026-11-22T03:15:27.000Z"


def claude_user(content, **extra):
    return {"type": "user", "timestamp": AT, "message": {"content": content}, **extra}


def claude_agent(*content):
    return {"type": "assistant", "timestamp": AT, "message": {"content": list(content)}}


def pi_message(role, content):
    return {"type": "message", "timestamp": AT, "message": {"role": role, "content": content}}


TEXT = {"type": "text", "text": "Done."}


class TestClaudeEvents(unittest.TestCase):
    def test_each_entry_becomes_the_right_event(self):
        rows = [
            {"id": "user_text", "entry": claude_user("fix the login"), "events": [("user", "[2026-11-22T03:15]: fix the login")]},
            {"id": "user_blocks", "entry": claude_user([{"type": "text", "text": "  one"}, {"type": "tool_result", "content": "x"}, {"type": "text", "text": "two"}]), "events": [("user", "[2026-11-22T03:15]: one\ntwo")]},
            {"id": "slash_command", "entry": claude_user("<command-name>/pr-review</command-name><command-args>do it local</command-args>"), "events": [("user", "[2026-11-22T03:15]: /pr-review do it local")]},
            {"id": "slash_command_no_args", "entry": claude_user("<command-message>x</command-message><command-name>/clear</command-name>"), "events": [("user", "[2026-11-22T03:15]: /clear ")]},
            {"id": "tool_result_only", "entry": claude_user([{"type": "tool_result", "content": "x"}]), "events": []},
            {"id": "task_notification", "entry": claude_user("<task-notification>done</task-notification>"), "events": []},
            {"id": "system_reminder", "entry": claude_user("<system-reminder>x</system-reminder>"), "events": []},
            {"id": "meta", "entry": claude_user("caveat", isMeta=True), "events": []},
            {"id": "sidechain", "entry": claude_user("subagent prompt", isSidechain=True), "events": []},
            {"id": "compact_summary", "entry": claude_user("We fixed the login.", isCompactSummary=True), "events": [("summary", "We fixed the login.")]},
            {"id": "agent_text_and_tools", "entry": claude_agent(TEXT, {"type": "tool_use", "name": "Bash"}, {"type": "thinking", "thinking": "hm"}), "events": [("agent", "Done."), ("tool", "")]},
            {"id": "other_type", "entry": {"type": "file-history-snapshot"}, "events": []},
        ]
        results = {row["id"]: list(claude_events([row["entry"]])) for row in rows}
        self.assertEqual(results, {row["id"]: row["events"] for row in rows})


class TestPiEvents(unittest.TestCase):
    def test_each_entry_becomes_the_right_event(self):
        skill = '<skill name="walk-me" path="/x">\nbody\n</skill>\n\n the questions  '
        rows = [
            {"id": "user_text", "entry": pi_message("user", "fix the login"), "events": [("user", "[2026-11-22T03:15]: fix the login")]},
            {"id": "user_blocks", "entry": pi_message("user", [{"type": "text", "text": "one"}, {"type": "image"}]), "events": [("user", "[2026-11-22T03:15]: one")]},
            {"id": "skill_call", "entry": pi_message("user", skill), "events": [("user", "[2026-11-22T03:15]: /walk-me the questions")]},
            {"id": "empty_user", "entry": pi_message("user", "  "), "events": []},
            {"id": "agent_text_and_tools", "entry": pi_message("assistant", [TEXT, {"type": "toolCall"}, {"type": "thinking"}]), "events": [("agent", "Done."), ("tool", "")]},
            {"id": "tool_result", "entry": pi_message("toolResult", [TEXT]), "events": []},
            {"id": "compaction", "entry": {"type": "compaction", "summary": "We fixed the login."}, "events": [("summary", "We fixed the login.")]},
            {"id": "branch_summary", "entry": {"type": "branch_summary", "summary": "A side branch."}, "events": [("summary", "A side branch.")]},
        ]
        results = {row["id"]: list(pi_events([row["entry"]])) for row in rows}
        self.assertEqual(results, {row["id"]: row["events"] for row in rows})


class TestNumber(unittest.TestCase):
    def test_turns_are_numbered_and_tool_calls_counted(self):
        events = [
            ("user", "[t]: first ask"),
            ("tool", ""), ("tool", ""),
            ("agent", "Looked around.\nUSER is a word here, not a turn."),
            ("tool", ""),
            ("summary", "Earlier work."),
            ("user", "[t]: second ask"),
            ("agent", "Done."),
            ("tool", ""),
        ]
        self.assertEqual(
            number(events),
            "\n[turn 1] USER [t]: first ask\n"
            "  (2 tool calls)\n"
            "agent: Looked around.\nUSER is a word here, not a turn.\n"
            "  (1 tool calls)\n"
            "\nsummary: Earlier work.\n"
            "\n[turn 2] USER [t]: second ask\n"
            "agent: Done.\n"
            "  (1 tool calls)\n",
        )

    def test_no_conversation_is_empty(self):
        self.assertEqual(number([]), "")


class TestCli(unittest.TestCase):
    """Runs the script the way the skill does, against a made-up home folder."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"]}

    def run_script(self, *args, **env):
        return subprocess.run([sys.executable, str(SCRIPT), *args], env={**self.env, **env}, capture_output=True, text=True)

    def write(self, path, entries):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))

    def out_file(self, stdout):
        return Path(stdout.strip().splitlines()[-1].removeprefix("OUT="))

    def test_claude_code_session_is_found_by_its_id(self):
        self.write(self.home / ".claude" / "projects" / "-work-app" / "abc123.jsonl", [claude_user("fix the login"), claude_agent(TEXT)])
        res = self.run_script(CLAUDE_CODE_SESSION_ID="abc123")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("[turn 1] USER [2026-11-22T03:15]: fix the login", res.stdout)
        self.assertEqual(self.out_file(res.stdout).read_text(), "\n[turn 1] USER [2026-11-22T03:15]: fix the login\nagent: Done.\n")

    def test_an_id_given_as_argument_wins(self):
        self.write(self.home / ".claude" / "projects" / "-work-app" / "abc123.jsonl", [claude_user("this session")])
        self.write(self.home / ".claude" / "projects" / "-work-other" / "other9.jsonl", [claude_user("the other session")])
        res = self.run_script("other9", CLAUDE_CODE_SESSION_ID="abc123")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("the other session", self.out_file(res.stdout).read_text())

    def test_pi_session_is_read_in_pi(self):
        session = self.home / ".pi" / "agent" / "sessions" / "work-app" / "2026-11-22_pi777.jsonl"
        self.write(session, [pi_message("user", "fix the login"), pi_message("assistant", [TEXT])])
        res = self.run_script(PI_SESSION_FILE=str(session), PI_SESSION_ID="pi777")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.out_file(res.stdout).read_text(), "\n[turn 1] USER [2026-11-22T03:15]: fix the login\nagent: Done.\n")

    def test_a_session_that_is_not_there_says_so(self):
        res = self.run_script(CLAUDE_CODE_SESSION_ID="nope")
        self.assertEqual(res.returncode, 1)
        self.assertIn("no transcript found for session nope", res.stderr)

    def test_a_long_turn_is_cut_in_the_list_but_whole_in_the_file(self):
        long = "x" * 500
        self.write(self.home / ".claude" / "projects" / "-work-app" / "abc123.jsonl", [claude_user(long)])
        res = self.run_script(CLAUDE_CODE_SESSION_ID="abc123")
        listed = [line for line in res.stdout.splitlines() if line.startswith("[turn 1]")]
        self.assertEqual([len(line) for line in listed], [200])
        self.assertIn(long, self.out_file(res.stdout).read_text())


if __name__ == "__main__":
    unittest.main()
