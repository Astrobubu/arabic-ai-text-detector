Language detected: {{ language }}

{{ summary }}

## Layer 1 — Rule-based heuristics

Conclusion: {{ heuristic.conclusion }}
Score: {{ heuristic.score }}/100
Confidence: {{ heuristic.confidence }}
Verdict: {{ heuristic.verdict }}
Words analyzed: {{ heuristic.word_count }}

Strongest evidence signals:
{{ heuristic.signals }}

## Layer 2 — Local ML classifier

{{ ml.available ? "Model: " + ml.model_id + " — Label: " + ml.label + " (" + ml.ai_probability + " AI probability)" : "Not available: " + ml.note }}

## Caveats

{{ caveats }}

## Suggested next steps

{{ heuristic.next_steps }}
