import pandas as pd

from app.auditor.quality import (
    check_allowed_values,
    check_missing_values,
    check_numeric_ranges,
)


def test_missing_values():
    df = pd.DataFrame(
        {
            "name": ["Juan", None, "Pedro"],
        }
    )

    issues = check_missing_values(df)

    assert len(issues) == 1
    assert issues[0]["type"] == "MISSING_VALUES"


def test_numeric_range():
    df = pd.DataFrame(
        {
            "age": [21, 25, -50, 30],
        }
    )

    issues = check_numeric_ranges(
        df,
        {
            "age": {
                "min": 0,
                "max": 120,
            }
        },
    )

    assert len(issues) == 1
    assert issues[0]["value"] == -50


def test_allowed_values():
    df = pd.DataFrame(
        {
            "gender": ["M", "F", "X"],
        }
    )

    issues = check_allowed_values(
        df,
        {
            "gender": ["M", "F"],
        },
    )

    assert len(issues) == 1
    assert issues[0]["value"] == "X"