import math

import pandas as pd


def _to_python_value(value):
    """
    Convert Pandas/NumPy scalar values into native Python values
    that can be safely serialized to JSON.
    """

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and math.isnan(value):
        return None

    return value


def check_missing_values(df: pd.DataFrame) -> list[dict]:
    """
    Detect missing values in each column.
    """

    issues = []

    for column in df.columns:
        missing = int(df[column].isna().sum())

        if missing > 0:
            issues.append(
                {
                    "type": "MISSING_VALUES",
                    "column": str(column),
                    "count": missing,
                    "severity": "WARNING",
                    "message": f"{missing} missing value(s) found.",
                }
            )

    return issues


def check_numeric_ranges(
    df: pd.DataFrame,
    rules: dict[str, dict[str, float]],
) -> list[dict]:
    """
    Validate numeric columns against configured minimum
    and maximum values.
    """

    issues = []

    for column, rule in rules.items():
        if column not in df.columns:
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        minimum = rule.get("min")
        maximum = rule.get("max")

        if minimum is not None:
            invalid = df[df[column] < minimum]

            for index in invalid.index:
                value = _to_python_value(
                    invalid.loc[index, column]
                )

                issues.append(
                    {
                        "type": "INVALID_RANGE",
                        "column": str(column),
                        "row": int(index),
                        "value": value,
                        "severity": "ERROR",
                        "message": (
                            f"Value is below minimum allowed "
                            f"value of {minimum}."
                        ),
                    }
                )

        if maximum is not None:
            invalid = df[df[column] > maximum]

            for index in invalid.index:
                value = _to_python_value(
                    invalid.loc[index, column]
                )

                issues.append(
                    {
                        "type": "INVALID_RANGE",
                        "column": str(column),
                        "row": int(index),
                        "value": value,
                        "severity": "ERROR",
                        "message": (
                            f"Value exceeds maximum allowed "
                            f"value of {maximum}."
                        ),
                    }
                )

    return issues


def check_allowed_values(
    df: pd.DataFrame,
    rules: dict[str, list],
) -> list[dict]:
    """
    Validate categorical columns against allowed values.
    """

    issues = []

    for column, allowed_values in rules.items():
        if column not in df.columns:
            continue

        invalid = df[
            ~df[column].isin(allowed_values)
            & df[column].notna()
        ]

        for index in invalid.index:
            value = _to_python_value(
                invalid.loc[index, column]
            )

            issues.append(
                {
                    "type": "INVALID_CATEGORY",
                    "column": str(column),
                    "row": int(index),
                    "value": value,
                    "severity": "ERROR",
                    "message": (
                        "Value is not in the allowed "
                        "category list."
                    ),
                }
            )

    return issues