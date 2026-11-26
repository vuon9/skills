"""Render the narrator avatar in three states to transparent PNGs:
avatar_idle.png (quiet), avatar_talk.png (ring lit) and avatar_open.png
(ring lit, mouth open). Name and accent colour come from demo.json.

Usage: <venv python> avatar.py [out/] [--config demo.json]
"""

import argparse
from pathlib import Path
from string import Template

from playwright.sync_api import sync_playwright

from webdemo import launch_chromium, load_config

TEMPLATE = Template((Path(__file__).parent / "assets" / "avatar.html").read_text(encoding="utf-8"))
MOUTH_OPEN = '<rect x="47" y="70" width="26" height="13" rx="6.5" fill="#0f2a3a"/>'
MOUTH_CLOSED = '<rect x="47" y="74" width="26" height="4" rx="2" fill="#0f2a3a"/>'


def page_for(state, name, accent):
    talking = state != "idle"
    ring = (
        f'<circle cx="60" cy="60" r="57" fill="none" stroke="{accent}" stroke-width="5"/>'
        if talking
        else '<circle cx="60" cy="60" r="57" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="3"/>'
    )
    return TEMPLATE.substitute(
        name=name,
        opacity=1 if talking else 0.75,
        ring=ring,
        antenna=accent if talking else "#d9f7f1",
        mouth=MOUTH_OPEN if state == "open" else MOUTH_CLOSED,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", nargs="?", default="out")
    parser.add_argument("--config", default="demo.json")
    args = parser.parse_args()

    config = load_config(args.config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        page = browser.new_page(device_scale_factor=1)
        for state in ("idle", "talk", "open"):
            page.set_content(page_for(state, config["avatar"]["name"], config["style"]["accent"]))
            page.locator("#badge").screenshot(path=str(out / f"avatar_{state}.png"), omit_background=True)
        browser.close()
    print("avatars in", out)


if __name__ == "__main__":
    main()
