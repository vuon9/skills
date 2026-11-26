"""Record a narrated web demo: one scene per beat in narration.json.

Usage: PYTHONPATH=<skill>/scripts <venv python> record.py [storage-state.json]

Copy this file, demo.json, narration.json and title.html into the demo
folder and edit the part marked below. Writes out/screen.webm (at the
layout's app size) and out/timeline.json (where each beat's voice starts).
Needs out/voice.json from tts.py. A failed scene saves out/fail_<beat>.png.
"""

import json
import sys
import time
from pathlib import Path
from string import Template

from playwright.sync_api import sync_playwright

from webdemo import launch_chromium, layout, load_config  # PYTHONPATH=<skill>/scripts

# ---- Edit for your app ---------------------------------------------------------
BASE = "http://127.0.0.1:8080"
# What the app shows while it is busy; settle() waits for each to go.
BUSY_SELECTORS = [".loading", ".spinner"]


def scene_title(demo):
    demo.title_card()


def scene_queue(demo):
    demo.nav(BASE + "/orders/")
    demo.page.locator("table").first.wait_for()
    demo.settle()
    demo.speak()
    demo.at(1.5)
    demo.highlight(demo.page.locator("table").first, 3.0)


def scene_open(demo):
    demo.click(demo.page.locator("table tbody tr").first, dx=0.3)
    demo.speak()
    demo.highlight(demo.page.locator(".status").first, 2.5)


SCENES = {"title": scene_title, "queue": scene_queue, "open": scene_open}
# ---------------------------------------------------------------------------------

CURSOR_SCRIPT = """
  window.addEventListener('DOMContentLoaded', () => {
    const c = document.createElement('div');
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M3 2l7.5 19 2.6-7.9L21 10.5z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, { position: 'fixed', left: (window.__mx || 800) + 'px', top: (window.__my || 450) + 'px', zIndex: 2147483647, pointerEvents: 'none', transform: 'translate(-3px,-2px)' });
    document.body.appendChild(c);
    document.addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    document.addEventListener('mousedown', (e) => {
      const r = document.createElement('div');
      Object.assign(r.style, { position: 'fixed', left: e.clientX - 18 + 'px', top: e.clientY - 18 + 'px', width: '36px', height: '36px',
        borderRadius: '50%', border: '3px solid HIGHLIGHT', zIndex: 2147483646, pointerEvents: 'none', transition: 'all .45s ease-out' });
      document.body.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
      setTimeout(() => r.remove(), 500);
    }, true);
  });"""

HIGHLIGHT_SCRIPT = """([b, ms, color]) => {
    const h = document.createElement('div');
    Object.assign(h.style, { position: 'fixed', left: b.x - 6 + 'px', top: b.y - 6 + 'px', width: b.width + 12 + 'px', height: b.height + 12 + 'px',
      border: '3px solid ' + color, borderRadius: '8px', boxShadow: '0 0 0 9999px rgba(0,0,0,.12)', zIndex: 2147483640, pointerEvents: 'none',
      opacity: '0', transition: 'opacity .3s' });
    document.body.appendChild(h);
    requestAnimationFrame(() => (h.style.opacity = '1'));
    setTimeout(() => { h.style.opacity = '0'; setTimeout(() => h.remove(), 350); }, ms);
  }"""


class Demo:
    """The helpers a scene uses. Times are in seconds."""

    def __init__(self, page, config, voice):
        self.page, self.config, self.voice = page, config, voice
        width, height = layout(config)["app"]
        self.mouse = (width / 2, height / 2)
        self.beat_start = time.monotonic()
        self.beat_id = None

    def speak(self):
        """The beat's voice starts here: call it once the scene's page has loaded."""
        self.beat_start = time.monotonic()

    def at(self, seconds):
        """Wait until that moment of the beat's voice, counted from speak()."""
        wait = self.beat_start + seconds - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def settle(self, seconds=0.6):
        time.sleep(0.25)
        for selector in BUSY_SELECTORS:
            try:
                self.page.wait_for_selector(selector, state="hidden", timeout=30000)
            except Exception:  # noqa: BLE001  the app may not use that indicator at all
                pass
        time.sleep(seconds)

    def nav(self, url):
        """A full page load: single-page apps keep state across a hash-only change."""
        if self.page.url.startswith("http"):
            self.page.goto("about:blank")
        self.page.goto(url)

    def move_to(self, locator, dx=0.5, dy=0.5, glide=0.65):
        """Glide the cursor there, timed by the clock (a step count runs long)."""
        locator = locator.first
        locator.scroll_into_view_if_needed()
        box = locator.bounding_box()
        target = (box["x"] + box["width"] * dx, box["y"] + box["height"] * dy)
        start, began = self.mouse, time.monotonic()
        while True:
            t = min(1.0, (time.monotonic() - began) / glide)
            ease = 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
            self.page.mouse.move(start[0] + (target[0] - start[0]) * ease, start[1] + (target[1] - start[1]) * ease)
            if t == 1.0:
                break
            time.sleep(0.01)
        self.mouse = target
        self.page.evaluate("([x, y]) => { window.__mx = x; window.__my = y; }", list(target))

    def click(self, locator, dx=0.5, dy=0.5, glide=0.65, settle=0.6):
        self.move_to(locator, dx, dy, glide)
        time.sleep(0.15)
        self.page.mouse.down()
        time.sleep(0.09)
        self.page.mouse.up()
        self.settle(settle)

    def type(self, locator, text, delay_ms=30):
        self.click(locator)
        self.page.keyboard.type(text, delay=delay_ms)
        self.settle(0.5)

    def highlight(self, locator, seconds=2.5):
        """An amber frame around the element, with the rest of the page dimmed."""
        locator = locator.first
        locator.scroll_into_view_if_needed()
        self.page.evaluate(HIGHLIGHT_SCRIPT, [locator.bounding_box(), int(seconds * 1000), self.config["style"]["highlight"]])

    def title_card(self):
        """Show title.html with demo.json's title for the whole beat."""
        if not self.config["title_card"]:
            return
        page = Template(Path("title.html").read_text(encoding="utf-8")).substitute(
            title=self.config["title"],
            subtitle=self.config["subtitle"],
            background=self.config["style"]["background"],
            accent=self.config["style"]["accent"],
            footer=self.config["title_footer"],
        )
        self.page.set_content(page)
        self.speak()
        self.at(self.voice[self.beat_id]["duration"] + 0.3)


def main():
    state = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config("demo.json")
    narration = json.loads(Path("narration.json").read_text(encoding="utf-8"))
    voice = json.loads(Path("out/voice.json").read_text(encoding="utf-8"))
    width, height = layout(config)["app"]

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            storage_state=state,
            record_video_dir="out/video",
            record_video_size={"width": width, "height": height},
        )
        context.add_init_script(CURSOR_SCRIPT.replace("HIGHLIGHT", config["style"]["highlight"]))
        page = context.new_page()
        demo = Demo(page, config, voice)
        t0 = time.monotonic()
        timeline = []
        time.sleep(narration["intro_hold"])
        for beat in narration["beats"]:
            scene_start = time.monotonic()
            demo.beat_start, demo.beat_id = scene_start, beat["id"]
            try:
                SCENES[beat["id"]](demo)
            except Exception as error:  # noqa: BLE001  report the scene, keep the evidence
                page.screenshot(path=f"out/fail_{beat['id']}.png")
                context.close()
                browser.close()
                sys.exit(f"FAILED {beat['id']}: {str(error).splitlines()[0]}")
            # The voice clip goes where speak() was called (the scene start if it was not).
            timeline.append({"id": beat["id"], "start": round(demo.beat_start - t0, 3)})
            demo.at(voice[beat["id"]]["duration"] + narration["beat_gap"])
            print("beat", beat["id"], f"{time.monotonic() - scene_start:.1f} s")
        time.sleep(narration["outro_hold"])
        total = time.monotonic() - t0
        video = page.video.path()
        context.close()
        browser.close()
    Path(video).rename("out/screen.webm")
    Path("out/timeline.json").write_text(json.dumps({"total": round(total, 3), "beats": timeline}, indent=1), encoding="utf-8")
    print(f"recorded {total:.1f} s")


if __name__ == "__main__":
    main()
