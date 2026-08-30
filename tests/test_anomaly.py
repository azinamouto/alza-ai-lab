import pandas as pd

from app.auditor.anomaly import detect_anomalies


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