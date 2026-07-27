from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import ExtractionUnavailable, UnsupportedFileType, extract_text
from .report import CombinedReport, generate_report


def _print_human_report(report: CombinedReport) -> None:
    h = report.heuristic

    print(f"Language detected: {report.language}")
    print(f"Conclusion: {h.conclusion}")
    print(f"Score: {h.score}/100")
    print(f"Confidence: {h.confidence}")
    print(f"Verdict: {h.verdict}")
    print(f"Words analyzed: {h.word_count}")

    if h.signals:
        print("\nLayer 1 (rule-based heuristics) - strongest evidence:")
        for signal in h.strongest_signals():
            print(f"- {signal.name}: {signal.value:.2f} x {signal.weight:.2f} - {signal.note}")

    print("\nLayer 2 (local ML classifier):")
    if report.ml.available:
        print(f"- Model: {report.ml.model_id}")
        print(f"- Label: {report.ml.label} (AI probability {report.ml.ai_probability:.0%})")
        print(f"- Verdict: {report.ml.verdict}")
    else:
        print(f"- Not available: {report.ml.note}")

    print(f"\nCombined read ({report.agreement}):")
    print(report.summary)

    print("\nCaveats:")
    for caveat in report.caveats:
        print(f"- {caveat}")

    if h.next_steps:
        print("\nSuggested next steps:")
        for step in h.next_steps:
            print(f"- {step}")


def _read_input(path: str | None) -> str:
    if not path:
        return sys.stdin.read()

    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".docx", ".pdf"):
        try:
            return extract_text(p)
        except (ExtractionUnavailable, UnsupportedFileType) as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
    return p.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evidence-based, bilingual (Arabic/English) AI-like text risk analyzer."
    )
    parser.add_argument(
        "path", nargs="?",
        help="Text file to analyze (.txt, .docx, .pdf). Reads stdin when omitted.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--no-ml", action="store_true",
        help="Skip the local ML classifier layer and report heuristics only.",
    )
    args = parser.parse_args(argv)

    text = _read_input(args.path)
    report = generate_report(text, use_ml=not args.no_ml)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0

    _print_human_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
