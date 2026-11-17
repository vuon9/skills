"""Draws the checked subtitles on one or more takes, joins them, and adds music.
Never overwrites a final.

Run from the demo folder: render.py <final name> <take> [<take>...] [--music STYLE|none]

Each take must have labels/<take>/filter.txt from timeline.py, checked by
validate.py. A take narrower than the widest is centered on it, so a narrow
segment reads as a narrower window. ffmpeg runs in the container, which has
drawtext and the fonts. The final is H.264 with faststart, small enough for a
README at a minute or so."""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def size(path):
    w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    return int(w), int(h)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("name")
    ap.add_argument("takes", nargs="+")
    ap.add_argument("--music", default="b2", help="a music.py style, or none")
    ap.add_argument("--crf", default="20")
    a = ap.parse_args()
    out = f"final/{a.name}.mp4"
    if os.path.exists(out):
        sys.exit(f"{out} exists: pick a new name")
    for t in a.takes:
        if not os.path.exists(f"labels/{t}/filter.txt"):
            sys.exit(f"no subtitles for {t}: run timeline.py and validate.py first")
    os.makedirs("final", exist_ok=True)
    secs = sum(json.load(open(f"labels/{t}/timeline.json"))["duration"] for t in a.takes)
    widest = max(size(f"takes/{t}.mp4")[0] for t in a.takes)
    steps = []
    for t in a.takes:
        w, _ = size(f"takes/{t}.mp4")
        center = "" if w == widest else f"-vf 'pad={widest}:ih:(ow-iw)/2:0:color=0x11111B'"
        steps.append(f"ffmpeg -nostdin -v error -y -i takes/{t}.mp4 -/filter_complex labels/{t}/filter.txt -map '[v]' "
                     f"-c:v libx264 -crf 16 -pix_fmt yuv420p labels/{t}/sub.mp4")
        if center:
            steps.append(f"ffmpeg -nostdin -v error -y -i labels/{t}/sub.mp4 {center} -c:v libx264 -crf 16 "
                         f"-pix_fmt yuv420p labels/{t}/sub-wide.mp4 && mv labels/{t}/sub-wide.mp4 labels/{t}/sub.mp4")
    inputs = " ".join(f"-i labels/{t}/sub.mp4" for t in a.takes)
    n = len(a.takes)
    video = "".join(f"[{k}:v]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    if a.music == "none":
        steps.append(f"ffmpeg -nostdin -v error -y {inputs} -filter_complex '{video}' -map '[v]' "
                     f"-c:v libx264 -crf {a.crf} -pix_fmt yuv420p -movflags +faststart {out}")
    else:
        wav = f"final/{a.name}.wav"
        subprocess.run([sys.executable, os.path.join(HERE, "music.py"), a.music, str(int(secs) + 2), wav], check=True)
        steps.append(f"ffmpeg -nostdin -v error -y {inputs} -i {wav} -filter_complex '{video};[{n}:a]volume=0.55[a]' "
                     f"-map '[v]' -map '[a]' -shortest -c:v libx264 -crf {a.crf} -pix_fmt yuv420p -movflags +faststart "
                     f"-c:a aac -b:a 128k {out} && rm {wav}")
    subprocess.run([os.path.join(HERE, "run.sh"), " && ".join(steps)], check=True)
    print(out)


if __name__ == "__main__":
    main()
