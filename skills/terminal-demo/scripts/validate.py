"""Checks a take, and the final made from it, before anyone watches them.
Exits 1 on any failure.

Run from the demo folder: validate.py <take> [--final <name> [--with <take>...]]

1. Made up only: no real identifier from the deny list ($TD_DENY, one per line,
   kept outside the demo folder so it never travels with it) in the made-up
   machine, the tapes, or the subtitles.
2. Nothing unanswered: fakeweb missed no request beyond the expected misses,
   logged no error, and no fake command was called in a way it doesn't know.
3. Every key labeled and on time: timeline.py already refuses a take whose key
   log doesn't match the tape, or whose marker flips don't match the subtitles.
   Here: every subtitle has keys, none overlaps the next, and one shown too
   briefly to read is listed.
4. Stills: a contact sheet per 12 subtitles, one frame from each, with an index
   file, for a person to check every caption against its frame.
5. The final, when named: it has audio, and runs as long as its takes together.

The stills are the check that matters most: a take can be perfectly timed and
still caption the wrong thing."""
import argparse
import glob
import json
import os
import subprocess
import sys

fails, notes = [], []


def fail(msg):
    fails.append(msg)


def made_up(env, take):
    deny_path = os.environ.get("TD_DENY", "")
    if not deny_path or not os.path.exists(deny_path):
        fail("no deny list: set TD_DENY to a file of real names, emails, hosts and paths that must never appear")
        return
    deny = [w.strip().lower() for w in open(deny_path) if w.strip() and not w.startswith("#")]
    roots = [os.path.join(env, d) for d in ("bin", "data", "web", "home")] + glob.glob("*.tape") + [f"labels/{take}"]
    for root in roots:
        files = [root] if os.path.isfile(root) else [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs]
        for f in files:
            try:
                with open(f, "rb") as fh:
                    head = fh.read(1 << 20)
            except OSError:
                continue
            if b"\0" in head[:4096]:
                continue  # a binary, such as the app under test
            text = head.decode("utf-8", "ignore").lower()
            for w in deny:
                if w in text:
                    fail(f"real identifier {w!r} in {f}")


def answered(run):
    log = os.path.join(run, "fakeweb.log")
    misses = {l.strip() for l in open(log) if l.startswith("MISS")} if os.path.exists(log) else set()
    exp_path = os.path.join(run, "expected-misses.txt")
    expected = {l.strip() for l in open(exp_path)} if os.path.exists(exp_path) else set()
    for m in sorted(misses - expected):
        fail(f"fakeweb had no answer: {m}")
    err = os.path.join(run, "fakeweb.err")
    if os.path.exists(err) and open(err).read().strip():
        fail("fakeweb logged errors: " + open(err).read().strip()[:300])
    calls = os.path.join(run, "calls.log")
    for line in open(calls) if os.path.exists(calls) else []:
        if "unexpected" in line:
            fail("a fake command was called in a way it doesn't know: " + line.strip())


def labeled(tl):
    prev_end = -1
    for i, l in enumerate(tl["labels"]):
        if not l["keys"]:
            fail(f"subtitle {i} ({l['caption']}) has no keys")
        if l["start"] < prev_end:
            fail(f"subtitle {i} starts before the one before it ends")
        if l["end"] - l["start"] < 0.8:
            notes.append(f"subtitle {i} ({l['keys']}) shows for only {l['end'] - l['start']:.1f}s: add a Sleep after its keys")
        prev_end = l["end"]


def stills(take_mp4, tl, out):
    for f in glob.glob(os.path.join(out, "sheet-*")):
        os.remove(f)
    labels = tl["labels"]
    for s in range(0, len(labels), 12):
        group = labels[s:s + 12]
        frames = []
        for i, l in enumerate(group, s):
            t = min(l["key_times"][-1] + 0.8, l["end"] - 0.05)
            png = os.path.join(out, f"still-{i:03d}.png")
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", take_mp4,
                            "-frames:v", "1", "-vf", "scale=960:-2", png], check=True)
            frames.append(png)
        sheet = os.path.join(out, f"sheet-{s // 12:02d}.png")
        n = len(frames)
        inputs = sum((["-i", p] for p in frames), [])
        graph = ";".join(f"[{k}:v]scale=960:540,setsar=1[f{k}]" for k in range(n))
        graph += ";" + "".join(f"[f{k}]" for k in range(n)) + (
            f"xstack=inputs={n}:layout=" + "|".join(f"{(k % 3) * 960}_{(k // 3) * 540}" for k in range(n)) + ":fill=black"
            if n > 1 else "copy") + "[out]"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[out]",
                        "-frames:v", "1", sheet], check=True)
        with open(sheet[:-4] + ".txt", "w") as f:
            f.write("Tiles read left to right, three per row. Each frame is just after the subtitle's last key.\n")
            for i, l in enumerate(group, s):
                f.write(f"{i - s:2d}  #{i}  {l['start']:7.2f}  {l['keys']}  |  {l['caption']}\n")
        for p in frames:
            os.remove(p)
        notes.append(f"look at {sheet} with {sheet[:-4]}.txt")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def final_ok(final, takes):
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", final],
                             capture_output=True, text=True).stdout.split()
    if "audio" not in streams:
        notes.append(f"{final} has no audio")
    whole = sum(dur(f"takes/{t}.mp4") for t in takes)
    if abs(dur(final) - whole) > 1.5:
        fail(f"{final} runs {dur(final):.1f}s and its takes {whole:.1f}s")
    notes.append(f"{final}: {dur(final):.1f}s, {os.path.getsize(final) / 1e6:.1f} MB")


def main():
    ap = argparse.ArgumentParser(description="Check a take, and its final, before anyone watches them.")
    ap.add_argument("take")
    ap.add_argument("--final", help="the final's name, in final/")
    ap.add_argument("--with", dest="others", nargs="*", default=[], help="the other takes the final joins")
    a = ap.parse_args()
    env = os.environ.get("DEMO_ENV", f"/tmp/terminal-demo/{os.path.basename(os.getcwd())}")
    out = f"labels/{a.take}"
    tl = json.load(open(os.path.join(out, "timeline.json")))
    made_up(env, a.take)
    answered(f"runs/{a.take}")
    labeled(tl)
    stills(f"takes/{a.take}.mp4", tl, out)
    if a.final:
        final_ok(f"final/{a.final}.mp4", [a.take] + a.others)
    for n in notes:
        print("note:", n)
    for f in fails:
        print("FAIL:", f)
    print(f"{len(tl['labels'])} subtitles, {len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
