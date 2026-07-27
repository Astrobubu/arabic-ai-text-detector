# Contributing

Keep the project small, explainable, and honest.

## Recommended Workflow

1. Install locally with `pip install -e .` or `bash scripts/setup.sh`.
2. Run `make test`.
3. Run `make benchmark`.
4. Update `SKILL.md`, `README.md`, and `references/api-reference.md` when public behavior changes.

## Good Contributions

- Better evidence signals with tests
- Clearer agent instructions
- Better Chinese or multilingual handling that remains explainable
- False-positive examples and calibration notes
- Compatibility notes for additional agents
- Safer install and setup ergonomics for open source users

## Avoid

- Claims of forensic certainty
- Hidden network calls (the optional ML/docs/server extras are opt-in and documented in
  `docs/LEGAL_USE.md` - they must stay fully offline after the one-time model download)
- Heavy dependencies without a strong reason, and never make them required for Layer 1
- Features that encourage accusations or disciplinary decisions
- Output wording that frames scores as proof

## Pull Request Notes

- Keep runtime dependencies minimal.
- Prefer additive, well-tested heuristics over opaque model claims.
- If you adjust scoring behavior, include a benchmark or fixture update that explains why.
