"""Shows what a stretch of keys does, one screenshot per key, in a minute
instead of a full take. Use it when a scene's navigation is in doubt: which row
a key lands on, where focus goes after a popup, which tab opens.

Run from the demo folder:
  probe.py <base tape> <steps file>   writes probe.tape: the base tape's settings
                                      and hidden setup, then each step line, with a
                                      pause and a screenshot after each key
  run.sh 'vhs probe.tape'
  probe.py --tile                     tiles probe/s01.png... into probe/grid.png

A steps file holds tape lines, such as Type "j" or Enter, one per line. Steps
start from the app's first screen, so begin with the keys that open the app."""
import glob
import os
import re
import subprocess
import sys

KEY = re.compile(r"^(Type|Enter|Escape|Up|Down|Left|Right|Tab|Backspace|Space|Ctrl\+)")


def write(base, steps):
    head = []
    for line in open(base):
        s = line.strip()
        if s.startswith("Output"):
            line = "Output probe/probe.mp4\n"
        head.append(line)
        if s == "Show":
            break
    os.makedirs("probe", exist_ok=True)
    for f in glob.glob("probe/s*.png"):
        os.remove(f)
    body, n = [], 0
    for line in open(steps):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        body.append(s + "\n")
        if KEY.match(s):
            n += 1
            body.append(f"Sleep 1.5s\nScreenshot probe/s{n:02d}.png\n")
    open("probe.tape", "w").writelines(head + ["\n"] + body)
    print(f"probe.tape: {n} screenshots; run: run.sh 'vhs probe.tape', then probe.py --tile")


def tile():
    shots = sorted(glob.glob("probe/s*.png"))
    if not shots:
        sys.exit("no screenshots in probe/")
    rows = (len(shots) + 3) // 4
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "1", "-i", "probe/s%02d.png",
                    "-vf", f"scale=640:-1,tile=4x{rows}", "-frames:v", "1", "probe/grid.png"], check=True)
    print(f"probe/grid.png: {len(shots)} steps, four per row")


if __name__ == "__main__":
    if sys.argv[1:] == ["--tile"]:
        tile()
    elif len(sys.argv) == 3:
        write(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
