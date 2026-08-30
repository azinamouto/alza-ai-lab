from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "ALZA AI Lab"
    assert data["version"] == "0.3.0"


def test_audit_csv():
    with open(
        "data/sample/test_bad_data.csv",
        "rb",
    ) as file:
        response = client.post(
            "/api/v1/audit",
            files={
                "file": (
                    "test_bad_data.csv",
                    file,
                    "text/csv",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["dataset"] == "test_bad_data.csv"
    assert data["summary"]["errors"] == 3
    assert data["summary"]["warnings"] == 2
    assert data["summary"]["ml_anomalies"] == 1
    assert data["summary"]["status"] == "REVIEW_REQUIRED"


def test_reject_non_csv():
    response = client.post(
        "/api/v1/audit",
        files={
            "file": (
                "test.txt",
                b"hello world",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_missing_file():
    response = client.post(
        "/api/v1/audit"
    )

    assert response.status_code == 422