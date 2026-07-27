"""Build the standalone backend executable for the desktop installer.

Freezes scripts/run_backend.py (which starts the FastAPI/uvicorn server) into
desktop/backend-dist/aidetect-server/ using PyInstaller, then copies the
pre-fetched model cache alongside it so electron-builder's extraResources
picks up both. Run scripts/prefetch_models.py first if you want the ML layer
to work fully offline in the packaged app.

Usage:
    python scripts/build_backend.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "desktop" / "backend-dist"
WORK_DIR = ROOT / "build" / "pyinstaller"
MODEL_CACHE = ROOT / "model_cache"

HIDDEN_IMPORTS = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

COLLECT_ALL = ["transformers", "torch", "tokenizers"]


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            'error: PyInstaller is not installed. Run: pip install -e ".[all]" pyinstaller',
            file=sys.stderr,
        )
        return 2

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "aidetect-server",
        "--onedir",
        "--noconfirm",
        "--distpath", str(DIST_DIR),
        "--workpath", str(WORK_DIR),
        "--specpath", str(WORK_DIR),
    ]
    for mod in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", mod]
    for mod in COLLECT_ALL:
        cmd += ["--collect-all", mod]
    cmd.append(str(ROOT / "scripts" / "run_backend.py"))

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    frozen_dir = DIST_DIR / "aidetect-server"
    if not frozen_dir.exists():
        print(f"error: expected PyInstaller output at {frozen_dir}, not found.", file=sys.stderr)
        return 1

    if MODEL_CACHE.exists():
        target = frozen_dir / "model_cache"
        print(f"Copying model cache -> {target}")
        shutil.copytree(MODEL_CACHE, target, dirs_exist_ok=True)
    else:
        print(
            "warning: no model_cache found. The packaged app will need internet access "
            "on first ML-layer use, or run scripts/prefetch_models.py and rebuild.",
            file=sys.stderr,
        )

    # electron-builder's extraResources expects the exe directly under backend-dist,
    # so flatten aidetect-server/* up one level.
    for item in frozen_dir.iterdir():
        shutil.move(str(item), str(DIST_DIR / item.name))
    frozen_dir.rmdir()

    print(f"\nBackend build complete: {DIST_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
