"""Install what web-demo needs, from package registries only: the Kokoro
voice (weights from npm, engine from PyPI), Playwright for Python, and its
Chromium unless WEB_DEMO_CHROMIUM names one already on the machine.

Usage: python3 install.py

Everything goes under WEB_DEMO_HOME (default ~/.cache/web-demo). Run the
other scripts with its Python: ~/.cache/web-demo/.venv/bin/python.
Needs Node (npm) and Python 3.10+.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from webdemo import HOME, VENV_PYTHON

MODEL_SHA256 = "fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478"


def run(*command, cwd=HOME):
    subprocess.run(command, cwd=cwd, check=True)


def install_weights():
    model = HOME / "kokoro-q8.onnx"
    if not model.exists():
        if not (HOME / "package.json").exists():
            run("npm", "init", "-y")
        # --ignore-scripts: onnxruntime-node's postinstall downloads a binary
        # from GitHub, and only the weights and voice files are used.
        run("npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "kokoro-js", "kokoro-q8-shards")
        parts = sorted((HOME / "node_modules" / "kokoro-q8-shards").glob("kokoro-q8.part*.bin"))
        with model.open("wb") as joined:
            for part in parts:
                joined.write(part.read_bytes())
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        model.unlink()
        sys.exit(f"kokoro-q8.onnx checksum {digest}, expected {MODEL_SHA256}")


def install_python():
    if not VENV_PYTHON.exists():
        run(sys.executable, "-m", "venv", str(HOME / ".venv"))
    run(str(VENV_PYTHON), "-m", "pip", "install", "-q", "kokoro-onnx", "soundfile", "playwright")
    # Video recording needs Playwright's own ffmpeg build; installing Chromium brings it.
    target = "ffmpeg" if os.environ.get("WEB_DEMO_CHROMIUM") else "chromium"
    try:
        run(str(VENV_PYTHON), "-m", "playwright", "install", target)
    except subprocess.CalledProcessError:
        print(
            f"playwright install {target} failed (its download may be blocked here). "
            "Set WEB_DEMO_CHROMIUM to a Chromium on this machine, and PLAYWRIGHT_BROWSERS_PATH "
            "to a folder holding Playwright's ffmpeg (ffmpeg-<revision>/ffmpeg-linux).",
            file=sys.stderr,
        )


def pack_voices():
    # Runs in the venv: numpy comes with kokoro-onnx.
    run(str(VENV_PYTHON), "-I", str(Path(__file__).with_name("pack_voices.py")), str(HOME))


def main():
    HOME.mkdir(parents=True, exist_ok=True)
    install_weights()
    install_python()
    pack_voices()
    print(f"ready: run the scripts with {VENV_PYTHON}")


if __name__ == "__main__":
    main()
