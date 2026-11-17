import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "terminal-demo" / "scripts"))

import timeline
from fakes import Machine

TAPE = """Output takes/demo-01.mp4
Hide
Type "script -q -c bash"
Enter
#! keylog
Type "clear"
Enter
Show
#> open it
Type "acme"
Enter
#> move down three
Down 3
#> search
Type@200ms "/fix"
Enter
#> scroll to the rest
Type "jjjjjjjj"
#> quit
Escape
"""


def write_tape(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".tape", delete=False)
    f.write(text)
    f.close()
    return f.name


class TestTapeEvents(unittest.TestCase):
    def test_captions_and_keys(self):
        events, labels = timeline.tape_events(write_tape(TAPE))
        self.assertEqual([(l["caption"], l["keys"]) for l in labels], [
            ("open it", ["acme", "enter"]),
            ("move down three", ["↓  ↓  ↓"]),
            ("search", ["/fix", "enter"]),
            ("scroll to the rest", ["j ×8"]),
            ("quit", ["esc"]),
        ])
        # clear and its enter are logged but hidden; the script line is not logged.
        self.assertEqual(len(events), 6 + 5 + 3 + 5 + 8 + 1)
        self.assertEqual([e["label"] for e in events[:6]], [None] * 6)
        self.assertEqual(labels[1]["events"], [11, 12, 13])

    def test_rejects(self):
        cases = [
            ("a key after Show without a caption", 'Hide\n#! keylog\nShow\nType "q"\n', "no #> caption"),
            ("a Ctrl key after Show", 'Hide\n#! keylog\nShow\n#> stop\nCtrl+C\n', "Ctrl keys"),
        ]
        for id, tape, want in cases:
            with self.subTest(id):
                with self.assertRaises(SystemExit) as e:
                    timeline.tape_events(write_tape(tape))
                self.assertIn(want, str(e.exception))


class TestSplitKeys(unittest.TestCase):
    def test_cases(self):
        cases = [
            ("plain keys", b"ab\r", ["a", "b", "\r"]),
            ("script's header line is dropped", b"Script started on x\nq", ["q"]),
            ("a mode report is the terminal's, not a key", b"a\x1b[?2026;0$yb", ["a", "b"]),
            ("a colour reply is the terminal's", b"\x1b]11;rgb:1e1e/1e1e/2e2e\x1b\\j", ["j"]),
            ("a cursor position reply is the terminal's", b"\x1b[12;1Rk", ["k"]),
            ("arrows in either cursor mode are the same key", b"\x1b[B\x1bOB\x1bOA", ["\x1b[B", "\x1b[B", "\x1b[A"]),
            ("escape on its own is a key", b"\x1b", ["\x1b"]),
        ]
        for id, data, want in cases:
            with self.subTest(id):
                self.assertEqual(timeline.split_keys(data), want)


class TestLoggedTimes(unittest.TestCase):
    def test_pairs_input_chunks_with_their_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            keys, timing = Path(tmp, "k"), Path(tmp, "t")
            keys.write_bytes(b"Script started\nab\x1b[?2026;0$yc")
            timing.write_text("H 0.0 START_TIME x\nI 0.5 2\nO 0.1 30\nI 0.4 12\n")
            self.assertEqual(timeline.logged_times(keys, timing), [(0.5, "a"), (0.5, "b"), (1.0, "c")])


class TestMachine(unittest.TestCase):
    def test_builds_the_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "machine")
            m = Machine(root)
            cmd = m.cmd("acme", 'case "$1" in\n  list) echo ok ;;\n  *) unexpected "$@" ;;\nesac')
            m.data("list.json", [{"name": "widget"}])
            m.web("api.acme.test", "/v1/widgets/", {"n": 1})
            m.home("shop/notes.md", "hi\n")
            m.expect_miss("GET", "api.acme.test", "/v1/gone")
            m.done()
            self.assertTrue(os.stat(cmd).st_mode & stat.S_IXUSR)
            self.assertIn("unexpected()", open(cmd).read())
            self.assertEqual(open(os.path.join(root, "data", "list.json")).read(), '[\n  {\n    "name": "widget"\n  }\n]')
            self.assertEqual(open(os.path.join(root, "web", "api.acme.test", "v1", "widgets", "__index")).read(), '{"n": 1}')
            self.assertEqual(open(os.path.join(root, "home", "shop", "notes.md")).read(), "hi\n")
            self.assertEqual(open(os.path.join(root, "run", "expected-misses.txt")).read(), "MISS GET api.acme.test/v1/gone\n")

    def test_wipes_the_last_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "machine")
            Machine(root).home("left-over", "x")
            Machine(root)
            self.assertFalse(os.path.exists(os.path.join(root, "home", "left-over")))


if __name__ == "__main__":
    unittest.main()
