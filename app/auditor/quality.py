import math

import pandas as pd

from app.core.schemas import ColumnRule


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


def _normalize_rules(rules):
    if rules is None:
        return {}

    normalized = {}

    if isinstance(rules, dict):
        for key, value in rules.items():
            if isinstance(value, ColumnRule):
                normalized[value.column] = value
            elif isinstance(value, dict):
                rule_dict = dict(value)
                if "min" in rule_dict and "minimum" not in rule_dict:
                    rule_dict["minimum"] = rule_dict.pop("min")
                if "max" in rule_dict and "maximum" not in rule_dict:
                    rule_dict["maximum"] = rule_dict.pop("max")
                rule = ColumnRule(column=str(key), **rule_dict)
                normalized[rule.column] = rule
            else:
                normalized[str(key)] = ColumnRule(
                    column=str(key),
                    allowed_values=value,
                )
        return normalized

    for rule in rules:
        if isinstance(rule, ColumnRule):
            normalized[rule.column] = rule
        elif isinstance(rule, dict):
            rule_obj = ColumnRule(**rule)
            normalized[rule_obj.column] = rule_obj

    return normalized


def _matches_expected_dtype(actual_dtype: str, expected_dtype: str) -> bool:
    expected = expected_dtype.lower()
    actual = actual_dtype.lower()

    if expected in {"int", "integer", "int64", "int32"}:
        return "int" in actual or "uint" in actual

    if expected in {"float", "float64", "float32", "number", "numeric"}:
        return "float" in actual or "int" in actual or "number" in actual

    if expected in {"string", "str", "object", "text"}:
        return "str" in actual or "object" in actual or "string" in actual

    return expected == actual


def check_missing_values(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """
    Detect missing values in each column.
    """

    issues = []
    normalized_rules = _normalize_rules(rules)

    for column in df.columns:
        missing = int(df[column].isna().sum())

        if missing > 0:
            rule = normalized_rules.get(str(column))
            severity = "WARNING"
            if rule is not None and rule.severity in {"WARNING", "ERROR"}:
                severity = rule.severity
            if rule is not None and not rule.nullable and rule.severity is None:
                severity = "WARNING"

            issues.append(
                {
                    "type": "MISSING_VALUES",
                    "column": str(column),
                    "count": missing,
                    "severity": severity,
                    "message": f"{missing} missing value(s) found.",
                }
            )

    for column, rule in normalized_rules.items():
        if rule.required and column not in df.columns:
            issues.append(
                {
                    "type": "MISSING_VALUES",
                    "column": str(column),
                    "severity": rule.severity or "WARNING",
                    "message": "Required column is missing.",
                }
            )

    return issues


def check_expected_dtypes(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """Validate configured expected dtypes."""

    issues = []
    normalized_rules = _normalize_rules(rules)

    for column, rule in normalized_rules.items():
        if not rule.expected_dtype or column not in df.columns:
            continue

        actual_dtype = str(df[column].dtype)
        if not _matches_expected_dtype(actual_dtype, rule.expected_dtype):
            issues.append(
                {
                    "type": "INVALID_TYPE",
                    "column": str(column),
                    "severity": "ERROR",
                    "message": (
                        f"Column dtype is {actual_dtype}; "
                        f"expected {rule.expected_dtype}."
                    ),
                }
            )

    return issues


def check_numeric_ranges(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """
    Validate numeric columns against configured minimum
    and maximum values.
    """

    issues = []
    normalized_rules = _normalize_rules(rules)

    for column, rule in normalized_rules.items():
        if column not in df.columns:
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        minimum = rule.minimum
        maximum = rule.maximum

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
                        "severity": rule.severity or "ERROR",
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
                        "severity": rule.severity or "ERROR",
                        "message": (
                            f"Value exceeds maximum allowed "
                            f"value of {maximum}."
                        ),
                    }
                )

    return issues


def check_allowed_values(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """
    Validate categorical columns against allowed values.
    """

    issues = []
    normalized_rules = _normalize_rules(rules)

    for column, rule in normalized_rules.items():
        if column not in df.columns:
            continue

        allowed_values = rule.allowed_values
        if allowed_values is None:
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
                    "severity": rule.severity or "ERROR",
                    "message": (
                        "Value is not in the allowed "
                        "category list."
                    ),
                }
            )

    return issues


def check_unique_values(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """Validate configured unique-value constraints."""

    issues = []
    normalized_rules = _normalize_rules(rules)

    for column, rule in normalized_rules.items():
        if not rule.unique or column not in df.columns:
            continue

        invalid = df[
            df[column].duplicated(keep=False)
            & df[column].notna()
        ]

        for index in invalid.index:
            value = _to_python_value(
                invalid.loc[index, column]
            )

            issues.append(
                {
                    "type": "DUPLICATE_VALUES",
                    "column": str(column),
                    "row": int(index),
                    "value": value,
                    "severity": "WARNING",
                    "message": (
                        f"Value appears more than once in '{column}'."
                    ),
                }
            )

    return issues


def validate_columns(
    df: pd.DataFrame,
    rules: dict | list | None = None,
) -> list[dict]:
    """Run the deterministic, configurable validation rules."""

    normalized_rules = _normalize_rules(rules)
    issues = []

    issues.extend(check_missing_values(df, normalized_rules))
    issues.extend(check_expected_dtypes(df, normalized_rules))
    issues.extend(check_numeric_ranges(df, normalized_rules))
    issues.extend(check_allowed_values(df, normalized_rules))
    issues.extend(check_unique_values(df, normalized_rules))

    return issues