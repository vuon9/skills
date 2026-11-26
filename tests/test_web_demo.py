import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "web-demo" / "scripts"))

import webdemo  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[1] / "skills" / "web-demo" / "templates"


class TestConfig(unittest.TestCase):
    def test_missing_file_gives_defaults(self):
        config = webdemo.load_config("no-such-demo.json")
        self.assertEqual(config["layout"], "strip")
        self.assertEqual(config["voice"]["id"], "af_heart")

    def test_nested_keys_merge_over_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "demo.json"
            path.write_text(json.dumps({"avatar": {"name": "Guide"}, "style": {"accent": "#ff0000"}}))
            config = webdemo.load_config(path)
        self.assertEqual(config["avatar"], {"show": True, "name": "Guide"})
        self.assertEqual(config["style"]["accent"], "#ff0000")
        self.assertEqual(config["style"]["highlight"], "#f0a020")

    def test_unknown_layout_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "demo.json"
            path.write_text(json.dumps({"layout": "square"}))
            with self.assertRaises(ValueError):
                webdemo.load_config(path)

    def test_template_uses_only_known_keys(self):
        template = json.loads((TEMPLATES / "demo.json").read_text())
        self.assertEqual(set(template) - set(webdemo.DEFAULTS), set())


class TestLayout(unittest.TestCase):
    def test_strip_keeps_the_band_under_the_app(self):
        place = webdemo.layout(webdemo.load_config("no-such-demo.json"))
        self.assertEqual(place["canvas"], (1920, 1080))
        self.assertEqual(place["app"], (1600, 900))
        _, panel_y, _, _ = place["panel"]
        self.assertGreaterEqual(panel_y, 900)

    def test_panel_is_wider_without_the_avatar(self):
        config = webdemo.load_config("no-such-demo.json")
        with_avatar = webdemo.layout(config)["panel"][2]
        config["avatar"]["show"] = False
        self.assertGreater(webdemo.layout(config)["panel"][2], with_avatar)

    def test_every_layout_fits_its_canvas(self):
        for name in webdemo.LAYOUTS:
            with self.subTest(layout=name):
                config = webdemo.merge(webdemo.DEFAULTS, {"layout": name})
                place = webdemo.layout(config)
                width, height = place["canvas"]
                x, y, w, h = place["panel"]
                self.assertTrue(0 <= x and x + w <= width and 0 <= y and y + h <= height)


class TestCaptions(unittest.TestCase):
    BEATS = [{"id": "a", "caption": "Short one. A much longer second sentence here."}]

    def test_sentences_share_the_beat_by_length(self):
        events = webdemo.caption_events(self.BEATS, {"a": 10.0}, {"a": {"duration": 4.0}})
        self.assertEqual([text for _, _, text in events], ["Short one.", "A much longer second sentence here."])
        self.assertEqual(events[0][0], 10.0)
        self.assertAlmostEqual(events[-1][1], 14.0, places=2)
        self.assertLess(events[0][1] - events[0][0], events[1][1] - events[1][0])

    def test_beat_missing_from_the_take_is_skipped(self):
        self.assertEqual(webdemo.caption_events(self.BEATS, {}, {}), [])

    def test_srt_numbers_and_times(self):
        srt = webdemo.srt_document([(1.5, 3.25, "Hello.")])
        self.assertEqual(srt, "1\n00:00:01,500 --> 00:00:03,250\nHello.\n")

    def test_ass_places_captions_in_the_band(self):
        config = webdemo.load_config("no-such-demo.json")
        document = webdemo.ass_document([(0.0, 1.0, "Hi.")], config)
        x, y = webdemo.layout(config)["caption_pos"]
        self.assertIn(f"\\pos({x},{y})}}Hi.", document)

    def test_no_voice_intervals_means_never(self):
        self.assertEqual(webdemo.voice_intervals({"a": 0.0}, {"a": {"voiced": []}}, "voiced"), "0")


if __name__ == "__main__":
    unittest.main()
