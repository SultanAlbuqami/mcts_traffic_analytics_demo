from __future__ import annotations

import pandas as pd

from traffic_analytics_demo.quality import run_quality_checks


def test_quality_rules_smoke() -> None:
    current_day = pd.Timestamp.now(tz="UTC").normalize()

    roads = pd.DataFrame(
        {
            "road_id": ["R0001"],
            "region": ["Riyadh"],
            "city": ["Riyadh"],
            "road_type": ["Urban"],
            "speed_limit": [60],
            "lanes": [3],
        }
    )
    accidents = pd.DataFrame(
        {
            "incident_id": ["A000001"],
            "date_time": [current_day.isoformat()],
            "road_id": ["R0001"],
            "region": ["Riyadh"],
            "city": ["Riyadh"],
            "road_type": ["Urban"],
            "severity": ["Minor"],
            "fatalities": [0],
            "injuries": [1],
            "vehicles_involved": [2],
            "source_system": ["accident_reports"],
            "ingest_batch_id": ["B20260101T000000Z"],
            "record_hash": ["abc123"],
            "weather": ["Clear"],
        }
    )
    model_df = pd.DataFrame(
        {
            "road_id": ["R0001"],
            "date": [current_day.date().isoformat()],
            "p95_speed": [80],
            "daily_volume": [100],
            "mean_speed": [65],
            "total_violations": [4],
            "accidents": [1],
            "fatalities": [0],
            "region": ["Riyadh"],
            "city": ["Riyadh"],
            "road_type": ["Urban"],
            "violations_per_1000_volume": [40.0],
            "weather_mode": ["Clear"],
            "has_fatality": [0],
        }
    )

    results, summary = run_quality_checks(
        {"roads": roads, "accidents": accidents, "model_df": model_df}
    )

    assert summary["total"] >= 20
    assert summary["fail"] == 0
    assert all(result.status in {"PASS", "WARN", "FAIL"} for result in results)
