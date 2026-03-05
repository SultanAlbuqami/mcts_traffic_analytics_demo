from __future__ import annotations

import pandas as pd

from traffic_analytics_demo.stakeholder_pack import build_stakeholder_pack


def test_stakeholder_pack_contains_expected_sections() -> None:
    accidents = pd.DataFrame(
        {
            "incident_id": ["I1", "I2"],
            "date_time": ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z"],
            "fatalities": [1, 0],
            "injuries": [2, 1],
            "severity": ["Fatal", "Severe"],
            "region": ["North", "North"],
            "road_id": ["R1", "R2"],
            "city": ["C1", "C1"],
            "road_type": ["Highway", "Urban"],
        }
    )
    model_df = pd.DataFrame({"has_fatality": [1, 0], "violations_per_1000_volume": [2.0, 3.0]})
    scenario = pd.DataFrame(
        {
            "scenario": ["A"],
            "avg_risk_reduction": [0.1],
            "high_risk_road_days_reduced": [4],
        }
    )

    text = build_stakeholder_pack(accidents, model_df, quality_gate="PASS", scenario_summary=scenario)

    assert "Executive Board Brief" in text
    assert "Operations Command Brief" in text
    assert "Governance and Compliance Brief" in text
    assert "Data & Analytics Team Brief" in text
