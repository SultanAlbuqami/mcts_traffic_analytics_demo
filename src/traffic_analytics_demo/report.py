from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd


def _weekly_period(series: pd.Series) -> pd.Series:
    ts = pd.to_datetime(series, utc=True, errors="coerce")
    return ts.dt.tz_convert(None).dt.to_period("W")


def build_executive_report(accidents: pd.DataFrame, model_df: pd.DataFrame) -> str:
    acc = accidents.copy()
    acc["date"] = pd.to_datetime(acc["date_time"], utc=True, errors="coerce").dt.date

    total_accidents = int(len(acc))
    total_fatalities = int(acc["fatalities"].sum())
    total_injuries = int(acc["injuries"].sum())
    severe_count = int(acc["severity"].isin(["Severe", "Fatal"]).sum())
    fatality_rate = (total_fatalities / total_accidents) if total_accidents else 0.0
    severe_rate = (severe_count / total_accidents) if total_accidents else 0.0

    severity_mix = acc["severity"].value_counts(dropna=False).to_dict()

    weekly = (
        acc.groupby(_weekly_period(acc["date_time"]))
        .agg(
            accidents=("incident_id", "count"),
            fatalities=("fatalities", "sum"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
        )
        .reset_index()
        .rename(columns={"date_time": "week"})
    )
    weekly["week"] = weekly["week"].astype(str)
    weekly_tail = weekly.tail(8)

    by_region = (
        acc.groupby(["region"], as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            fatalities=("fatalities", "sum"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
        )
        .sort_values(["fatalities", "accidents"], ascending=False)
    )
    by_region["severe_rate"] = (by_region["severe"] / by_region["accidents"]).replace(
        [np.inf, np.nan], 0
    )

    by_road = acc.groupby(["road_id", "region", "city", "road_type"], as_index=False).agg(
        accidents=("incident_id", "count"),
        severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
        fatalities=("fatalities", "sum"),
    )
    by_road["severe_rate"] = (by_road["severe"] / by_road["accidents"]).replace([np.inf, np.nan], 0)
    hotspots = (
        by_road[by_road["accidents"] >= 20]
        .sort_values(["severe_rate", "fatalities"], ascending=False)
        .head(10)
    )

    signal_candidates = [
        "mean_speed",
        "p95_speed",
        "daily_volume",
        "total_violations",
        "violations_per_1000_volume",
        "low_visibility_hours",
        "rain_hours",
        "fog_hours",
    ]
    signals = []
    if "has_fatality" in model_df.columns:
        for col in signal_candidates:
            if col in model_df.columns:
                corr = float(model_df[col].corr(model_df["has_fatality"]))
                if not np.isnan(corr):
                    signals.append((col, corr))
    top_signals = sorted(signals, key=lambda item: abs(item[1]), reverse=True)[:5]

    leading_region = by_region.iloc[0]["region"] if not by_region.empty else "n/a"
    leading_hotspot = hotspots.iloc[0]["road_id"] if not hotspots.empty else "n/a"

    lines = []
    lines.append("# Executive Analytics Report - Traffic Safety Demo")
    lines.append("")
    lines.append(f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- Total accidents: **{total_accidents:,}**")
    lines.append(f"- Total fatalities: **{total_fatalities:,}**")
    lines.append(f"- Total injuries: **{total_injuries:,}**")
    lines.append(f"- Severe accident rate: **{severe_rate:.1%}**")
    lines.append(f"- Fatality rate per accident: **{fatality_rate:.1%}**")
    lines.append("")
    lines.append("## Severity Mix")
    for severity, value in severity_mix.items():
        lines.append(f"- {severity}: {int(value):,}")
    lines.append("")
    lines.append("## Weekly Trend (last 8 weeks)")
    lines.append("| Week | Accidents | Severe | Fatalities |")
    lines.append("|---|---:|---:|---:|")
    for _, row in weekly_tail.iterrows():
        lines.append(
            f"| {row['week']} | {int(row['accidents'])} | {int(row['severe'])} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("## Regions Requiring Attention")
    lines.append("| Region | Accidents | Severe | Severe Rate | Fatalities |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, row in by_region.head(5).iterrows():
        lines.append(
            f"| {row['region']} | {int(row['accidents'])} | {int(row['severe'])} | "
            f"{row['severe_rate']:.2%} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("## Top Hotspots (min 20 accidents)")
    lines.append("| Road | Region | City | Type | Accidents | Severe | Severe Rate | Fatalities |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|")
    for _, row in hotspots.iterrows():
        lines.append(
            f"| {row['road_id']} | {row['region']} | {row['city']} | {row['road_type']} | {int(row['accidents'])} | "
            f"{int(row['severe'])} | {row['severe_rate']:.2%} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("## Diagnostic Signals (correlation against road-day fatality flag)")
    if top_signals:
        for feature, corr in top_signals:
            direction = "higher risk" if corr >= 0 else "lower risk"
            lines.append(f"- {feature}: corr={corr:.3f} ({direction})")
    else:
        lines.append(
            "- Not enough modeled features were available to compute stable diagnostic signals."
        )
    lines.append("")
    lines.append("## Decision Notes")
    lines.append(
        f"- Prioritize detailed review for **{leading_region}** and hotspot **{leading_hotspot}**."
    )
    lines.append(
        "- Use road-day exposure, violations, and adverse-weather context together; raw accident counts alone are insufficient."
    )
    lines.append(
        "- For executive use, keep this output paired with the quality report and model report before publishing dashboards."
    )
    lines.append("")
    lines.append("## Assumptions and Limitations")
    lines.append("- This demo uses synthetic data to demonstrate governed analytics methodology.")
    lines.append(
        "- Production deployment would add entity-level SLAs, refresh monitoring, and approval workflows."
    )
    return "\n".join(lines)
