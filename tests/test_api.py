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


def test_audit_bad_dataset_integration_regression():
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
    assert set(data.keys()) == {
        "dataset",
        "profile",
        "summary",
        "issues",
        "ml_analysis",
    }

    profile = data["profile"]
    assert profile["rows"] == 10
    assert profile["columns"] == 5

    issues = data["issues"]
    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "age"
        for issue in issues
    )
    assert any(
        issue["type"] == "INVALID_RANGE"
        and issue["column"] == "age"
        and issue["value"] == -50
        for issue in issues
    )
    assert any(
        issue["type"] == "INVALID_RANGE"
        and issue["column"] == "income"
        and issue["value"] == -900000
        for issue in issues
    )
    assert any(
        issue["type"] == "INVALID_CATEGORY"
        and issue["column"] == "gender"
        and issue["value"] == "X"
        for issue in issues
    )

    summary = data["summary"]
    assert summary["status"] == "REVIEW_REQUIRED"
    assert summary["errors"] >= 1
    assert summary["total_issues"] == len(issues) + summary["ml_anomalies"]

    ml_analysis = data["ml_analysis"]
    assert set(ml_analysis.keys()) == {
        "model",
        "anomalies_detected",
        "anomalies",
    }
    assert ml_analysis["model"] == "IsolationForest"
    assert ml_analysis["anomalies_detected"] >= 1
    assert len(ml_analysis["anomalies"]) == ml_analysis["anomalies_detected"]
    assert any(
        anomaly["type"] == "ML_ANOMALY"
        for anomaly in ml_analysis["anomalies"]
    )


def test_audit_response_contract(tmp_path):
    csv_path = tmp_path / "duplicate_contract.csv"
    csv_path.write_text(
        "name,age\n"
        "Alice,30\n"
        "Bob,40\n"
        "Alice,30\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/v1/audit",
        files={
            "file": (
                "duplicate_contract.csv",
                csv_path.read_bytes(),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {
        "dataset",
        "profile",
        "summary",
        "issues",
        "ml_analysis",
    }
    assert data["dataset"] == "duplicate_contract.csv"

    profile = data["profile"]
    assert set(profile.keys()) == {
        "dataset",
        "rows",
        "columns",
        "duplicate_rows",
        "column_profiles",
    }
    assert profile["dataset"] == "duplicate_contract.csv"
    assert profile["rows"] == 3
    assert profile["columns"] == 2
    assert profile["duplicate_rows"] == 1
    assert len(profile["column_profiles"]) == 2
    assert profile["column_profiles"][0]["name"] in {"name", "age"}

    summary = data["summary"]
    assert set(summary.keys()) == {
        "total_issues",
        "errors",
        "warnings",
        "ml_anomalies",
        "status",
    }
    assert isinstance(summary["total_issues"], int)
    assert isinstance(summary["errors"], int)
    assert isinstance(summary["warnings"], int)
    assert isinstance(summary["ml_anomalies"], int)
    assert summary["status"] in {"PASS", "WARNING", "REVIEW_REQUIRED"}
    assert summary["ml_anomalies"] == len(data["ml_analysis"]["anomalies"])
    assert summary["total_issues"] == len(data["issues"]) + summary["ml_anomalies"]

    ml_analysis = data["ml_analysis"]
    assert set(ml_analysis.keys()) == {
        "model",
        "anomalies_detected",
        "anomalies",
    }
    assert ml_analysis["model"] == "IsolationForest"
    assert ml_analysis["anomalies_detected"] == summary["ml_anomalies"]
    assert isinstance(ml_analysis["anomalies"], list)

    if ml_analysis["anomalies"]:
        anomaly = ml_analysis["anomalies"][0]
        assert set(anomaly.keys()) == {
            "type",
            "row",
            "anomaly_score",
            "severity",
            "message",
        }
        assert anomaly["type"] == "ML_ANOMALY"
        assert anomaly["severity"] == "WARNING"
        assert isinstance(anomaly["row"], int)
        assert isinstance(anomaly["anomaly_score"], (int, float))


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

def test_reject_empty_file():
    response = client.post(
        "/api/v1/audit",
        files={
            "file": (
                "empty.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The uploaded file is empty."
    )

def test_reject_malformed_csv():
    with open(
        "data/sample/test_malformed.csv",
        "rb",
    ) as file:
        response = client.post(
            "/api/v1/audit",
            files={
                "file": (
                    "test_malformed.csv",
                    file,
                    "text/csv",
                )
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The CSV file is malformed and could not be parsed."
    )



def test_reject_oversized_file():
    oversized_data = b"x" * (
        10 * 1024 * 1024 + 1
    )

    response = client.post(
        "/api/v1/audit",
        files={
            "file": (
                "large.csv",
                oversized_data,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "The uploaded file exceeds the 10 MB limit."
    )