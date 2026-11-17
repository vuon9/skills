"""Times the subtitles from a marker the recording carries in its own frames.

VHS's video clock drifts from real time, faster in one take, slower in the
next, and unevenly, so times guessed from the tape or the key log land seconds
off. Instead the app runs in tmux, and marker.py flips a white block in tmux's
otherwise blank status row the moment each subtitle's first key arrives. Each
flip in the video is a subtitle start, to the frame.

A "#> caption" line in the tape starts a subtitle: it covers the key lines after
it, up to the next one, and its keys are read from those lines, so the text on
screen can't drift from what the tape presses.

Run from the demo folder: timeline.py <tape> <take> [--band PX]
Reads takes/<take>.mp4 and runs/<take>/<tape stem>.keys and .timing. Writes
labels/<take>/: the subtitle text files, filter.txt for render.py, and
timeline.json for validate.py."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KEYNAMES = {"Enter": ("\r", "enter"), "Escape": ("\x1b", "esc"), "Down": ("\x1b[B", "↓"), "Up": ("\x1b[A", "↑"),
            "Right": ("\x1b[C", "→"), "Left": ("\x1b[D", "←"), "Tab": ("\t", "tab"), "Backspace": ("\x7f", "⌫"),
            "Space": (" ", "space")}

# The terminal answers an app's questions on the same input stream the keys
# use: mode reports (ESC[?2026;0$y), colors (ESC]11;rgb:...ESC\), cursor
# positions (ESC[12;1R). None of them is a key.
TERMINAL_REPLY = re.compile(r"\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1bP[^\x1b]*\x1b\\|\x1b\[[?>=]?[0-9;]*\$?[a-zA-Z](?<![A-D])")
KEY = re.compile(r"\x1b\[[0-9;]*[A-D~]|\x1bO[A-D]|.", re.S)

# VHS's default padding, in pixels.
PADDING = 24
KEYS_FONT = "/usr/share/fonts/jetbrains-mono/JetBrainsMono-Bold.ttf"
CAPTION_FONT = "/usr/share/fonts/noto/NotoSans-Regular.ttf"


def tape_events(path):
    """Every key the tape sends after the #! keylog marker, in order, with the
    subtitle it belongs to (None for the hidden setup before Show)."""
    events, labels, label, logging, shown = [], [], None, False, False
    for n, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if line == "#! keylog":
            logging = True
            continue
        if line == "Show":
            shown = True
            continue
        if line.startswith("#>"):
            labels.append({"caption": line[2:].strip(), "line": n, "keys": [], "events": []})
            label = len(labels) - 1
            continue
        if not logging or not line or line.startswith("#"):
            continue
        # A key may carry its own speed, as in Type@500ms "x" or Down@100ms 3.
        m = re.match(r'Type(?:@\S+)? "(.*)"$', line)
        word = line.split()[0].split("@")[0]
        if m:
            text = m.group(1)
            seq = list(text)
            shown_as = f"{text[0]} ×{len(text)}" if len(text) > 3 and len(set(text)) == 1 else text
        elif word in KEYNAMES:
            count = int(line.split()[1]) if len(line.split()) > 1 and line.split()[1].isdigit() else 1
            seq = [KEYNAMES[word][0]] * count
            shown_as = "  ".join([KEYNAMES[word][1]] * count)
        elif word.startswith("Ctrl+"):
            sys.exit(f"tape line {n}: Ctrl keys are not paired with the key log yet; keep them in the hidden setup")
        else:
            continue
        own = label if shown else None
        if shown and own is None:
            sys.exit(f"tape line {n}: a key after Show with no #> caption above it")
        if own is not None:
            labels[own]["keys"].append(shown_as)
        for key in seq:
            if own is not None:
                labels[own]["events"].append(len(events))
            events.append({"bytes": key, "line": n, "label": own})
    return events, labels


def split_keys(data):
    """The keys in script's input log, without the terminal's replies."""
    if data.startswith(b"Script started"):
        data = data[data.index(b"\n") + 1:]
    text = TERMINAL_REPLY.sub("", data.decode("utf-8", "replace"))
    # An app in application cursor mode gets arrows as ESC O B, not ESC [ B.
    return [re.sub(r"^\x1bO([A-D])$", "\x1b[\\1", k) for k in KEY.findall(text)]


def logged_times(keys_path, timing_path):
    """(time, key) for each key, from script's timing log."""
    data = Path(keys_path).read_bytes()
    if data.startswith(b"Script started"):
        data = data[data.index(b"\n") + 1:]
    t, pos, out = 0.0, 0, []
    for line in Path(timing_path).read_text().splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[0] not in "IOSH":
            continue
        t += float(parts[1])
        if parts[0] == "I":
            chunk = data[pos:pos + int(parts[2])]
            pos += int(parts[2])
            out += [(t, k) for k in split_keys(chunk)]
    return out


def size(path):
    w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    return int(w), int(h)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout)


def brightness(take, crop):
    out = subprocess.run(["ffmpeg", "-nostdin", "-i", take, "-vf",
                          f"crop={crop},format=gray,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return [(float(t), float(v)) for t, v in re.findall(r"pts_time:([0-9.]+).*?YAVG=([0-9.]+)", out, re.S)]


def flips_in(frames):
    lo, hi = min(v for _, v in frames), max(v for _, v in frames)
    flips, on = [], False
    for t, v in frames:
        now = v > (lo + hi) / 2
        if now != on:
            flips.append(t)
            on = now
    return flips, hi - lo


def frame_bytes(take, at, crop, fmt):
    return subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{at:.3f}", "-i", take, "-frames:v", "1", "-vf",
                           f"crop={crop},format={fmt}", "-f", "rawvideo", "-"], capture_output=True).stdout


def marker_flips(take):
    """The frames where the status row's white block turns on or off, the row
    itself, and the terminal's background colour to paint it over with."""
    w, h = size(take)
    coarse, _ = flips_in(brightness(take, f"60:200:{PADDING + 2}:{h - 200}"))
    if not coarse:
        sys.exit("no marker flips at the bottom left of the video: did the tape start marker.py and tmux?")
    col = frame_bytes(take, coarse[0] + 0.1, f"1:200:{PADDING + 6}:{h - 200}", "gray")
    lit = [i for i, b in enumerate(col) if b > 200]
    if not lit:
        sys.exit("found no white block in the status row")
    # The status row is the bottom row, so the block is the lowest unbroken run;
    # anything bright above it (a cursor, a highlight) belongs to the app.
    end = start = lit[-1]
    while start - 1 in lit:
        start -= 1
    y, row_h = h - 200 + start, end - start + 1
    flips, contrast = flips_in(brightness(take, f"60:{row_h}:{PADDING + 2}:{y}"))
    if contrast < 60:
        sys.exit(f"the status row's brightness moves only {contrast:.0f}: no marker there")
    r, g, b = frame_bytes(take, coarse[0] + 0.1, f"1:1:{w - PADDING - 4}:{y + row_h // 2}", "rgb24")[:3]
    return flips, y, row_h, f"0x{r:02X}{g:02X}{b:02X}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tape")
    ap.add_argument("take")
    ap.add_argument("--band", type=int, default=140, help="height of the subtitle band under the app")
    ap.add_argument("--band-color", default="0x11111B")
    a = ap.parse_args()
    stem = os.path.splitext(os.path.basename(a.tape))[0]
    take, run, out = f"takes/{a.take}.mp4", f"runs/{a.take}", f"labels/{a.take}"
    events, labels = tape_events(a.tape)
    logged = logged_times(f"{run}/{stem}.keys", f"{run}/{stem}.timing")
    if [k for _, k in logged] != [e["bytes"] for e in events]:
        sys.exit(f"the log's {len(logged)} keys don't match the tape's {len(events)}: they can't be paired")
    flips, status_y, row_h, bg = marker_flips(take)
    if len(flips) != len(labels):
        sys.exit(f"the video has {len(flips)} marker flips and the tape {len(labels)} subtitles")
    end_of_take = duration(take)
    os.makedirs(out, exist_ok=True)
    # The block's edges blur across a pixel or two, so the patch reaches past them.
    rows, filters = [], [f"drawbox=x=0:y={status_y - 3}:w=iw:h={row_h + 6}:color={bg}:t=fill"]
    for i, l in enumerate(labels):
        start = flips[i]
        end = flips[i + 1] - 0.04 if i + 1 < len(labels) else end_of_take
        # Keys after the first are placed by the log, at real time from it.
        first = logged[l["events"][0]][0]
        key_times = [round(start + logged[j][0] - first, 3) for j in l["events"]]
        keys = "  ".join(l["keys"])
        rows.append({"caption": l["caption"], "keys": keys, "start": round(start, 3), "end": round(end, 3),
                     "line": l["line"], "key_times": key_times})
        open(os.path.join(out, f"k{i}.txt"), "w").write(keys)
        open(os.path.join(out, f"c{i}.txt"), "w").write(l["caption"])
        on = f"enable='between(t,{start:.3f},{end:.3f})'"
        filters.append(f"drawtext=fontfile={KEYS_FONT}:textfile=/vhs/{out}/k{i}.txt:fontsize=34:fontcolor=white:"
                       f"box=1:boxcolor=0x7C3AED@0.96:boxborderw=14:x=(w-text_w)/2:y=h-{a.band}+24:{on}")
        filters.append(f"drawtext=fontfile={CAPTION_FONT}:textfile=/vhs/{out}/c{i}.txt:fontsize=30:fontcolor=0xCDD6F4:"
                       f"x=(w-text_w)/2:y=h-{a.band}+84:{on}")
    graph = filters[0] + f",pad=iw:ih+{a.band}:0:0:color={a.band_color}," + ",".join(filters[1:])
    open(os.path.join(out, "filter.txt"), "w").write("[0:v]" + graph + "[v]")
    json.dump({"take": a.take, "duration": end_of_take, "status_y": status_y, "flips": flips, "labels": rows},
              open(os.path.join(out, "timeline.json"), "w"), indent=1)
    print(f"{len(events)} keys paired with the log; {len(flips)} marker flips for {len(labels)} subtitles")
    for r in rows:
        print(f"{r['start']:7.2f} - {r['end']:7.2f}  {r['keys'][:30]:30} {r['caption']}")


if __name__ == "__main__":
    main()
