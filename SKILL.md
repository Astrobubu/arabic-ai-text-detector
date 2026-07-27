---
name: ai-text-detector-github
description: Detect whether a passage shows AI-like writing signals and return an explainable risk estimate with confidence, caveats, and next steps.
---

# AI Text Detector Skill

## Overview

This skill wraps the local `ai-detector-skill` analyzer into a reusable open source Codex-style skill.

It is designed for:

- essays
- emails
- articles
- reviews
- forum posts
- other prose where a user asks whether the writing may be AI-generated

This skill returns a risk estimate, not proof of authorship. It supports both Arabic and
English text, and combines two independent layers: rule-based heuristics (always available)
and an optional local ML classifier (`--no-ml` to skip it).

## Trigger Conditions

Use this skill when:

- the user asks "is this AI-written?"
- the user asks to detect AI-generated text
- the user pastes a passage and asks whether it sounds machine-written
- the user wants a cautious AI-likeness review for a document or message

## Required Behavior

- Never present the score as proof.
- Never accuse a named person of cheating, fraud, or misconduct.
- Ask for a longer sample when the text is under about 80 words.
- Prefer "AI-like signals are present" over "This was written by AI".
- For high-stakes contexts, recommend human review and comparison with known writing samples.

## Execution Flow

1. Receive the candidate text and check length.
2. If the sample is under about 80 words, explain that the detector will be noisy and ask for a longer sample when possible.
3. Save the text to a file or pipe it through stdin.
4. Run the local detector:

```bash
ai-detect path/to/text.txt --json
```

or:

```bash
python -m aidetect.cli path/to/text.txt --json
```

or from the repository helper:

```bash
python scripts/detect.py path/to/text.txt --json
```

5. Parse the JSON result. It is a combined report - see [references/api-reference.md](./references/api-reference.md)
   for the full contract - and validate that it includes:

- `language`
- `heuristic.score`, `heuristic.confidence`, `heuristic.verdict`, `heuristic.conclusion`, `heuristic.signals`
- `ml.available`, and when `true`, `ml.label` / `ml.ai_probability`
- `agreement`, `summary`
- `caveats`

6. Respond in this order:

1. One-sentence `summary` with uncertainty (this already reflects both layers).
2. `heuristic.score`/`confidence` and, if `ml.available`, the ML layer's label and probability.
3. Strongest evidence signals from `heuristic.signals`.
4. `caveats`.
5. Next steps only when useful (`heuristic.next_steps`).

If the two layers disagree (`agreement == "layers_disagree"`), say so explicitly rather than
picking one layer's number to lead with.

## Output Guidance

Good phrasing:

- "AI-like signals are present, but this is not proof."
- "The result is uncertain because the sample is short."
- "This should be reviewed against known writing samples."

Avoid:

- "This was definitely written by AI."
- "The detector proves misconduct."
- Any accusation against a named person.

## Repository Layout

- `SKILL.md`: skill contract and usage rules
- `scripts/detect.py`: repository-local wrapper for the detector
- `scripts/setup.sh`: local environment bootstrap
- `references/api-reference.md`: response contract and CLI reference
- `assets/templates/report.md`: reusable response template

## Development Notes

- Keep the analyzer explainable and lightweight.
- Prefer local heuristics over hidden network calls.
- Update this file whenever behavior or output changes.
