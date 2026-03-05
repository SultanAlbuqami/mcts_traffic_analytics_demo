from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def build_stakeholder_pack(
    accidents: pd.DataFrame,
    model_df: pd.DataFrame,
    quality_gate: str,
    scenario_summary: pd.DataFrame | None = None,
) -> str:
    acc = accidents.copy()
    acc["date"] = pd.to_datetime(acc["date_time"], utc=True, errors="coerce").dt.date

    total_accidents = int(len(acc))
    total_fatalities = int(acc["fatalities"].sum())
    total_injuries = int(acc["injuries"].sum())
    severe_count = int(acc["severity"].isin(["Severe", "Fatal"]).sum())
    severe_rate = (severe_count / total_accidents) if total_accidents else 0.0

    by_region = (
        acc.groupby("region", as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            fatalities=("fatalities", "sum"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
        )
        .sort_values(["fatalities", "accidents"], ascending=False)
    )
    leading_region = by_region.iloc[0]["region"] if not by_region.empty else "n/a"

    hotspots = (
        acc.groupby(["road_id", "region", "city", "road_type"], as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .sort_values(["fatalities", "accidents"], ascending=False)
        .head(10)
    )

    model_positive_rate = float(model_df["has_fatality"].mean()) if "has_fatality" in model_df.columns else 0.0
    avg_violation_intensity = (
        float(model_df["violations_per_1000_volume"].mean()) if "violations_per_1000_volume" in model_df.columns else 0.0
    )

    best_scenario_text = "n/a"
    if scenario_summary is not None and not scenario_summary.empty:
        top = scenario_summary.sort_values(
            ["avg_risk_reduction", "high_risk_road_days_reduced"],
            ascending=False,
        ).iloc[0]
        best_scenario_text = (
            f"{top['scenario']} (avg_risk_reduction={top['avg_risk_reduction']:.4f}, "
            f"high_risk_road_days_reduced={int(top['high_risk_road_days_reduced'])})"
        )

    lines: list[str] = []
    lines.append("# Stakeholder Pack - Traffic Safety Analytics")
    lines.append("")
    lines.append(f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## 1) Executive Board Brief")
    lines.append(f"- Total accidents: **{total_accidents:,}**")
    lines.append(f"- Total fatalities: **{total_fatalities:,}**")
    lines.append(f"- Severe incident rate: **{severe_rate:.1%}**")
    lines.append(f"- Quality gate status: **{quality_gate}**")
    lines.append(f"- Best intervention package: **{best_scenario_text}**")
    lines.append("")
    lines.append("Decision note: prioritize funding and enforcement in top-risk region while preserving governance controls.")
    lines.append("")
    lines.append("## 2) Operations Command Brief")
    lines.append(f"- Leading risk region: **{leading_region}**")
    lines.append(f"- Model positive rate (road-day fatality flag): **{model_positive_rate:.2%}**")
    lines.append(f"- Avg violations per 1000 volume: **{avg_violation_intensity:.2f}**")
    lines.append("")
    lines.append("| Road | Region | City | Type | Accidents | Severe | Fatalities |")
    lines.append("|---|---|---|---|---:|---:|---:|")
    for _, row in hotspots.head(8).iterrows():
        lines.append(
            f"| {row['road_id']} | {row['region']} | {row['city']} | {row['road_type']} | "
            f"{int(row['accidents'])} | {int(row['severe'])} | {int(row['fatalities'])} |"
        )
    lines.append("")
    lines.append("Action note: use hotspot + exposure + violation intensity jointly for deployment decisions.")
    lines.append("")
    lines.append("## 3) Governance and Compliance Brief")
    lines.append("- Data is synthetic in this demo; no personal data should be used without legal basis in production.")
    lines.append("- Traceability fields (`source_system`, `ingest_batch_id`, `record_hash`) are required controls.")
    lines.append("- Release of dashboards should be conditioned on quality gate and documented assumptions.")
    lines.append("")
    lines.append("## 4) Data & Analytics Team Brief")
    lines.append("- Reproducible pipeline path: raw -> staged -> curated -> reporting.")
    lines.append("- Validate model limitations and group-level metrics before policy recommendations.")
    lines.append("- Track drift, calibration, and quality trends across refresh cycles in production.")
    lines.append("")
    lines.append("## 5) Assumptions and Limitations")
    lines.append("- Synthetic data and simplified operational assumptions.")
    lines.append("- Not a substitute for legal/regulatory review in real deployments.")
    lines.append("")
    lines.append("## 6) Ministerial Committee Reporting Lens")
    lines.append("- Supports periodic reporting readiness to economic/development governance bodies through standardized metrics.")
    lines.append("- Enables cross-entity performance monitoring using shared KPI definitions and traceability controls.")
    lines.append("- Helps reduce initiative conflicts by aligning strategy, diagnostics, and intervention outputs in one governed pack.")
    return "\n".join(lines)
