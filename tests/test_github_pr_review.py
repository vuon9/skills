import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "github-pr-review" / "scripts"))

from pr_threads import is_agent, next_round, pending_items, seen_ids


def comment(cid, login, typename="User", body="text"):
    return {
        "id": cid,
        "url": f"https://github.com/o/r/pull/1#{cid}",
        "body": body,
        "createdAt": "2026-09-23T00:00:00Z",
        "author": {"login": login, "__typename": typename},
    }


def thread(tid, comments, resolved=False, outdated=False):
    return {
        "id": tid,
        "isResolved": resolved,
        "isOutdated": outdated,
        "path": "app.py",
        "line": 10,
        "comments": {"nodes": comments},
    }


def pr(threads=(), reviews=(), comments=()):
    return {
        "reviewThreads": {"nodes": list(threads)},
        "reviews": {"nodes": list(reviews)},
        "comments": {"nodes": list(comments)},
    }


class TestRounds(unittest.TestCase):
    def test_first_round_is_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(next_round(Path(tmp) / "pr-1"), 1)

    def test_next_round_follows_highest_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            pr_dir = Path(tmp)
            (pr_dir / "round-01.md").write_text("", encoding="utf-8")
            (pr_dir / "round-03.md").write_text("", encoding="utf-8")
            (pr_dir / "notes.md").write_text("", encoding="utf-8")
            self.assertEqual(next_round(pr_dir), 4)

    def test_seen_ids_collects_node_ids_from_round_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            pr_dir = Path(tmp)
            (pr_dir / "round-01.md").write_text(
                "<!-- ids: PRRT_a1, PRRC_b2 -->\n<!-- ids: IC_c3 -->", encoding="utf-8"
            )
            (pr_dir / "round-02.md").write_text("<!-- ids: PRR_d4 -->", encoding="utf-8")
            self.assertEqual(seen_ids(pr_dir), {"PRRT_a1", "PRRC_b2", "IC_c3", "PRR_d4"})


class TestAgentDetection(unittest.TestCase):
    def test_github_app_accounts_are_agents(self):
        self.assertTrue(is_agent({"login": "copilot-pull-request-reviewer", "__typename": "Bot"}))

    def test_bot_suffix_is_agent(self):
        self.assertTrue(is_agent({"login": "claude[bot]", "__typename": "User"}))

    def test_extra_logins_are_agents(self):
        self.assertTrue(is_agent({"login": "my-agent", "__typename": "User"}, {"my-agent"}))

    def test_people_are_not_agents(self):
        self.assertFalse(is_agent({"login": "alice", "__typename": "User"}))

    def test_deleted_account_is_not_agent(self):
        self.assertFalse(is_agent(None))


class TestPendingItems(unittest.TestCase):
    def test_unresolved_agent_thread_is_pending(self):
        data = pr(threads=[thread("PRRT_1", [comment("PRRC_1", "copilot", "Bot")])])
        items = pending_items(data, "me", set())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "thread")
        self.assertTrue(items[0]["agent"])
        self.assertEqual(items[0]["ids"], ["PRRT_1", "PRRC_1"])

    def test_resolved_thread_is_skipped(self):
        data = pr(threads=[thread("PRRT_1", [comment("PRRC_1", "copilot", "Bot")], resolved=True)])
        self.assertEqual(pending_items(data, "me", set()), [])

    def test_thread_seen_in_earlier_round_is_skipped(self):
        data = pr(threads=[thread("PRRT_1", [comment("PRRC_1", "alice")])])
        self.assertEqual(pending_items(data, "me", {"PRRT_1", "PRRC_1"}), [])

    def test_new_reply_on_seen_thread_is_pending_again(self):
        data = pr(
            threads=[thread("PRRT_1", [comment("PRRC_1", "alice"), comment("PRRC_2", "alice")])]
        )
        self.assertEqual(len(pending_items(data, "me", {"PRRT_1", "PRRC_1"})), 1)

    def test_thread_where_viewer_replied_last_is_skipped(self):
        data = pr(threads=[thread("PRRT_1", [comment("PRRC_1", "alice"), comment("PRRC_2", "me")])])
        self.assertEqual(pending_items(data, "me", set()), [])

    def test_thread_author_is_the_opener_not_the_last_replier(self):
        data = pr(
            threads=[thread("PRRT_1", [comment("PRRC_1", "coderabbitai", "Bot"), comment("PRRC_2", "alice")])]
        )
        self.assertTrue(pending_items(data, "me", set())[0]["agent"])

    def test_empty_review_bodies_and_own_comments_are_skipped(self):
        data = pr(
            reviews=[comment("PRR_1", "copilot", "Bot", body=""), comment("PRR_2", "alice", body="LGTM but see x")],
            comments=[comment("IC_1", "me"), comment("IC_2", "claude", "Bot")],
        )
        items = pending_items(data, "me", set())
        self.assertEqual([i["ids"] for i in items], [["PRR_2"], ["IC_2"]])
        self.assertEqual([i["kind"] for i in items], ["review", "comment"])


if __name__ == "__main__":
    unittest.main()
