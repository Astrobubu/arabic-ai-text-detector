from __future__ import annotations

import argparse

from .extract import ExtractionUnavailable, UnsupportedFileType, extract_text
from .report import generate_report

try:
    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover - exercised only without the 'server' extra
    raise SystemExit(
        "The local backend server needs the optional 'server' extra. "
        'Install with: pip install -e ".[server]"'
    ) from exc

app = FastAPI(title="AI Text Detector (local)", version="0.2.0")

# Bound to 127.0.0.1 only (see run_server below) - this is a desktop app talking
# to itself, not a network service, so a permissive CORS policy is safe here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeTextRequest(BaseModel):
    text: str
    use_ml: bool = True


@app.get("/api/health")
def health() -> dict:
    from . import ml_layer
    return {
        "status": "ok",
        "ml_supported_languages": ["ar", "en", "mixed"],
        "arabic_model": ml_layer.ARABIC_MODEL_ID,
        "english_model": ml_layer.ENGLISH_MODEL_ID,
    }


@app.post("/api/analyze/text")
def analyze_text_endpoint(body: AnalyzeTextRequest) -> dict:
    report = generate_report(body.text, use_ml=body.use_ml)
    return report.to_dict()


@app.post("/api/analyze/file")
async def analyze_file_endpoint(file: UploadFile = File(...), use_ml: bool = True) -> dict:
    data = await file.read()
    try:
        text = extract_text(data, filename=file.filename)
    except (ExtractionUnavailable, UnsupportedFileType) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    report = generate_report(text, use_ml=use_ml)
    result = report.to_dict()
    result["source_filename"] = file.filename
    return result


def run_server(host: str = "127.0.0.1", port: int = 8756) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local AI text detector backend server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8756)
    args = parser.parse_args(argv)
    run_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
