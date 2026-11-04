import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "local-pr-review" / "scripts"))

from hunk_notes import next_round, pending_threads


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


class TestPendingThreads(unittest.TestCase):
    def test_other_agent_note_is_pending(self):
        items = pending_threads([note("mcp:1", "opencode")], "claude-code")
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
            note("mcp:1", "opencode"),
            note("mcp:2", "codex"),
            note("user:3", "user", "user", parent="mcp:1"),
        ]
        items = pending_threads(notes, "claude-code")
        self.assertEqual([i["thread"] for i in items], ["mcp:1", "mcp:2"])
        self.assertEqual([n["id"] for n in items[0]["notes"]], ["mcp:1", "user:3"])

    def test_old_side_anchor(self):
        n = note("mcp:1", "opencode")
        del n["newRange"]
        n["oldRange"] = [7, 7]
        self.assertEqual(pending_threads([n], "me")[0]["where"], "app.py:7 (old)")


if __name__ == "__main__":
    unittest.main()
