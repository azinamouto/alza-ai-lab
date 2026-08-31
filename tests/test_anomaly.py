import pandas as pd

from app.auditor.anomaly import detect_anomalies, select_ml_features
from app.core.schemas import ColumnRule


def test_anomaly_detection():
    df = pd.DataFrame(
        {
            "age": [
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                1500,
            ],
            "income": [
                15000,
                16000,
                17000,
                18000,
                19000,
                20000,
                21000,
                22000,
                23000,
                9999999,
            ],
        }
    )

    anomalies = detect_anomalies(
        df,
        contamination=0.1,
    )

    assert len(anomalies) >= 1
    assert all(
        anomaly["type"] == "ML_ANOMALY"
        for anomaly in anomalies
    )


def test_select_ml_features_numeric_fallback_remains_default():
    df = pd.DataFrame(
        {
            "age": [25, 30, 35],
            "salary": [25000, 30000, 35000],
        }
    )

    selected = select_ml_features(df)

    assert list(selected.columns) == ["age", "salary"]


def test_select_ml_features_explicit_exclusion():
    df = pd.DataFrame(
        {
            "employee_id": [1001, 1002, 1003],
            "age": [25, 30, 35],
            "salary": [25000, 30000, 35000],
        }
    )

    selected = select_ml_features(
        df,
        [ColumnRule(column="employee_id", include_in_ml=False)],
    )

    assert list(selected.columns) == ["age", "salary"]


def test_select_ml_features_explicit_inclusion_keeps_numeric_column():
    df = pd.DataFrame(
        {
            "age": [25, 30, 35],
            "salary": [25000, 30000, 35000],
        }
    )

    selected = select_ml_features(
        df,
        [ColumnRule(column="salary", include_in_ml=True)],
    )

    assert list(selected.columns) == ["age", "salary"]


def test_select_ml_features_non_numeric_explicit_include_is_ignored():
    df = pd.DataFrame(
        {
            "department": ["HR", "IT", "Finance"],
            "age": [25, 30, 35],
        }
    )

    selected = select_ml_features(
        df,
        [ColumnRule(column="department", include_in_ml=True)],
    )

    assert list(selected.columns) == ["age"]


def test_select_ml_features_mixed_rules_only_keep_allowed_numeric_columns():
    df = pd.DataFrame(
        {
            "employee_id": [1001, 1002, 1003],
            "age": [25, 30, 35],
            "salary": [25000, 30000, 35000],
            "department": ["HR", "IT", "Finance"],
        }
    )

    selected = select_ml_features(
        df,
        [
            ColumnRule(column="employee_id", include_in_ml=False),
            ColumnRule(column="age", include_in_ml=True),
            ColumnRule(column="salary", include_in_ml=True),
            ColumnRule(column="department", include_in_ml=False),
        ],
    )

    assert list(selected.columns) == ["age", "salary"]


def test_select_ml_features_no_usable_numeric_columns_is_safe():
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "department": ["HR", "IT", "Finance"],
            "barangay": ["A", "B", "C"],
        }
    )

    selected = select_ml_features(df)

    assert selected.empty
    assert detect_anomalies(df) == []