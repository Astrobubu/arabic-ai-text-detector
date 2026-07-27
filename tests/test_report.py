from aidetect.report import generate_report


def test_insufficient_text_skips_ml_layer():
    report = generate_report("Too short.")
    assert report.agreement == "insufficient_text"
    assert report.ml.available is False
    assert report.heuristic.verdict == "insufficient_text"


def test_use_ml_false_skips_ml_layer_explicitly():
    text = " ".join([
        "In conclusion, it is important to note that this comprehensive overview is long enough for analysis.",
        "Moreover, the passage uses transitions and repeated phrasing to exercise the full report pipeline.",
    ] * 10)
    report = generate_report(text, use_ml=False)
    assert report.ml.available is False
    assert report.agreement == "ml_layer_unavailable"


def test_report_contains_legal_metadata():
    text = " ".join([
        "In conclusion, it is important to note that this comprehensive overview is long enough for analysis.",
        "Moreover, the passage uses transitions and repeated phrasing to exercise the full report pipeline.",
    ] * 10)
    report = generate_report(text)
    data = report.to_dict()

    assert len(data["input_sha256"]) == 64
    assert data["generated_at"]
    assert data["tool_version"]
    assert data["language"] == "en"
    assert any("not" in c.lower() and "proof" in c.lower() for c in data["caveats"])
