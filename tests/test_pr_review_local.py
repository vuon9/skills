import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "pr-review" / "scripts"))

from hunk_notes import batch, next_round, parse_findings, pending_threads
from review_state import route


def note(nid, author, source="agent", parent=None, body="text"):
    n = {
        "noteId": nid,
        "source": source,
        "filePath": "app.py",
        "hunkIndex": 0,
        "newRange": [4, 4],
        "body": body,
        "author": author,
        "createdAt": "2026-09-23T00:00:00Z",
    }
    if parent:
        n["parentId"] = parent
    return n


class TestRounds(unittest.TestCase):
    def test_first_round_is_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(next_round(Path(tmp) / "local-main"), 1)

    def test_next_round_follows_highest_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "round-02.md").write_text("", encoding="utf-8")
            self.assertEqual(next_round(d), 3)


class TestRoute(unittest.TestCase):
    def test_feedback_on_the_pr_comes_first_then_hunk_notes(self):
        rows = [
            {"id": "pr_has_feedback", "pr": 2, "hunk": 0, "route": "github"},
            {"id": "both_have_feedback", "pr": 1, "hunk": 3, "route": "github"},
            {"id": "only_hunk_has_notes", "pr": 0, "hunk": 3, "route": "local"},
            {"id": "nothing_waiting", "pr": 0, "hunk": 0, "route": "choose"},
        ]
        results = {row["id"]: route(row["pr"], row["hunk"]) for row in rows}
        self.assertEqual(results, {row["id"]: row["route"] for row in rows})


class TestFindings(unittest.TestCase):
    FINDING = {"filePath": "app.py", "newLine": 4, "summary": "Off by one"}

    def test_findings_are_read_out_of_a_reviewer_reply(self):
        one = json.dumps({"comments": [self.FINDING]})
        rows = [
            {"id": "bare_object", "text": one, "count": 1},
            {"id": "bare_list", "text": json.dumps([self.FINDING, self.FINDING]), "count": 2},
            {"id": "in_a_code_fence", "text": f"Here are my findings:\n```json\n{one}\n```\nDone.", "count": 1},
            {"id": "no_findings", "text": 'Nothing to report. {"comments": []}', "count": 0},
        ]
        results = {row["id"]: len(parse_findings(row["text"])) for row in rows}
        self.assertEqual(results, {row["id"]: row["count"] for row in rows})

    def test_a_reply_with_no_json_is_refused(self):
        with self.assertRaises(ValueError):
            parse_findings("Looks good to me.")

    def test_each_finding_is_signed_by_the_reviewer(self):
        self.assertEqual(batch([self.FINDING], "devin"), {"comments": [{**self.FINDING, "author": "devin"}]})

    def test_a_finding_hunk_cannot_place_is_refused(self):
        rows = [
            {"id": "no_file", "finding": {"newLine": 4, "summary": "x"}, "names": "filePath"},
            {"id": "no_summary", "finding": {"filePath": "app.py", "newLine": 4}, "names": "summary"},
            {"id": "no_line", "finding": {"filePath": "app.py", "summary": "x"}, "names": "newLine"},
        ]
        for row in rows:
            with self.subTest(row["id"]):
                with self.assertRaises(ValueError) as caught:
                    batch([row["finding"]], "devin")
                self.assertIn(f"finding 1 has no {row['names']}", str(caught.exception))


FAKE_HUNK = """import json, os, sys
json.dump({"args": sys.argv[1:], "stdin": sys.stdin.read()}, open(os.environ["FAKE_HUNK_OUT"], "w"))
"""


class TestLoadCli(unittest.TestCase):
    """Runs `hunk_notes.py load` the way an agent does, against a fake hunk on PATH."""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "hunk"
        fake.write_text(f"#!{sys.executable}\n{FAKE_HUNK}")
        fake.chmod(0o755)
        self.out = tmp / "hunk-call.json"
        self.findings = tmp / "findings.txt"
        self.env = {**os.environ, "PATH": os.pathsep.join([str(bin_dir), "/usr/bin", "/bin"]), "FAKE_HUNK_OUT": str(self.out)}

    def load(self, text):
        self.findings.write_text(text)
        script = REPO_ROOT / "skills" / "pr-review" / "scripts" / "hunk_notes.py"
        return subprocess.run(
            [sys.executable, str(script), "load", str(self.findings), "--author", "devin", "--repo", "/work/app"],
            env=self.env, capture_output=True, text=True,
        )

    def test_findings_reach_hunk_as_one_signed_batch(self):
        finding = {"filePath": "app.py", "newLine": 4, "summary": "Off by one"}
        res = self.load("My findings:\n" + json.dumps({"comments": [finding]}))
        self.assertEqual(res.returncode, 0, res.stderr)
        call = json.loads(self.out.read_text())
        self.assertEqual(call["args"], ["session", "comment", "apply", "--repo", "/work/app", "--stdin", "--focus", "--json"])
        self.assertEqual(json.loads(call["stdin"]), {"comments": [{**finding, "author": "devin"}]})

    def test_no_findings_does_not_call_hunk(self):
        res = self.load('{"comments": []}')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("no findings", res.stdout)
        self.assertFalse(self.out.exists())

    def test_a_reply_that_is_not_findings_stops_before_hunk(self):
        res = self.load("Looks good to me.")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("no JSON found", res.stderr)
        self.assertFalse(self.out.exists())


class TestPendingThreads(unittest.TestCase):
    def test_other_agent_note_is_pending(self):
        items = pending_threads([note("mcp:1", "pi")], "claude-code")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["thread"], "mcp:1")
        self.assertEqual(items[0]["from"], "agent")
        self.assertEqual(items[0]["where"], "app.py:4 (new)")

    def test_human_note_is_pending_and_marked_human(self):
        items = pending_threads([note("user:1", "user", source="user")], "claude-code")
        self.assertEqual(items[0]["from"], "human")

    def test_thread_where_i_replied_last_is_skipped(self):
        notes = [note("user:1", "user", "user"), note("mcp:2", "claude-code", parent="user:1")]
        self.assertEqual(pending_threads(notes, "claude-code"), [])

    def test_reply_after_mine_reopens_thread(self):
        notes = [
            note("user:1", "user", "user"),
            note("mcp:2", "claude-code", parent="user:1"),
            note("user:3", "user", "user", parent="mcp:2"),
        ]
        items = pending_threads(notes, "claude-code")
        self.assertEqual(items[0]["reply_to"], "user:3")
        self.assertEqual([n["id"] for n in items[0]["notes"]], ["user:1", "mcp:2", "user:3"])

    def test_my_own_root_notes_are_skipped(self):
        self.assertEqual(pending_threads([note("mcp:1", "claude-code")], "claude-code"), [])

    def test_threads_are_grouped_by_root(self):
        notes = [
            note("mcp:1", "pi"),
            note("mcp:2", "codex"),
            note("user:3", "user", "user", parent="mcp:1"),
        ]
        items = pending_threads(notes, "claude-code")
        self.assertEqual([i["thread"] for i in items], ["mcp:1", "mcp:2"])
        self.assertEqual([n["id"] for n in items[0]["notes"]], ["mcp:1", "user:3"])

    def test_old_side_anchor(self):
        n = note("mcp:1", "pi")
        del n["newRange"]
        n["oldRange"] = [7, 7]
        self.assertEqual(pending_threads([n], "me")[0]["where"], "app.py:7 (old)")


if __name__ == "__main__":
    unittest.main()
