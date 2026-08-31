import pandas as pd

from app.auditor.quality import (
    check_allowed_values,
    check_missing_values,
    check_numeric_ranges,
    check_unique_values,
    validate_columns,
)
from app.core.schemas import ColumnRule


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


def test_configured_numeric_range_rule():
    df = pd.DataFrame(
        {
            "barangay": ["Talibon", "San Jose", "Loon"],
            "population": [68000, 12000, -500],
        }
    )

    issues = check_numeric_ranges(
        df,
        [
            ColumnRule(
                column="population",
                minimum=0,
            )
        ],
    )

    assert len(issues) == 1
    assert issues[0]["column"] == "population"
    assert issues[0]["value"] == -500


def test_configured_allowed_values_rule():
    df = pd.DataFrame(
        {
            "product": ["Rice", "Bread", "Pasta"],
            "price": [500, 100, 250],
        }
    )

    issues = check_allowed_values(
        df,
        [
            ColumnRule(
                column="product",
                allowed_values=["Rice", "Bread"],
            )
        ],
    )

    assert len(issues) == 1
    assert issues[0]["column"] == "product"
    assert issues[0]["value"] == "Pasta"


def test_configured_required_nullable_and_unique_rules():
    df = pd.DataFrame(
        {
            "city": ["Tagbilaran", None, "Duero"],
            "code": ["A", "A", "B"],
        }
    )

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="city",
                required=True,
                nullable=False,
            ),
            ColumnRule(
                column="code",
                unique=True,
                nullable=False,
            ),
        ],
    )

    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "city"
        for issue in issues
    )
    assert any(
        issue["type"] == "DUPLICATE_VALUES"
        and issue["column"] == "code"
        for issue in issues
    )

    unique_issues = check_unique_values(
        df,
        [
            ColumnRule(
                column="code",
                unique=True,
            )
        ],
    )

    assert len(unique_issues) == 2
    assert unique_issues[0]["value"] == "A"


def test_required_column_missing():
    df = pd.DataFrame({"name": ["Alice", "Bob"]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="age",
                required=True,
            )
        ],
    )

    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "age"
        and issue["severity"] == "WARNING"
        for issue in issues
    )


def test_nullable_false_does_not_duplicate_missing_findings():
    df = pd.DataFrame({"age": [20, None, 30]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="age",
                nullable=False,
            )
        ],
    )

    age_missing_issues = [
        issue
        for issue in issues
        if issue["type"] == "MISSING_VALUES"
        and issue["column"] == "age"
    ]

    assert len(age_missing_issues) == 1
    assert age_missing_issues[0]["severity"] == "WARNING"


def test_nullable_true_keeps_generic_missing_warning():
    df = pd.DataFrame({"age": [20, None, 30]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="age",
                nullable=True,
            )
        ],
    )

    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "age"
        for issue in issues
    )


def test_expected_dtype_rule():
    numeric_df = pd.DataFrame({"score": pd.Series([1, 2, 3], dtype="int64")})
    invalid_df = pd.DataFrame({"score": [1, "two", 3]})

    valid_issues = validate_columns(
        numeric_df,
        [ColumnRule(column="score", expected_dtype="int")],
    )
    invalid_issues = validate_columns(
        invalid_df,
        [ColumnRule(column="score", expected_dtype="int")],
    )

    assert valid_issues == []
    assert any(
        issue["type"] == "INVALID_TYPE"
        and issue["column"] == "score"
        for issue in invalid_issues
    )


def test_unique_value_rule():
    unique_df = pd.DataFrame({"code": ["A", "B", "C"]})
    duplicate_df = pd.DataFrame({"code": ["A", "A", "B"]})

    unique_issues = validate_columns(
        unique_df,
        [ColumnRule(column="code", unique=True)],
    )
    duplicate_issues = validate_columns(
        duplicate_df,
        [ColumnRule(column="code", unique=True)],
    )

    assert unique_issues == []
    assert any(
        issue["type"] == "DUPLICATE_VALUES"
        and issue["column"] == "code"
        and issue["value"] == "A"
        for issue in duplicate_issues
    )


def test_minimum_maximum_boundaries_are_respected():
    df = pd.DataFrame({"score": [-1, 0, 50, 100, 101]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="score",
                minimum=0,
                maximum=100,
            )
        ],
    )

    range_values = [
        issue["value"]
        for issue in issues
        if issue["type"] == "INVALID_RANGE"
        and issue["column"] == "score"
    ]

    assert sorted(range_values) == [-1, 101]


def test_configured_severity_overrides_default():
    df = pd.DataFrame({"score": [-1]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="score",
                minimum=0,
                severity="WARNING",
            )
        ],
    )

    assert len(issues) == 1
    assert issues[0]["severity"] == "WARNING"
    assert issues[0]["type"] == "INVALID_RANGE"


def test_multiple_rules_on_one_column():
    df = pd.DataFrame({"age": [None, 130, 30]})

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="age",
                expected_dtype="int",
                minimum=0,
                maximum=120,
                nullable=False,
            )
        ],
    )

    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "age"
        for issue in issues
    )
    assert any(
        issue["type"] == "INVALID_RANGE"
        and issue["column"] == "age"
        and issue["value"] == 130
        for issue in issues
    )


def test_unconfigured_columns_are_not_validated():
    df = pd.DataFrame(
        {
            "barangay": ["Talibon", "San Jose"],
            "population": [68000, 12000],
            "households": [16000, 3000],
        }
    )

    issues = validate_columns(
        df,
        [
            ColumnRule(
                column="population",
                minimum=0,
            )
        ],
    )

    assert issues == []


def test_empty_and_all_null_data_do_not_crash():
    empty_df = pd.DataFrame()
    all_null_numeric = pd.DataFrame({"score": [None, None]})
    all_null_categorical = pd.DataFrame({"status": [None, None]})

    empty_issues = validate_columns(
        empty_df,
        [ColumnRule(column="score", minimum=0)],
    )
    numeric_issues = validate_columns(
        all_null_numeric,
        [ColumnRule(column="score", minimum=0)],
    )
    categorical_issues = validate_columns(
        all_null_categorical,
        [ColumnRule(column="status", allowed_values=["A", "B"])],
    )

    assert empty_issues == []
    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "score"
        and issue["severity"] == "WARNING"
        for issue in numeric_issues
    )
    assert any(
        issue["type"] == "MISSING_VALUES"
        and issue["column"] == "status"
        and issue["severity"] == "WARNING"
        for issue in categorical_issues
    )