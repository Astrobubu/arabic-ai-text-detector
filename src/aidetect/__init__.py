from .core import DetectionResult, analyze_text, detect_language
from .report import CombinedReport, generate_report

__all__ = [
    "analyze_text",
    "detect_language",
    "DetectionResult",
    "generate_report",
    "CombinedReport",
]
