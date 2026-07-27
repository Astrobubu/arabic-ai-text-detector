# AI Text Detector - Desktop App

An Electron shell around the same `aidetect` engine used by the CLI, for someone who just wants
to double-click an app: paste text or drop in a `.txt`/`.docx`/`.pdf` file and get a bilingual
(Arabic/English) two-layer report with PDF export. The UI itself is fully translated (not just
the input box) - Arabic is the default with proper RTL layout, with a one-click switch to
English, and a light/dark theme toggle that starts from the OS preference. Everything runs
locally - see [../docs/LEGAL_USE.md](../docs/LEGAL_USE.md) for what the report does and doesn't
prove.

## Architecture

- `main.js` - Electron main process. Spawns the local Python backend (`aidetect.server`) as a
  child process, waits for it to become healthy, and opens the window.
- `preload.js` - exposes a small `window.electronAPI` (PDF export, backend readiness events) to
  the renderer via `contextBridge`, with `contextIsolation` on and `nodeIntegration` off.
- `renderer/i18n.js` - the `ar`/`en` translation dictionaries for every UI string, including
  report labels and verdict/agreement phrasing (not machine-translated at render time - each
  language has its own hand-written copy).
- `renderer/` - plain HTML/CSS/JS UI. Talks to the backend over `http://127.0.0.1:8756` using
  `fetch`, not Node APIs, so it works the same in dev and packaged. Language and theme choices
  persist via `localStorage`.
- The Python backend (`src/aidetect/server.py`, a FastAPI app) does the actual analysis and is
  otherwise identical to what the CLI/library use.

## Run from source (development)

1. From the repo root, create the project's virtual environment once and install everything:

   ```bash
   python -m venv .venv
   .venv\Scripts\pip install -e ".[all]"          # Windows
   # .venv/bin/pip install -e ".[all]"             # macOS/Linux
   ```

   `main.js` automatically prefers `../.venv` if present, otherwise falls back to the `python`
   on your PATH.

2. From `desktop/`:

   ```bash
   npm install
   npm start
   ```

   The app spawns the backend itself - you do not need to run it separately. On first launch,
   if the ML classifier layer's models aren't cached yet, the first analysis that uses them will
   download them from Hugging Face (one-time, then fully offline - see prefetching below to
   avoid this at analysis time entirely).

## Building a one-click Windows installer

Producing a real installer that needs zero Python/Node knowledge from the end user is a two-step
freeze: first the Python backend, then the Electron shell around it.

```bash
# 1. (optional but recommended) cache the ML models so the installer needs no internet at all
python scripts/prefetch_models.py

# 2. freeze the Python backend into desktop/backend-dist/
python scripts/build_backend.py

# 3. build the Windows installer (produces an NSIS setup.exe under desktop/dist/)
cd desktop
npm install
npm run dist
```

The result is a single `setup.exe` in `desktop/dist/` that installs the app, creates a desktop
shortcut, and needs no Python or Node installed on the target machine - `build/electron-builder`
bundles a portable copy of everything, including the frozen backend from step 2.

**Known caveat:** PyInstaller freezing `transformers`/`torch` can require iterating on hidden
imports depending on the exact package versions on your build machine - if `build_backend.py`
produces an exe that fails at runtime, check its console output for `ModuleNotFoundError` and
add the missing module to `HIDDEN_IMPORTS`/`COLLECT_ALL` in `scripts/build_backend.py`.

## Self-test

`main.js` supports a `--self-test` flag that starts the backend, waits for `/api/health`, prints
`SELF_TEST_OK` or `SELF_TEST_FAIL`, and quits - useful for a quick smoke check without manually
clicking through the UI:

```bash
.\node_modules\.bin\electron.cmd . --self-test --disable-gpu --no-sandbox
```

There's also a `--screenshot <path>` flag that runs a full sample analysis and saves a PNG of
the results, optionally toggling language/theme first with `--lang-en` / `--theme-light` -
useful for visually checking the UI after changes without clicking through it by hand:

```bash
.\node_modules\.bin\electron.cmd . --screenshot demo.png --lang-en --theme-light --disable-gpu --no-sandbox
```
