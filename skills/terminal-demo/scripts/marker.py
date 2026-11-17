"""Runs beside the recording, inside the container. Follows script's key log as
it is written, and flips tmux's status marker the moment each subtitle's first
key arrives, so the video carries its own subtitle clock.

Usage: marker.py <tape> <keys log>"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline

tape, keys = sys.argv[1:3]
_, labels = timeline.tape_events(tape)
starts = [l["events"][0] for l in labels]
mark, flipped = 0, 0
while flipped < len(starts):
    try:
        with open(keys, "rb") as f:
            n = len(timeline.split_keys(f.read()))
    except FileNotFoundError:
        n = 0
    while flipped < len(starts) and n > starts[flipped]:
        mark ^= 1
        # tmux may not be up yet for the first flips; keep trying.
        while subprocess.run(["tmux", "set", "-g", "@mark", str(mark)], capture_output=True).returncode:
            time.sleep(0.01)
        subprocess.run(["tmux", "refresh-client", "-S"], capture_output=True)
        flipped += 1
    time.sleep(0.004)
