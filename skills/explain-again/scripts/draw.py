"""Draw a Mermaid file in this terminal with the kitty graphics protocol.

Run it inside the pane that should show the picture: it renders the Mermaid
with Pele, turns the SVG into a PNG with macOS Quick Look, and writes the PNG
as kitty graphics escape codes scaled to the pane's width.
"""

import base64
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SIZE = 1600

mmd = pathlib.Path(sys.argv[1])
render = pathlib.Path(__file__).with_name("mermaid-svg.mjs")
with tempfile.TemporaryDirectory() as tmp:
    svg = subprocess.run(["node", render, mmd], capture_output=True, text=True, check=True).stdout
    (pathlib.Path(tmp) / "diagram.svg").write_text(svg)
    subprocess.run(["qlmanage", "-t", "-s", str(SIZE), "-o", tmp, pathlib.Path(tmp) / "diagram.svg"], capture_output=True, check=True)
    png = (pathlib.Path(tmp) / "diagram.svg.png").read_bytes()

# Quick Look always makes a square, with a wide diagram along its top, so a
# wide one shows only the rows it fills.
w, h = map(float, re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', svg).groups())
crop = f",h={round(SIZE * h / w)}" if w > h else ""

data = base64.standard_b64encode(png)
cols = shutil.get_terminal_size().columns - 2
out = sys.stdout.buffer
for i in range(0, len(data), 4096):
    more = int(i + 4096 < len(data))
    head = f"a=T,f=100,c={cols}{crop},m={more}" if i == 0 else f"m={more}"
    out.write(b"\x1b_G" + head.encode() + b";" + data[i:i + 4096] + b"\x1b\\")
out.write(b"\n")
out.flush()
