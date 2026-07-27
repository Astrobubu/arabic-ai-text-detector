"""Pre-download the local ML classifier models for fully-offline bundling.

Run this once (with the 'ml' extra installed) before packaging the desktop
app, so the installer can ship the model weights and the end user's machine
never needs internet access to use the ML classifier layer.

Downloads each model into its own flat directory via huggingface_hub's
`local_dir` mode rather than the default hub cache. On Windows, the default
cache's blobs+snapshots layout falls back to full file copies (no symlink
permission), silently doubling on-disk size - `local_dir` avoids that and
also gives ml_layer.py a plain folder it can load directly, no HF_HOME
indirection needed.

Usage:
    python scripts/prefetch_models.py [--cache-dir model_cache]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=str(ROOT / "model_cache"))
    args = parser.parse_args(argv)

    cache_dir = Path(args.cache_dir).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            "error: huggingface_hub is not installed. "
            'Install the ML extra first: pip install -e ".[ml]"',
            file=sys.stderr,
        )
        return 2

    from aidetect.ml_layer import ARABIC_MODEL_ID, ENGLISH_MODEL_ID, MODEL_DIR_NAME_BY_MODEL

    for model_id in (ARABIC_MODEL_ID, ENGLISH_MODEL_ID):
        local_dir = cache_dir / MODEL_DIR_NAME_BY_MODEL[model_id]
        print(f"Downloading {model_id} into {local_dir} ...")
        snapshot_download(repo_id=model_id, local_dir=str(local_dir))
        print(f"  done: {model_id}")

    print(f"\nAll models cached under {cache_dir}")
    print("build_backend.py copies this folder alongside the frozen backend automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
