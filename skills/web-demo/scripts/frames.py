"""Contact sheets for checking a render: two frames per beat, one early in
its voice (15%) and one late (90%), labelled with the beat id.

Usage: python3 frames.py final.mp4 [--out out/]

Writes out/sheet_<n>.png, twelve frames each. Open every one and check that
each caption is true of the screen above it.
"""

import argparse
import json
import subprocess
from pathlib import Path


def grab(video, moment, text, path):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{moment:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
         f"scale=480:-2,drawtext=text='{text}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6",
         str(path)],
        check=True,
    )


def sheet(paths, path):
    paths = list(paths)
    while len(paths) % 4:
        paths.append(paths[-1])
    rows = len(paths) // 4
    inputs = sum([["-i", str(p)] for p in paths], [])
    graph = "".join(f"[{4 * r}][{4 * r + 1}][{4 * r + 2}][{4 * r + 3}]hstack=inputs=4[r{r}];" for r in range(rows))
    graph += ("".join(f"[r{r}]" for r in range(rows)) + f"vstack=inputs={rows}") if rows > 1 else "[r0]null"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, str(path)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--out", default="out")
    args = parser.parse_args()

    out = Path(args.out)
    timeline = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    voice = json.loads((out / "voice.json").read_text(encoding="utf-8"))
    frames = []
    for beat in timeline["beats"]:
        for label, share in (("early", 0.15), ("late", 0.9)):
            moment = beat["start"] + voice[beat["id"]]["duration"] * share
            path = out / f"frame_{len(frames):03d}.png"
            grab(args.video, moment, f"{beat['id']} {label} {moment:.0f}s", path)
            frames.append(path)
    for number, first in enumerate(range(0, len(frames), 12)):
        path = out / f"sheet_{number}.png"
        sheet(frames[first : first + 12], path)
        print(path)


if __name__ == "__main__":
    main()
