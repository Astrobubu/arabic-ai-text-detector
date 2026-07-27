# API Reference

## CLI

Primary command:

```bash
ai-detect path/to/text.txt --json      # also accepts .docx / .pdf
```

Flags:

- `--json` - emit machine-readable JSON (the combined report, see below)
- `--no-ml` - skip Layer 2 (local ML classifier), heuristics-only

Alternative entry points:

```bash
python -m aidetect.cli path/to/text.txt --json
python scripts/detect.py path/to/text.txt --json
```

When no file path is provided, the CLI reads from stdin.

## Local HTTP server (`ai-detect-server`, requires the `server` extra)

```bash
ai-detect-server --host 127.0.0.1 --port 8756
```

- `GET /api/health` - `{"status": "ok", "ml_supported_languages": [...], "arabic_model": "...", "english_model": "..."}`
- `POST /api/analyze/text` - body `{"text": str, "use_ml": bool = true}` -> combined report JSON
- `POST /api/analyze/file` - multipart form field `file` (`.txt`/`.docx`/`.pdf`), query param
  `use_ml` (default `true`) -> combined report JSON with an added `source_filename` field

## Combined Report JSON Contract

`generate_report(text, use_ml=True)` / the CLI's `--json` / both server endpoints all return this
shape:

```jsonc
{
  "generated_at": "2026-07-25T18:19:30+00:00",   // ISO 8601 UTC
  "tool_version": "0.2.0",
  "input_sha256": "…",                            // hash of the exact analyzed text
  "language": "ar",                                // "ar" | "en" | "mixed" | "unknown"
  "word_count": 400,
  "heuristic": { /* Layer 1, see below */ },
  "ml": { /* Layer 2, see below */ },
  "agreement": "both_layers_flag_ai_like",
  "summary": "Plain-English sentence describing where the layers agree or disagree.",
  "caveats": ["…"]
}
```

### `heuristic` (Layer 1 - rule-based, always present)

- `score`: integer 0-100
- `verdict`: `insufficient_text` | `low_ai_likelihood` | `mixed_or_uncertain` | `high_ai_likelihood`
- `confidence`: `low` | `medium`
- `language`: same detection as top-level `language`
- `word_count`, `conclusion`
- `signals`: list of `{name, value, weight, note}`
- `caveats`, `next_steps`

### `ml` (Layer 2 - local classifier, optional extra)

- `available`: `true`/`false`
- `model_id`: e.g. `sabaridsnfuji/arabic-ai-text-detector` or `Hello-SimpleAI/chatgpt-detector-roberta`
- `label`: the model's raw predicted label
- `ai_probability`: 0.0-1.0
- `verdict`: same bucket names as Layer 1, derived from `ai_probability`
- `note`: human-readable status, especially important when `available` is `false` (explains why:
  optional dep not installed, unsupported language, or inference failure)

### `agreement` values

`insufficient_text`, `ml_layer_unavailable`, `both_layers_flag_ai_like`,
`both_layers_flag_human_like`, `layers_disagree`, `uncertain_or_mixed`.

## Interpretation Rules

- Treat the score as a risk estimate, not proof - see [docs/LEGAL_USE.md](../docs/LEGAL_USE.md).
- Very short samples should return `insufficient_text` and skip Layer 2 entirely.
- When the two layers disagree, treat the result as unresolved rather than picking whichever
  layer supports the desired conclusion.
- High-stakes decisions should involve human review and comparison with known writing samples.
