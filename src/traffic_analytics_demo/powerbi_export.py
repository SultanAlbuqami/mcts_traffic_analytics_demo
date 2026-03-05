from __future__ import annotations

from pathlib import Path

import pandas as pd

TRACEABILITY_COLS = ["source_system", "ingest_batch_id", "record_hash"]


def _normalize_traceability(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for col in TRACEABILITY_COLS:
        if col in normalized.columns:
            continue
        for candidate in [f"{col}_x", f"{col}_accident", f"{col}_source"]:
            if candidate in normalized.columns:
                normalized = normalized.rename(columns={candidate: col})
                break
    return normalized


def _write_powerbi_guidance(out_dir: Path) -> None:
    measures = """
-- Core KPIs
Accidents = COUNTROWS(fact_accident)
Fatalities = SUM(fact_accident[fatalities])
Injuries = SUM(fact_accident[injuries])
Severe Accidents =
CALCULATE(
    [Accidents],
    fact_accident[severity] IN {"Severe", "Fatal"}
)
Severe Rate = DIVIDE([Severe Accidents], [Accidents])

-- Exposure / violations
Violations = COUNTROWS(fact_violation)
Total Fines = SUM(fact_violation[fine_amount])
Avg Sensor Speed = AVERAGE(fact_sensor[avg_speed])
Road-Day Fatality Flag Rate = AVERAGE(fact_road_day[has_fatality])
Road-Day Severe Rate = AVERAGE(fact_road_day[severe_rate])
""".strip()
    (out_dir / "measures.dax").write_text(measures, encoding="utf-8")

    notes = """
# Power BI Model Notes

Recommended relationships:
- fact_accident[road_id] -> dim_road[road_id]
- fact_violation[road_id] -> dim_road[road_id]
- fact_sensor[road_id] -> dim_road[road_id]
- fact_road_day[road_id] -> dim_road[road_id]
- fact_*[date] -> dim_date[date]

Suggested report pages:
1. Executive overview: KPI cards, weekly trend, hotspot table.
2. Operations diagnostics: region/road type drill-down, violation mix, exposure vs severity.
3. Predictive monitoring: fatality-risk road-days and adverse-weather overlays.
4. Intervention planning: scenario_summary.csv and scenario_region_impact.csv for action-package comparisons.
""".strip()
    (out_dir / "model_notes.md").write_text(notes, encoding="utf-8")


def export_star_schema(processed: dict[str, pd.DataFrame], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    accidents = _normalize_traceability(processed["accidents"]).copy()
    roads = processed["roads"].drop_duplicates(subset=["road_id"]).copy()
    violations = _normalize_traceability(processed["violations"]).copy()
    sensors = _normalize_traceability(processed["sensors"]).copy()
    model_df = processed.get("model_df")

    dim_road = roads[["road_id", "region", "city", "road_type", "speed_limit", "lanes"]].copy()
    dim_road.to_csv(out_dir / "dim_road.csv", index=False)

    dates = pd.concat(
        [
            pd.to_datetime(accidents["date_time"], utc=True, errors="coerce"),
            pd.to_datetime(violations["date_time"], utc=True, errors="coerce"),
            pd.to_datetime(sensors["date_time"], utc=True, errors="coerce"),
        ],
        ignore_index=True,
    ).dropna()
    dim_date = pd.DataFrame({"date_time": dates.dt.floor("D").unique()})
    dim_date["date"] = dim_date["date_time"].dt.date.astype(str)
    dim_date["year"] = dim_date["date_time"].dt.year
    dim_date["month"] = dim_date["date_time"].dt.month
    dim_date["month_name"] = dim_date["date_time"].dt.month_name()
    dim_date["day"] = dim_date["date_time"].dt.day
    dim_date["dow"] = dim_date["date_time"].dt.day_name()
    dim_date["week"] = dim_date["date_time"].dt.isocalendar().week.astype(int)
    dim_date.to_csv(out_dir / "dim_date.csv", index=False)

    fact_accident = accidents[
        [
            "incident_id",
            "date_time",
            "road_id",
            "severity",
            "vehicles_involved",
            "injuries",
            "fatalities",
            "weather",
            "visibility_km",
            "precip_mm",
            "temp_c",
            *TRACEABILITY_COLS,
        ]
    ].copy()
    fact_accident["date"] = pd.to_datetime(fact_accident["date_time"], utc=True).dt.date.astype(str)
    fact_accident.to_csv(out_dir / "fact_accident.csv", index=False)

    fact_violation = violations[
        [
            "violation_id",
            "date_time",
            "road_id",
            "violation_type",
            "fine_amount",
            "driver_age_band",
            *TRACEABILITY_COLS,
        ]
    ].copy()
    fact_violation["date"] = pd.to_datetime(fact_violation["date_time"], utc=True).dt.date.astype(
        str
    )
    fact_violation.to_csv(out_dir / "fact_violation.csv", index=False)

    fact_sensor = sensors[
        [
            "sensor_id",
            "date_time",
            "road_id",
            "volume",
            "avg_speed",
            *TRACEABILITY_COLS,
        ]
    ].copy()
    fact_sensor["date"] = pd.to_datetime(fact_sensor["date_time"], utc=True).dt.date.astype(str)
    fact_sensor.to_csv(out_dir / "fact_sensor.csv", index=False)

    if model_df is not None:
        fact_road_day_cols = [
            "road_id",
            "date",
            "region",
            "city",
            "road_type",
            "speed_limit",
            "lanes",
            "weather_mode",
            "daily_volume",
            "mean_speed",
            "p95_speed",
            "sensor_events",
            "total_violations",
            "violations_per_1000_volume",
            "accidents",
            "injuries",
            "fatalities",
            "severe",
            "severe_rate",
            "has_fatality",
            "low_visibility_hours",
            "rain_hours",
            "fog_hours",
            "max_precip_mm",
            "avg_temp_c",
        ]
        existing_cols = [c for c in fact_road_day_cols if c in model_df.columns]
        fact_road_day = model_df[existing_cols].copy()
        fact_road_day["date"] = pd.to_datetime(fact_road_day["date"]).dt.date.astype(str)
        fact_road_day.to_csv(out_dir / "fact_road_day.csv", index=False)

    _write_powerbi_guidance(out_dir)
