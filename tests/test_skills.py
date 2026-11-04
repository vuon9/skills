import unittest
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
SKILLS = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir())


def frontmatter(path):
    _, block, _ = path.read_text(encoding="utf-8").split("---", 2)
    meta = {}
    for line in block.splitlines():
        key, sep, val = line.partition(":")
        if sep and not line.startswith(" "):
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


class TestSkills(unittest.TestCase):
    def test_frontmatter(self):
        for d in SKILLS:
            with self.subTest(skill=d.name):
                meta = frontmatter(d / "SKILL.md")
                self.assertEqual(meta.get("name"), d.name)
                self.assertTrue(meta.get("description", "").startswith("Use when"))

    def test_readme(self):
        for d in SKILLS:
            with self.subTest(skill=d.name):
                self.assertTrue((d / "README.md").is_file())

    def test_no_em_dash(self):
        for path in SKILLS_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".ts", ".sh", ".mjs"}:
                with self.subTest(path=str(path.relative_to(SKILLS_DIR))):
                    self.assertNotIn("—", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
