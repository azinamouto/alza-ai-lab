from pathlib import Path

import pandas as pd


def profile_csv(file_path: str) -> dict:
    """
    Profile a CSV dataset and return structural information.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    if path.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are supported.")

    df = pd.read_csv(path)

    column_profiles = []

    for column in df.columns:
        series = df[column]

        column_profiles.append(
            {
                "name": column,
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_percentage": round(
                    float(series.isna().mean() * 100),
                    2,
                ),
                "unique_values": int(
                    series.nunique(dropna=True)
                ),
            }
        )

    return {
        "dataset": path.name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_profiles": column_profiles,
    }