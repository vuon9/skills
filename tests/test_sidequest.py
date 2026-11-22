import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "sidequest" / "scripts" / "sidequest.py"
sys.path.insert(0, str(SCRIPT.parent))

from sidequest import detect_app, draft_text, fork_name

FAKE_REX = """import json, os, sys
args = sys.argv[1:]
stdin = sys.stdin.read() if args[:1] == ["send"] else ""
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"tool": "rex", "args": args, "stdin": stdin}) + "\\n")
env = os.environ.get
if args[:2] == ["block", "inspect"]:
    sys.exit(int(env("FAKE_REX_INSPECT", "0")))
if args[:2] == ["session", "list"]:
    print(env("FAKE_REX_SESSIONS", '{"sessions": [{"session_id": "session:live"}]}') if "--json" in args else "session:a\\nsession:b")
elif args[:1] == ["split"]:
    print(env("FAKE_REX_SPLIT", '{"block_ids": ["block:new"]}'))
    sys.exit(int(env("FAKE_REX_SPLIT_EXIT", "0")))
elif args[:2] == ["block", "call"] and args[-1] == "title":
    print(json.dumps({"title": env("FAKE_REX_TITLE", "")}))
elif args[:2] == ["block", "call"] and args[-1] == "modes":
    print(json.dumps({"modes": [{"name": "bracketed_paste", "set": env("FAKE_REX_PASTE", "true") == "true"}]}))
elif args[:1] == ["capture"]:
    print(env("FAKE_SCREEN", "the fork's screen"))
"""

FAKE_GHOSTTY = """import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"tool": "ghostty", "args": args, "stdin": ""}) + "\\n")
env = os.environ.get
if args[:1] == ["ls"]:
    print(env("FAKE_G_LS", ""))
elif args[:1] == ["split"]:
    print("pane-new")
elif args[:1] == ["wait"]:
    sys.exit(int(env("FAKE_G_WAIT", "0")))
elif args[:1] == ["read"]:
    print(env("FAKE_SCREEN", "the fork's screen"))
"""

SID = "abc123"
PASTE_START, PASTE_END = "\x1b[200~", "\x1b[201~"


class TestPure(unittest.TestCase):
    def test_the_terminal_app_is_read_from_the_environment(self):
        rows = [
            {"id": "ghostty", "env": {"TERM_PROGRAM": "ghostty"}, "app": "ghostty"},
            {"id": "rex", "env": {"TERM_PROGRAM": "rex"}, "app": "rex"},
            {"id": "rex_block_under_another_name", "env": {"TERM_PROGRAM": "xterm", "REX_BLOCK": "block:1"}, "app": "rex"},
            {"id": "other_terminal", "env": {"TERM_PROGRAM": "iTerm.app"}, "app": None},
            {"id": "nothing_set", "env": {}, "app": None},
        ]
        results = {row["id"]: detect_app(row["env"]) for row in rows}
        self.assertEqual(results, {row["id"]: row["app"] for row in rows})

    def test_the_draft_asks_before_reporting_back(self):
        text = draft_text("Why does the retry double-charge?", "It came up in review. We ruled out the queue.", "fix-billing")
        self.assertEqual(
            text,
            "Sidequest: Why does the retry double-charge?\n\n"
            "Context: It came up in review. We ruled out the queue.\n"
            "Go deep on this question only. Read code, docs, and logs as needed. Do not edit files; if a change is needed, make your own worktree first.\n"
            'When done, follow step 6 of the sidequest skill: ask me whether to send your summary to the main chat "fix-billing" or to keep digging here.',
        )

    def test_the_fork_is_named_after_the_topic_and_the_main_chat(self):
        self.assertEqual(fork_name('the "retry" bug', "fix-billing"), 'sq: the "retry" bug (fix-billing)')

    def test_the_skill_never_tells_the_user_to_copy_the_summary(self):
        skill = (REPO_ROOT / "skills" / "sidequest" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("paste back", skill)


class CliCase(unittest.TestCase):
    """Runs sidequest.py the way an agent does, against a fake rex and a fake Ghostty script."""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.home, self.work, bin_dir = tmp / "home", tmp / "work" / "app", tmp / "bin"
        for folder in (self.home, self.work, bin_dir):
            folder.mkdir(parents=True)
        for name, body in (("rex", FAKE_REX), ("ghostty.js", FAKE_GHOSTTY)):
            fake = bin_dir / name
            fake.write_text(f"#!{sys.executable}\n{body}")
            fake.chmod(0o755)
        self.log = tmp / "calls.jsonl"
        self.started_in = tmp / "started" / "here"
        self.env = {
            "HOME": str(self.home), "PATH": "/usr/bin:/bin", "FAKE_LOG": str(self.log),
            "REX_BIN_DIR": str(bin_dir), "SIDEQUEST_GHOSTTY": str(bin_dir / "ghostty.js"),
            "SIDEQUEST_PAUSE": "0", "SIDEQUEST_POLLS": "2",
        }

    def claude_session(self, name="fix-billing"):
        entries = [{"type": "user", "cwd": str(self.started_in)}]
        if name:
            entries += [{"type": "agent-name", "agentName": "old-name"}, {"type": "agent-name", "agentName": name}]
        path = self.home / ".claude" / "projects" / "-work-app" / f"{SID}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
        return {"CLAUDE_CODE_SESSION_ID": SID}

    def pi_session(self, name="fix-billing"):
        path = self.home / "pi-session.jsonl"
        entries = [{"type": "session_info", "name": name}] if name else [{"type": "message"}]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
        return {"PI_SESSION_FILE": str(path)}

    def run_script(self, *extra, **env):
        args = ["--question", "Why does the retry double-charge?", "--context", "It came up in review.", "--topic", 'the "retry" bug', *extra]
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.work, env={**self.env, **env}, capture_output=True, text=True)

    def calls(self, *prefix):
        lines = self.log.read_text().splitlines() if self.log.exists() else []
        calls = [json.loads(line) for line in lines]
        return [call for call in calls if call["args"][: len(prefix)] == list(prefix)]


class TestRex(CliCase):
    REX = {"TERM_PROGRAM": "rex", "REX_SESSION": "session:mine", "REX_BLOCK": "block:mine", "FAKE_REX_TITLE": "✳ fix-billing"}

    def test_claude_code_fork_is_split_beside_this_pane_and_sent(self):
        res = self.run_script(**self.REX, **self.claude_session())
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(
            self.calls("split")[0]["args"],
            ["split", "-s", "session:mine", "-b", "block:mine", "--split=right", "--cwd", str(self.started_in), "--json", "--",
             "claude", "--resume", SID, "--fork-session", "--name", 'sq: the "retry" bug (fix-billing)'],
        )
        sent = self.calls("send")[0]
        self.assertEqual(sent["args"], ["send", "-s", "session:mine", "-b", "block:new"])
        self.assertEqual(sent["stdin"], PASTE_START + self.expected_draft("fix-billing") + PASTE_END)
        self.assertEqual([call["args"] for call in self.calls("send-key")], [["send-key", "-s", "session:mine", "-b", "block:new", "enter"]])
        self.assertIn("the fork's screen", res.stdout)
        self.assertIn("sidequest pane: session=session:mine block=block:new", res.stdout)

    def expected_draft(self, main_chat):
        from sidequest import draft_text
        return draft_text("Why does the retry double-charge?", "It came up in review.", main_chat)

    def test_draft_only_pastes_and_does_not_press_enter(self):
        res = self.run_script("--draft-only", **self.REX, **self.claude_session())
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(len(self.calls("send")), 1)
        self.assertEqual(self.calls("send-key"), [])

    def test_a_draft_that_collapsed_into_a_chip_is_pasted_again_to_open_it(self):
        """Claude Code shows a long paste as a chip. A second paste turns it into text the user can edit."""
        rows = [
            {"id": "draft_only_and_a_chip", "extra": ["--draft-only"], "screen": "> [Pasted text #1 +4 lines]", "pastes": 2},
            {"id": "draft_only_and_plain_text", "extra": ["--draft-only"], "screen": "> Sidequest: Why", "pastes": 1},
            {"id": "sent_and_a_chip", "extra": [], "screen": "> [Pasted text #1 +4 lines]", "pastes": 1},
        ]
        session = self.claude_session()
        results = {}
        for row in rows:
            self.log.unlink(missing_ok=True)
            res = self.run_script(*row["extra"], **self.REX, **session, FAKE_SCREEN=row["screen"])
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            results[row["id"]] = len(self.calls("send"))
        self.assertEqual(results, {row["id"]: row["pastes"] for row in rows})

    def test_stale_pane_ids_fall_back_to_the_one_live_session(self):
        res = self.run_script(**self.REX, **self.claude_session(), FAKE_REX_INSPECT="1")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.calls("split")[0]["args"][:4], ["split", "-s", "session:live", "--split=right"])
        self.assertEqual(self.calls("send")[0]["args"], ["send", "-s", "session:live", "-b", "block:new"])

    def test_stale_pane_ids_and_two_live_sessions_ask_the_user(self):
        two = json.dumps({"sessions": [{"session_id": "session:a"}, {"session_id": "session:b"}]})
        res = self.run_script(**self.REX, **self.claude_session(), FAKE_REX_INSPECT="1", FAKE_REX_SESSIONS=two)
        self.assertEqual(res.returncode, 1)
        self.assertIn("no single session is left to pick, ask the user which one", res.stdout)
        self.assertIn("session:a\nsession:b", res.stdout)
        self.assertEqual(self.calls("split"), [])

    def test_a_session_the_user_named_is_split_without_checking_the_pane(self):
        res = self.run_script("--rex-session", "session:b", **self.REX, **self.claude_session(), FAKE_REX_INSPECT="1")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.calls("split")[0]["args"][:4], ["split", "-s", "session:b", "--split=right"])

    def test_pi_fork_is_ready_when_its_title_shows(self):
        res = self.run_script(**{**self.REX, "FAKE_REX_TITLE": "π - fix-billing - app"}, **self.pi_session())
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        split = self.calls("split")[0]["args"]
        self.assertEqual(split[split.index("--cwd") + 1], str(self.work.resolve()))
        self.assertEqual(split[split.index("--") + 1 :], ["pi", "--fork", str(self.home / "pi-session.jsonl"), "--name", 'sq: the "retry" bug (fix-billing)'])
        self.assertEqual(len(self.calls("send-key")), 1)

    def test_an_unnamed_claude_session_is_addressed_by_its_id(self):
        res = self.run_script(**{**self.REX, "FAKE_REX_TITLE": f"✳ sq: the \"retry\" bug (app)"}, **self.claude_session(name=None))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.calls("split")[0]["args"][-1], 'sq: the "retry" bug (app)')
        self.assertEqual(self.calls("send")[0]["stdin"], PASTE_START + self.expected_draft(SID) + PASTE_END)

    def test_a_fork_that_never_shows_its_input_box_is_reported(self):
        res = self.run_script(**{**self.REX, "FAKE_REX_TITLE": "zsh"}, **self.claude_session())
        self.assertEqual(res.returncode, 1)
        self.assertIn("the fork did not reach its input box", res.stdout)
        self.assertIn("the fork's screen", res.stdout)
        self.assertEqual(self.calls("send"), [])

    def test_a_pane_without_bracketed_paste_gets_nothing_pasted(self):
        res = self.run_script(**self.REX, **self.claude_session(), FAKE_REX_PASTE="false")
        self.assertEqual(res.returncode, 1)
        self.assertIn("did not enable bracketed paste", res.stdout)
        self.assertEqual(self.calls("send"), [])

    def test_a_failed_split_is_reported(self):
        rows = [
            {"id": "rex_says_no", "env": {"FAKE_REX_SPLIT": "no such session", "FAKE_REX_SPLIT_EXIT": "1"}, "message": "the split failed"},
            {"id": "no_block_id", "env": {"FAKE_REX_SPLIT": '{"block_ids": []}'}, "message": "the split returned no block id"},
        ]
        session = self.claude_session()
        for row in rows:
            with self.subTest(row["id"]):
                res = self.run_script(**self.REX, **session, **row["env"])
                self.assertEqual(res.returncode, 1)
                self.assertIn(row["message"], res.stdout)
                self.assertEqual(self.calls("send"), [])


class TestGhostty(CliCase):
    GHOSTTY = {"TERM_PROGRAM": "ghostty"}
    PANES = "p1\tw1\tt1\t✳ fix-billing\np2\tw1\tt1\tzsh"

    def test_claude_code_fork_is_typed_into_a_split_and_sent(self):
        res = self.run_script(**self.GHOSTTY, **self.claude_session(), FAKE_G_LS=self.PANES)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(
            self.calls("split")[0]["args"],
            ["split", "p1", "right", "--cwd", str(self.started_in), "--input",
             f"claude --resume {SID} --fork-session --name 'sq: the \"retry\" bug (fix-billing)'\n"],
        )
        self.assertEqual(self.calls("wait")[0]["args"], ["wait", "pane-new", r"shift\+tab to cycle|\? for shortcuts", "--timeout", "60"])
        self.assertEqual(self.calls("send")[0]["args"][:2], ["send", "pane-new"])
        self.assertIn("Sidequest: Why does the retry double-charge?", self.calls("send")[0]["args"][2])
        self.assertEqual([call["args"] for call in self.calls("key")], [["key", "pane-new", "enter"]])
        self.assertIn("sidequest pane: pane-new", res.stdout)

    def test_draft_only_does_not_press_enter(self):
        res = self.run_script("--draft-only", **self.GHOSTTY, **self.claude_session(), FAKE_G_LS=self.PANES)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.calls("key"), [])

    def test_a_draft_that_collapsed_into_a_chip_is_pasted_again_to_open_it(self):
        res = self.run_script("--draft-only", **self.GHOSTTY, **self.claude_session(), FAKE_G_LS=self.PANES, FAKE_SCREEN="> [Pasted text #1 +4 lines]")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(len(self.calls("send")), 2)

    def test_pi_fork_runs_as_the_pane_command_with_the_path_passed_through(self):
        panes = "p1\tw1\tt1\tπ - fix-billing\np2\tw1\tt1\tπ - fix-billing - other"
        res = self.run_script(**self.GHOSTTY, **self.pi_session(), FAKE_G_LS=panes)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(
            self.calls("split")[0]["args"],
            ["split", "p1", "right", "--cwd", str(self.work.resolve()), "--wait-after", "--env", "PATH=/usr/bin:/bin", "--cmd",
             f"pi --fork {self.home / 'pi-session.jsonl'} --name 'sq: the \"retry\" bug (fix-billing)'"],
        )

    def test_no_single_pane_asks_the_user(self):
        rows = [
            {"id": "two_panes_match", "panes": "p1\tw\tt\t✳ fix-billing\np2\tw\tt\t✳ fix-billing"},
            {"id": "none_match", "panes": "p1\tw\tt\tzsh"},
        ]
        session = self.claude_session()
        for row in rows:
            with self.subTest(row["id"]):
                res = self.run_script(**self.GHOSTTY, **session, FAKE_G_LS=row["panes"])
                self.assertEqual(res.returncode, 1)
                self.assertIn("no single pane matched, ask the user which one", res.stdout)
                self.assertEqual(self.calls("split"), [])

    def test_a_pane_the_user_named_is_used(self):
        res = self.run_script("--pane", "p2", **self.GHOSTTY, **self.claude_session(), FAKE_G_LS="p1\tw\tt\tzsh")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.calls("split")[0]["args"][:3], ["split", "p2", "right"])

    def test_a_fork_that_never_shows_its_input_box_is_reported(self):
        res = self.run_script(**self.GHOSTTY, **self.claude_session(), FAKE_G_LS=self.PANES, FAKE_G_WAIT="1")
        self.assertEqual(res.returncode, 1)
        self.assertIn("the fork did not reach its input box", res.stdout)
        self.assertEqual(self.calls("send"), [])


class TestNoWayIn(CliCase):
    def test_another_terminal_hands_the_draft_back(self):
        res = self.run_script(TERM_PROGRAM="iTerm.app", **self.claude_session())
        self.assertEqual(res.returncode, 1)
        self.assertIn("no Ghostty or Rex terminal here (TERM_PROGRAM=iTerm.app)", res.stdout)
        self.assertIn("Sidequest: Why does the retry double-charge?", res.stdout)
        self.assertEqual(self.calls(), [])

    def test_a_session_with_no_transcript_hands_the_draft_back(self):
        res = self.run_script(TERM_PROGRAM="rex", CLAUDE_CODE_SESSION_ID="nope")
        self.assertEqual(res.returncode, 1)
        self.assertIn('no transcript found for session id "nope"', res.stdout)
        self.assertIn("Sidequest: Why does the retry double-charge?", res.stdout)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
