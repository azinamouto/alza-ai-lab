import pandas as pd
from sklearn.ensemble import IsolationForest

from app.auditor.quality import _normalize_rules


def select_ml_features(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> pd.DataFrame:
    """Select columns eligible for IsolationForest."""

    normalized_rules = _normalize_rules(rules)
    selected_columns = []

    for column in df.columns:
        rule = normalized_rules.get(str(column))

        if rule is not None and rule.include_in_ml is False:
            continue

        if rule is not None and rule.include_in_ml is True:
            if pd.api.types.is_numeric_dtype(df[column]):
                selected_columns.append(str(column))
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            selected_columns.append(str(column))

    return df.loc[:, selected_columns].copy()


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.1,
    rules: dict | list | None = None,
) -> list[dict]:
    """
    Detect statistically unusual rows using Isolation Forest.

    Numeric columns are selected only after explicit governance rules are applied.
    """

    numeric_df = select_ml_features(df, rules).copy()

    if numeric_df.empty:
        return []

    numeric_df = numeric_df.fillna(
        numeric_df.median(numeric_only=True)
    )

    numeric_df = numeric_df.dropna(axis=1, how="all")

    if numeric_df.empty:
        return []

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
    )

    predictions = model.fit_predict(numeric_df)

    scores = model.decision_function(numeric_df)

    anomalies = []

    for index, prediction in enumerate(predictions):
        if prediction == -1:
            anomalies.append(
                {
                    "type": "ML_ANOMALY",
                    "row": int(df.index[index]),
                    "anomaly_score": float(scores[index]),
                    "severity": "WARNING",
                    "message": (
                        "This row was identified as "
                        "statistically unusual by the "
                        "anomaly detection model."
                    ),
                }
            )

    return anomalies