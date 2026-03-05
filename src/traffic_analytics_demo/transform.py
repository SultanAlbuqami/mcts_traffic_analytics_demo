from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROAD_ATTRS = ["region", "city", "road_type", "speed_limit", "lanes"]
WEATHER_ATTRS = ["weather", "visibility_km", "precip_mm", "temp_c"]


def _merge_missing_columns(
    base: pd.DataFrame,
    lookup: pd.DataFrame,
    keys: list[str],
    candidate_cols: list[str],
) -> pd.DataFrame:
    missing = [c for c in candidate_cols if c not in base.columns and c in lookup.columns]
    if not missing:
        return base

    cols = list(dict.fromkeys([*keys, *missing]))
    return base.merge(lookup[cols].drop_duplicates(subset=keys), on=keys, how="left")


def _mode_or_na(series: pd.Series) -> object:
    modes = series.mode(dropna=True)
    if modes.empty:
        return pd.NA
    return modes.iloc[0]


def clean_and_integrate(sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    roads = sources["roads"].copy()
    accidents = sources["accidents"].copy()
    violations = sources["violations"].copy()
    sensors = sources["sensors"].copy()
    weather = sources["weather"].copy()

    for df in [accidents, violations, sensors, weather]:
        df["date_time"] = pd.to_datetime(df["date_time"], utc=True, errors="coerce")

    roads = roads.drop_duplicates(subset=["road_id"]).copy()

    accidents = accidents.dropna(subset=["incident_id", "road_id", "date_time"]).copy()
    accidents["injuries"] = accidents["injuries"].fillna(0).clip(0, 20).astype(int)
    accidents["fatalities"] = accidents["fatalities"].fillna(0).clip(0, 10).astype(int)
    accidents["vehicles_involved"] = (
        accidents["vehicles_involved"].fillna(1).clip(1, 30).astype(int)
    )
    accidents["date"] = accidents["date_time"].dt.date

    violations = violations.dropna(
        subset=["violation_id", "road_id", "date_time", "violation_type"]
    ).copy()
    violations["fine_amount"] = violations["fine_amount"].fillna(0).clip(0, 10000).astype(int)
    violations["date"] = violations["date_time"].dt.date

    sensors = sensors.dropna(subset=["road_id", "date_time"]).copy()
    sensors["volume"] = sensors["volume"].fillna(0).clip(0, 500).astype(int)
    sensors["avg_speed"] = sensors["avg_speed"].fillna(sensors["avg_speed"].median()).clip(0, 220)
    sensors["date"] = sensors["date_time"].dt.date

    road_lookup = roads[["road_id", *ROAD_ATTRS]].copy()
    accidents = _merge_missing_columns(accidents, road_lookup, ["road_id"], ROAD_ATTRS)

    weather["hour"] = weather["date_time"].dt.floor("h")
    accidents["hour"] = accidents["date_time"].dt.floor("h")
    if {"region", "city"}.issubset(accidents.columns):
        weather_lookup = weather[["hour", "region", "city", *WEATHER_ATTRS]].copy()
        accidents = _merge_missing_columns(
            accidents, weather_lookup, ["hour", "region", "city"], WEATHER_ATTRS
        )
    accidents.drop(columns=["hour"], inplace=True, errors="ignore")

    exposure = sensors.groupby(["road_id", "date"], as_index=False).agg(
        daily_volume=("volume", "sum"),
        mean_speed=("avg_speed", "mean"),
        p95_speed=("avg_speed", lambda s: float(np.percentile(s, 95))),
        sensor_events=("sensor_id", "count"),
    )

    vio_counts = (
        violations.pivot_table(
            index=["road_id", "date"],
            columns="violation_type",
            values="violation_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    violation_cols = [c for c in vio_counts.columns if c not in ["road_id", "date"]]
    if violation_cols:
        vio_counts["total_violations"] = vio_counts[violation_cols].sum(axis=1)

    acc_day = accidents.groupby(["road_id", "date"], as_index=False).agg(
        accidents=("incident_id", "count"),
        injuries=("injuries", "sum"),
        fatalities=("fatalities", "sum"),
        severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
    )

    weather_daily = (
        weather.assign(date=weather["date_time"].dt.date)
        .groupby(["region", "city", "date"], as_index=False)
        .agg(
            weather_mode=("weather", _mode_or_na),
            low_visibility_hours=("visibility_km", lambda s: int((s < 4).sum())),
            rain_hours=("weather", lambda s: int((s == "Rain").sum())),
            fog_hours=("weather", lambda s: int((s == "Fog").sum())),
            max_precip_mm=("precip_mm", "max"),
            avg_temp_c=("temp_c", "mean"),
        )
    )

    model_df = exposure.merge(vio_counts, on=["road_id", "date"], how="left").merge(
        acc_day,
        on=["road_id", "date"],
        how="left",
    )
    model_df = model_df.merge(road_lookup, on="road_id", how="left")
    model_df = model_df.merge(weather_daily, on=["region", "city", "date"], how="left")

    for col in ["region", "city", "road_type", "weather_mode"]:
        if col in model_df.columns:
            model_df[col] = model_df[col].fillna("Unknown")

    numeric_cols = [
        c
        for c in model_df.columns
        if c not in ["road_id", "date", "region", "city", "road_type", "weather_mode"]
    ]
    for col in numeric_cols:
        model_df[col] = model_df[col].fillna(0)

    model_df["has_fatality"] = (model_df["fatalities"] > 0).astype(int)
    model_df["severe_rate"] = (
        model_df["severe"] / model_df["accidents"].replace(0, np.nan)
    ).fillna(0.0)
    model_df["violations_per_1000_volume"] = (
        (model_df.get("total_violations", 0) * 1000) / model_df["daily_volume"].replace(0, np.nan)
    ).fillna(0.0)

    return {
        "roads": roads,
        "accidents": accidents,
        "violations": violations,
        "sensors": sensors,
        "model_df": model_df,
    }


def save_processed(processed_dir: Path, dfs: dict[str, pd.DataFrame]) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    for name, df in dfs.items():
        df.to_csv(processed_dir / f"{name}.csv", index=False)
