from __future__ import annotations

import numpy as np
import pandas as pd


def build_diagnostic_report(accidents: pd.DataFrame, model_df: pd.DataFrame) -> str:
    acc = accidents.copy()
    acc["date_time"] = pd.to_datetime(acc["date_time"], utc=True, errors="coerce")

    region_diag = (
        acc.groupby("region", as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .sort_values(["fatalities", "accidents"], ascending=False)
    )
    region_diag["severe_rate"] = (region_diag["severe"] / region_diag["accidents"]).replace(
        [np.inf, np.nan], 0.0
    )

    road_type_diag = (
        acc.groupby("road_type", as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .sort_values("severe", ascending=False)
    )
    road_type_diag["severe_rate"] = (
        road_type_diag["severe"] / road_type_diag["accidents"]
    ).replace([np.inf, np.nan], 0.0)

    lighting_diag = (
        acc.groupby("lighting", as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .sort_values("severe", ascending=False)
    )
    lighting_diag["severe_rate"] = (lighting_diag["severe"] / lighting_diag["accidents"]).replace(
        [np.inf, np.nan], 0.0
    )

    weather_diag = pd.DataFrame()
    if "weather" in acc.columns:
        weather_diag = (
            acc.groupby("weather", as_index=False)
            .agg(
                accidents=("incident_id", "count"),
                severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
                fatalities=("fatalities", "sum"),
            )
            .sort_values("severe", ascending=False)
        )
        weather_diag["severe_rate"] = (weather_diag["severe"] / weather_diag["accidents"]).replace(
            [np.inf, np.nan], 0.0
        )

    road_day_diag = pd.DataFrame()
    diag_cols = [
        c
        for c in [
            "region",
            "road_type",
            "daily_volume",
            "p95_speed",
            "total_violations",
            "violations_per_1000_volume",
            "low_visibility_hours",
            "rain_hours",
            "fog_hours",
            "severe_rate",
            "has_fatality",
        ]
        if c in model_df.columns
    ]
    if diag_cols:
        road_day_diag = model_df[diag_cols].copy()

    signals: list[tuple[str, float]] = []
    if "has_fatality" in road_day_diag.columns:
        for column in [
            "daily_volume",
            "p95_speed",
            "total_violations",
            "violations_per_1000_volume",
            "low_visibility_hours",
            "rain_hours",
            "fog_hours",
            "severe_rate",
        ]:
            if column in road_day_diag.columns:
                corr = float(road_day_diag[column].corr(road_day_diag["has_fatality"]))
                if not np.isnan(corr):
                    signals.append((column, corr))
    top_signals = sorted(signals, key=lambda item: abs(item[1]), reverse=True)[:6]

    observed_risk = model_df.copy()
    observed_hotspots = pd.DataFrame()
    if {
        "road_id",
        "date",
        "region",
        "city",
        "road_type",
        "accidents",
        "fatalities",
        "severe_rate",
    }.issubset(observed_risk.columns):
        observed_hotspots = observed_risk.sort_values(
            ["has_fatality", "severe_rate", "fatalities", "accidents"],
            ascending=False,
        ).head(10)

    lines: list[str] = []
    lines.append("# Diagnostic Report")
    lines.append("")
    lines.append(
        "This report supports diagnostic and root-cause style analysis for the solution outputs."
    )
    lines.append("")
    lines.append("## Regional Concentration")
    lines.append("| Region | Accidents | Severe | Severe Rate | Fatalities |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, row in region_diag.iterrows():
        lines.append(
            f"| {row['region']} | {int(row['accidents'])} | {int(row['severe'])} | {row['severe_rate']:.2%} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("## Road Type Comparison")
    lines.append("| Road Type | Accidents | Severe | Severe Rate | Fatalities |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, row in road_type_diag.iterrows():
        lines.append(
            f"| {row['road_type']} | {int(row['accidents'])} | {int(row['severe'])} | {row['severe_rate']:.2%} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("## Lighting Comparison")
    lines.append("| Lighting | Accidents | Severe | Severe Rate | Fatalities |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, row in lighting_diag.iterrows():
        lines.append(
            f"| {row['lighting']} | {int(row['accidents'])} | {int(row['severe'])} | {row['severe_rate']:.2%} | {int(row['fatalities'])} |"
        )
    lines.append("")
    if not weather_diag.empty:
        lines.append("## Weather Context")
        lines.append("| Weather | Accidents | Severe | Severe Rate | Fatalities |")
        lines.append("|---|---:|---:|---:|---:|")
        for _, row in weather_diag.iterrows():
            lines.append(
                f"| {row['weather']} | {int(row['accidents'])} | {int(row['severe'])} | {row['severe_rate']:.2%} | {int(row['fatalities'])} |"
            )
        lines.append("")
    lines.append("## Strongest Diagnostic Signals")
    if top_signals:
        for feature, corr in top_signals:
            direction = "positive" if corr >= 0 else "negative"
            lines.append(
                f"- {feature}: corr={corr:.3f} ({direction} association with fatality flag)"
            )
    else:
        lines.append("- Not enough stable modeled signals were available.")
    lines.append("")
    lines.append("## Priority Road-Days")
    if observed_hotspots.empty:
        lines.append("- No road-day prioritization table was available.")
    else:
        lines.append(
            "| Road | Date | Region | City | Type | Accidents | Fatalities | Severe Rate |"
        )
        lines.append("|---|---|---|---|---|---:|---:|---:|")
        for _, row in observed_hotspots.iterrows():
            road_day = (
                pd.to_datetime(row["date"]).date().isoformat() if pd.notna(row["date"]) else ""
            )
            lines.append(
                f"| {row['road_id']} | {road_day} | {row['region']} | {row['city']} | {row['road_type']} | {int(row['accidents'])} | "
                f"{int(row['fatalities'])} | {row['severe_rate']:.2%} |"
            )
    lines.append("")
    lines.append("## Root-Cause Style Hypotheses")
    lines.append(
        "- Roads with elevated severe rates should be reviewed alongside exposure, speed profile, and violation intensity rather than accident count alone."
    )
    lines.append(
        "- Low-visibility and high-speed contexts are useful diagnostic variables for targeted interventions and further field investigation."
    )
    lines.append(
        "- Regional differences in severe rate suggest operational, infrastructure, enforcement, or contextual effects that need deeper investigation with real data."
    )
    return "\n".join(lines)
