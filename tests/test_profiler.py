import pandas as pd

from app.auditor.profiler import profile_csv


def test_duplicate_rows(tmp_path):
    csv_path = tmp_path / "duplicate_rows.csv"
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Alice", "Charlie", "Bob"],
            "age": [30, 40, 30, 50, 40],
        }
    )
    df.to_csv(csv_path, index=False)

    profile = profile_csv(str(csv_path))

    assert profile["rows"] == 5
    assert profile["duplicate_rows"] == 2
