"""Shared pieces of the web-demo scripts: the demo's choices (demo.json),
the video layout, caption timing and the browser launch.

Standard library only, so the repository's tests can import it.
"""

import copy
import json
import os
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get("WEB_DEMO_HOME", Path.home() / ".cache" / "web-demo"))
VENV_PYTHON = HOME / ".venv" / "bin" / "python"

# What demo.json holds when a key is left out. templates/demo.json shows every key.
DEFAULTS = {
    "title": "",
    "subtitle": "",
    "title_footer": "",
    "title_card": True,
    "layout": "strip",
    "captions": True,
    "captions_file": True,
    "avatar": {"show": True, "name": "Demo Bot"},
    "voice": {"engine": "kokoro", "id": "af_heart", "speed": 1.0},
    "style": {
        "background": "#1b2630",
        "panel": "#ffffff",
        "panel_opacity": 0.08,
        "accent": "#2ee6c5",
        "highlight": "#f0a020",
        "font": "Inter",
        "text": "#ffffff",
    },
    "notes": {},
}

# Layouts: the frame, the app's browser viewport, and where captions go.
# "strip": the app on top, captions and avatar in a band under it; nothing covers the app.
# "full": the app fills the frame; captions sit on a band over its bottom edge.
# "portrait": a phone-shaped app on top, a tall band under it, for vertical players.
LAYOUTS = {
    "strip": {"canvas": (1920, 1080), "app": (1600, 900), "band": "below"},
    "full": {"canvas": (1920, 1080), "app": (1920, 1080), "band": "over"},
    "portrait": {"canvas": (1080, 1920), "app": (1080, 1600), "band": "below"},
}

AVATAR_SIZE = (300, 132)  # width, height of avatar_*.png as avatar.py draws it


def merge(base, override):
    """A copy of base with override's keys laid over it, nested dicts merged."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path="demo.json"):
    """demo.json merged over DEFAULTS; a missing file gives the defaults."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    config = merge(DEFAULTS, data)
    if config["layout"] not in LAYOUTS:
        raise ValueError(f"layout {config['layout']!r}: use one of {sorted(LAYOUTS)}")
    return config


def layout(config):
    """Pixel positions for the render, from the config's layout and options."""
    preset = LAYOUTS[config["layout"]]
    canvas_w, canvas_h = preset["canvas"]
    app_w, app_h = preset["app"]
    app_x = (canvas_w - app_w) // 2
    show_avatar = config["avatar"]["show"]
    avatar_w, avatar_h = AVATAR_SIZE if show_avatar else (0, 0)
    margin = round(canvas_h * 0.02)

    if preset["band"] == "below":
        band_y, band_h = app_h, canvas_h - app_h
        left, right = app_x, app_x + app_w
    else:
        band_h = round(canvas_h * 0.15)
        band_y = canvas_h - band_h
        left, right = margin * 2, canvas_w - margin * 2

    panel_w = right - left - (avatar_w + margin if show_avatar else 0)
    style = config["style"]
    # Over the app, the band must be dark enough to read white text on any page.
    panel_fill = (style["panel"], style["panel_opacity"]) if preset["band"] == "below" else (style["background"], 0.85)
    return {
        "panel_fill": panel_fill,
        "canvas": (canvas_w, canvas_h),
        "app": (app_w, app_h),
        "app_pos": (app_x, 0),
        "panel": (left, band_y + margin, panel_w, band_h - 2 * margin),
        "caption_pos": (left + margin, band_y + band_h // 2),
        "caption_margin_right": canvas_w - left - panel_w + margin,
        # ffmpeg overlay position: right-aligned in the band, centred in its
        # height; w and h are the avatar image's own size, which follows the name.
        "avatar_overlay": f"x={right}-w:y={band_y}+({band_h}-h)/2",
        "font_size": round(canvas_h * 0.03) if canvas_w >= canvas_h else round(canvas_w * 0.04),
    }


def caption_events(beats, starts, voice):
    """One caption per sentence: (start, end, text) in seconds, each sentence
    timed by its share of the beat's characters.

    :param beats: narration beats, each with ``id`` and ``caption``
    :param starts: beat id -> where its voice starts in the video
    :param voice: beat id -> ``{"duration": seconds}``
    """
    events = []
    for beat in beats:
        if beat["id"] not in starts:
            continue
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", beat["caption"].strip()) if s]
        clock, duration = starts[beat["id"]], voice[beat["id"]]["duration"]
        total = sum(len(s) for s in sentences)
        for sentence in sentences:
            length = duration * len(sentence) / total
            events.append((round(clock, 3), round(clock + length, 3), sentence))
            clock += length
    return events


def _ass_color(hex_color):
    """#rrggbb as an ASS colour (&H00BBGGRR)."""
    value = hex_color.lstrip("#")
    return f"&H00{value[4:6]}{value[2:4]}{value[0:2]}".upper()


def _clock(seconds, separator):
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if separator == ".":
        return f"{int(hours)}:{int(minutes):02d}:{secs:05.2f}"
    whole = int(secs)
    return f"{int(hours):02d}:{int(minutes):02d}:{whole:02d},{int(round((secs - whole) * 1000)):03d}"


def ass_document(events, config):
    """Captions burned into the video, placed in the layout's band."""
    place = layout(config)
    width, height = place["canvas"]
    x, y = place["caption_pos"]
    style = config["style"]
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Caption,{style['font']},{place['font_size']},{_ass_color(style['text'])},"
        f"{_ass_color(style['text'])},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,"
        f"{x},{place['caption_margin_right']},0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, text in events:
        lines.append(
            f"Dialogue: 0,{_clock(start, '.')},{_clock(end, '.')},Caption,,0,0,0,,"
            f"{{\\an4\\pos({x},{y})}}{text}"
        )
    return "\n".join(lines) + "\n"


def srt_document(events):
    """The same captions as a sidecar subtitle file, for players that add their own."""
    blocks = []
    for number, (start, end, text) in enumerate(events, 1):
        blocks.append(f"{number}\n{_clock(start, ',')} --> {_clock(end, ',')}\n{text}\n")
    return "\n".join(blocks)


def voice_intervals(starts, voice, key):
    """ffmpeg enable expression for one kind of voice interval in every beat;
    "0" (never) when there are none, as with captions only."""
    terms = [
        f"between(t,{starts[beat_id] + a:.3f},{starts[beat_id] + b:.3f})"
        for beat_id in starts
        for a, b in voice[beat_id][key]
    ]
    return "+".join(terms) or "0"


def launch_chromium(playwright, **options):
    """Chromium for the recorder and the avatar. WEB_DEMO_CHROMIUM points at
    a browser already on the machine, when Playwright's own is not installed."""
    executable = os.environ.get("WEB_DEMO_CHROMIUM")
    if executable:
        options["executable_path"] = executable
    return playwright.chromium.launch(**options)
