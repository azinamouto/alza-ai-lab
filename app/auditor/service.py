from pathlib import Path

import pandas as pd

from app.auditor.anomaly import detect_anomalies
from app.auditor.profiler import profile_csv
from app.auditor.quality import (
    check_allowed_values,
    check_missing_values,
    check_numeric_ranges,
)


def audit_csv(file_path: str) -> dict:
    """
    Run the complete rule-based and ML-based audit.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    df = pd.read_csv(path)

    profile = profile_csv(file_path)

    issues = []

    # -------------------------
    # RULE ENGINE
    # -------------------------

    issues.extend(
        check_missing_values(df)
    )

    numeric_rules = {
        "age": {
            "min": 0,
            "max": 120,
        },
        "income": {
            "min": 0,
        },
    }

    issues.extend(
        check_numeric_ranges(
            df,
            numeric_rules,
        )
    )

    category_rules = {
        "gender": ["M", "F"],
    }

    issues.extend(
        check_allowed_values(
            df,
            category_rules,
        )
    )

    # -------------------------
    # ML ENGINE
    # -------------------------

    ml_anomalies = detect_anomalies(df)

    error_count = sum(
        1
        for issue in issues
        if issue["severity"] == "ERROR"
    )

    warning_count = sum(
        1
        for issue in issues
        if issue["severity"] == "WARNING"
    )

    ml_anomaly_count = len(ml_anomalies)

    total_warnings = (
        warning_count + ml_anomaly_count
    )

    if error_count > 0:
        status = "REVIEW_REQUIRED"
    elif total_warnings > 0:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "dataset": profile["dataset"],
        "profile": profile,
        "summary": {
            "total_issues": (
                len(issues) + ml_anomaly_count
            ),
            "errors": error_count,
            "warnings": total_warnings,
            "ml_anomalies": ml_anomaly_count,
            "status": status,
        },
        "issues": issues,
        "ml_analysis": {
            "model": "IsolationForest",
            "anomalies_detected": ml_anomaly_count,
            "anomalies": ml_anomalies,
        },
    }