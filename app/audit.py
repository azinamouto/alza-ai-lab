import argparse

from app.auditor.service import audit_csv
from app.core.schemas import AuditReport


def run_audit(file_path: str) -> AuditReport:
    """
    Execute the complete ALZA AI audit pipeline.
    """

    result = audit_csv(file_path)

    return AuditReport.model_validate(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ALZA AI Data Quality Auditor"
    )

    parser.add_argument(
        "file",
        help="Path to CSV dataset",
    )

    args = parser.parse_args()

    report = run_audit(args.file)

    print()
    print("=" * 60)
    print("              ALZA AI DATA AUDITOR")
    print("=" * 60)

    print(f"\nDataset: {report.dataset}")

    print("\nDATASET")
    print("-" * 60)
    print(f"Rows:              {report.profile.rows}")
    print(f"Columns:           {report.profile.columns}")
    print(
        f"Duplicate rows:    "
        f"{report.profile.duplicate_rows}"
    )

    print("\nRULE-BASED QUALITY")
    print("-" * 60)
    print(f"Errors:            {report.summary.errors}")
    print(
        f"Warnings:          "
        f"{report.summary.warnings}"
    )

    print("\nML ANALYSIS")
    print("-" * 60)
    print(
        f"Model:             "
        f"{report.ml_analysis.model}"
    )
    print(
        f"Anomalies:         "
        f"{report.ml_analysis.anomalies_detected}"
    )

    print("\nFINDINGS")
    print("-" * 60)

    for issue in report.issues:
        location = issue.column or "dataset"

        if issue.row is not None:
            location += f" | row {issue.row}"

        print(
            f"[{issue.severity}] "
            f"{location} → "
            f"{issue.message}"
        )

    for anomaly in report.ml_analysis.anomalies:
        print(
            f"[ML] row {anomaly.row} → "
            f"{anomaly.message}"
        )

    print("\nFINAL STATUS")
    print("-" * 60)
    print(report.summary.status)

    print("=" * 60)
    print()


if __name__ == "__main__":
    main()