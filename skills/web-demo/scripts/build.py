"""Render the final video from a take: the screen recording placed by the
demo's layout, each voice clip at its beat, captions and the avatar.

Usage: python3 build.py final.mp4 [--narration narration.json] [--config demo.json] [--out out/]

Reads out/screen.webm, out/timeline.json, out/voice.json, out/<beat>.wav and
out/avatar_{idle,talk,open}.png. Writes final.mp4 and, with "captions_file",
final.srt. Refuses to overwrite final.mp4.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from webdemo import ass_document, caption_events, layout, load_config, srt_document, voice_intervals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("final")
    parser.add_argument("--narration", default="narration.json")
    parser.add_argument("--config", default="demo.json")
    parser.add_argument("--out", default="out")
    args = parser.parse_args()

    final = Path(args.final)
    if final.exists():
        sys.exit(f"{final} exists; pick a new name")
    out = Path(args.out)
    config = load_config(args.config)
    place = layout(config)
    narration = json.loads(Path(args.narration).read_text(encoding="utf-8"))
    voice = json.loads((out / "voice.json").read_text(encoding="utf-8"))
    timeline = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    starts = {beat["id"]: beat["start"] for beat in timeline["beats"]}
    beat_ids = list(starts)
    events = caption_events(narration["beats"], starts, voice)

    inputs = ["-i", str(out / "screen.webm")]
    for state in ("idle", "talk", "open"):
        inputs += ["-i", str(out / f"avatar_{state}.png")]
    for beat_id in beat_ids:
        inputs += ["-i", str(out / f"{beat_id}.wav")]

    graph = []
    for index, beat_id in enumerate(beat_ids):
        delay = int(starts[beat_id] * 1000)
        graph.append(f"[{4 + index}:a]adelay={delay}|{delay}[a{index}]")
    graph.append(
        "".join(f"[a{i}]" for i in range(len(beat_ids)))
        + f"amix=inputs={len(beat_ids)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[voice]"
    )

    width, height = place["canvas"]
    app_x, app_y = place["app_pos"]
    style = config["style"]
    graph.append(f"color=c={style['background'].replace('#', '0x')}:s={width}x{height}:r=25:d={timeline['total']}[bg]")
    graph.append(f"[bg][0:v]overlay=x={app_x}:y={app_y}[v]")
    label = "v"
    if config["captions"]:
        x, y, w, h = place["panel"]
        color, opacity = place["panel_fill"]
        graph.append(f"[{label}]drawbox=x={x}:y={y}:w={w}:h={h}:color={color.replace('#', '0x')}@{opacity}:t=fill[panel]")
        captions = out / "captions.ass"
        captions.write_text(ass_document(events, config), encoding="utf-8")
        graph.append(f"[panel]subtitles={captions}[captioned]")
        label = "captioned"
    if config["avatar"]["show"]:
        position = place["avatar_overlay"]
        graph.append(f"[{label}][1:v]overlay={position}[idle]")
        graph.append(f"[idle][2:v]overlay={position}:enable='{voice_intervals(starts, voice, 'voiced')}'[talk]")
        graph.append(f"[talk][3:v]overlay={position}:enable='{voice_intervals(starts, voice, 'mouth')}'[video]")
    else:
        graph.append(f"[{label}]null[video]")
    graph_path = out / "graph.txt"
    graph_path.write_text(";\n".join(graph), encoding="utf-8")

    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", *inputs,
            "-filter_complex_script", str(graph_path),
            "-map", "[video]", "-map", "[voice]",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "160k",
            "-t", str(timeline["total"]),
            "-movflags", "+faststart",
            str(final),
        ],
        check=True,
    )
    if config["captions_file"]:
        final.with_suffix(".srt").write_text(srt_document(events), encoding="utf-8")

    report = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(final), "-af", "volumedetect", "-vn", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    levels = dict(re.findall(r"(mean_volume|max_volume): (-?[\d.]+) dB", report))
    print(
        f"wrote {final}: {timeline['total']:.1f} s, {final.stat().st_size / 1e6:.1f} MB, "
        f"{width}x{height}, mean {levels.get('mean_volume')} dB, peak {levels.get('max_volume')} dB"
    )


if __name__ == "__main__":
    main()
