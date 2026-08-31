from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from app.auditor.anomaly import detect_anomalies
from app.auditor.profiler import profile_csv
from app.auditor.quality import validate_columns
from app.core.schemas import ColumnRule


DEFAULT_RULES = [
    ColumnRule(column="age", minimum=0, maximum=120),
    ColumnRule(column="income", minimum=0),
    ColumnRule(column="gender", allowed_values=["M", "F"]),
]


def audit_csv(file_path: str) -> dict:
    """
    Run the complete rule-based and ML-based audit.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    try:
        df = pd.read_csv(path)

    except EmptyDataError as exc:
        raise ValueError(
            "The CSV file contains no readable data."
        ) from exc

    except ParserError as exc:
        raise ValueError(
            "The CSV file is malformed and could not be parsed."
        ) from exc

    profile = profile_csv(file_path)

    issues = []

    # -------------------------
    # RULE ENGINE
    # -------------------------

    issues.extend(
        validate_columns(
            df,
            DEFAULT_RULES,
        )
    )

    # -------------------------
    # ML ENGINE
    # -------------------------

    ml_anomalies = detect_anomalies(df, rules=DEFAULT_RULES)

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