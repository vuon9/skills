"""Synthesizes a quiet low-tempo backing track, so the video has nothing to
license. 72 BPM over Am7, Fmaj7, Cmaj7, G6, faded in and out.

Usage: music.py <style> <seconds> <out.wav>
Styles: a, a soft pad; b, pad, kick and hat; b2, pad, soft kick, pitched tick
and bass (the default); b3, b2 with a slow melody; c, pad and arpeggio.
For a choice, render 20-second samples of two or three styles and ask."""
import math, random, struct, sys, wave

SR = 44100
BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
# Am7, Fmaj7, Cmaj7, G6, as MIDI notes.
CHORDS = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 64]]

def hz(n):
    return 440 * 2 ** ((n - 69) / 12)

def env(t, attack, release, length):
    if t < attack:
        return t / attack
    if t > length - release:
        return max(0.0, (length - t) / release)
    return 1.0

def render(style, seconds):
    n = int(seconds * SR)
    out = [0.0] * n
    rnd = random.Random(7)

    def add(start, length, fn):
        s0 = int(start * SR)
        for i in range(int(length * SR)):
            if s0 + i >= n:
                break
            out[s0 + i] += fn(i / SR)

    bars = int(seconds / BAR) + 1
    for b in range(bars):
        chord = CHORDS[b % len(CHORDS)]
        start = b * BAR
        pad_gain = {"a": 0.05, "b": 0.03, "b2": 0.03, "b3": 0.03, "c": 0.025}[style]
        for note in chord:
            f = hz(note)
            add(start, BAR + 1.2, lambda t, f=f: pad_gain * env(t, 1.0, 1.2, BAR + 1.2) * (
                math.sin(2 * math.pi * f * t) + 0.5 * math.sin(2 * math.pi * f * 1.003 * t) + 0.15 * math.sin(4 * math.pi * f * t)))
        def kick(at):
            add(start + at * BEAT, 0.35, lambda t: 0.5 * math.exp(-t / 0.09) * math.sin(2 * math.pi * (45 + 75 * math.exp(-t / 0.03)) * t))

        # A pitched tick instead of noise, which read as an audience.
        def tick(at, f, gain):
            add(start + at * BEAT, 0.08, lambda t: gain * math.exp(-t / 0.012) * (math.sin(2 * math.pi * f * t) + 0.4 * math.sin(2 * math.pi * 2.01 * f * t)))

        def bass(at, length):
            f = hz(chord[0] - 24)
            add(start + at * BEAT, length, lambda t: 0.16 * env(t, 0.02, 0.3, length) * math.exp(-t / 1.5) * math.sin(2 * math.pi * f * t))

        if style == "b2":
            kick(0), kick(2)
            tick(1, 1600, 0.10), tick(3, 1600, 0.10)
            bass(0, 1.5), bass(2.5, 1.2)
        if style == "b3":
            kick(0), kick(2.5)
            tick(2, 900, 0.08)
            bass(0, BAR)
            for at, note in ((0.5, chord[2] + 12), (1.6, chord[3] + 12), (3, chord[1] + 12)):
                f = hz(note)
                add(start + at * BEAT, 1.4, lambda t, f=f: 0.05 * env(t, 0.06, 0.5, 1.4) * math.sin(2 * math.pi * f * (t + 0.002 * math.sin(2 * math.pi * 5 * t))))
        if style in ("b", "b2", "b3"):
            if style == "b":
                kick(0), kick(2)
                for half in range(8):
                    if half % 2:
                        add(start + half * BEAT / 2, 0.06, lambda t: 0.04 * math.exp(-t / 0.015) * (rnd.random() * 2 - 1))
            for note in chord:
                f = hz(note + 12)
                add(start, 1.6, lambda t, f=f: 0.035 * math.exp(-t / 0.5) * (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t)))
        if style == "c":
            notes = [chord[i % 4] + 24 for i in range(8)]
            for i, note in enumerate(notes):
                f = hz(note)
                add(start + i * BEAT / 2, 1.2, lambda t, f=f: 0.06 * math.exp(-t / 0.35) * (math.sin(2 * math.pi * f * t) + 0.2 * math.sin(6 * math.pi * f * t)))

    peak = max(abs(x) for x in out) or 1
    fade = 1.5 * SR
    return [0.3 * x / peak * min(1, i / fade, (n - i) / fade) for i, x in enumerate(out)]

def main():
    style, seconds, path = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    samples = render(style, seconds)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x * 32767)) for x in samples))

main()
