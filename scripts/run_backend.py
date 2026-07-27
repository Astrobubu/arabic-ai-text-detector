"""PyInstaller entry point for the local backend server.

Not meant to be run directly during development - use
`python -m aidetect.server` (see README) instead. This script exists only so
PyInstaller has a plain file to analyze when freezing the backend.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aidetect.server import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
