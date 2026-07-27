import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from aidetect.server import app  # noqa: E402

client = fastapi_testclient.TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_analyze_text_endpoint():
    text = " ".join([
        "In conclusion, it is important to note that this comprehensive overview is long enough for analysis.",
        "Moreover, the passage uses transitions and repeated phrasing to exercise the server endpoint.",
    ] * 10)
    resp = client.post("/api/analyze/text", json={"text": text, "use_ml": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "en"
    assert data["ml"]["available"] is False


def test_analyze_file_endpoint_rejects_unsupported_type():
    resp = client.post(
        "/api/analyze/file",
        files={"file": ("sample.xyz", b"whatever", "application/octet-stream")},
    )
    assert resp.status_code == 422
