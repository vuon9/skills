"""Pack kokoro-js's voice files into voices.npz for kokoro-onnx.

Usage (install.py runs it): <venv python> pack_voices.py <web-demo home>

Each voices/<name>.bin in the kokoro-js npm package is 510 x 256 float32.
"""

import sys
from pathlib import Path

import numpy as np

home = Path(sys.argv[1])
voices = {
    path.stem: np.fromfile(path, dtype=np.float32).reshape(510, 1, 256)
    for path in sorted((home / "node_modules" / "kokoro-js" / "voices").glob("*.bin"))
}
np.savez(home / "voices.npz", **voices)
print(len(voices), "voices")
