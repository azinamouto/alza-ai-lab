import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.1,
) -> list[dict]:
    """
    Detect statistically unusual rows using Isolation Forest.

    Only numeric columns are considered by the initial model.
    """

    numeric_df = df.select_dtypes(include="number").copy()

    if numeric_df.empty:
        return []

    # Replace missing numeric values with column medians
    # so the ML model can process the dataset.
    numeric_df = numeric_df.fillna(
        numeric_df.median(numeric_only=True)
    )

    # Remove columns that still contain NaN values
    # (for example, an entirely empty numeric column).
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