from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.pipeline import Pipeline

from .model import get_model_feature_columns


@dataclass(frozen=True)
class ScenarioAnalysis:
    summary: pd.DataFrame
    top_opportunities: pd.DataFrame
    region_impact: pd.DataFrame


def _apply_speed_management(df: pd.DataFrame) -> pd.DataFrame:
    adjusted = df.copy()
    if "mean_speed" in adjusted.columns:
        adjusted["mean_speed"] = adjusted["mean_speed"] * 0.92
    if "p95_speed" in adjusted.columns:
        adjusted["p95_speed"] = adjusted["p95_speed"] * 0.88
    return adjusted


def _apply_enforcement(df: pd.DataFrame) -> pd.DataFrame:
    adjusted = df.copy()
    factor = 0.78
    for col in ["total_violations", "violations_per_1000_volume", "Speeding", "UnsafeLaneChange", "RedLight"]:
        if col in adjusted.columns:
            adjusted[col] = adjusted[col] * factor
    return adjusted


def _apply_visibility_response(df: pd.DataFrame) -> pd.DataFrame:
    adjusted = df.copy()
    for col, factor in [("low_visibility_hours", 0.65), ("fog_hours", 0.60), ("rain_hours", 0.80)]:
        if col in adjusted.columns:
            adjusted[col] = adjusted[col] * factor
    return adjusted


def _apply_combined_safe_system(df: pd.DataFrame) -> pd.DataFrame:
    return _apply_visibility_response(_apply_enforcement(_apply_speed_management(df)))


SCENARIO_FUNCTIONS = {
    "Baseline": lambda df: df.copy(),
    "Speed Management": _apply_speed_management,
    "Targeted Enforcement": _apply_enforcement,
    "Visibility Response": _apply_visibility_response,
    "Combined Safe System": _apply_combined_safe_system,
}


def _normalized_series(series: pd.Series, lower: float, upper: float) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce").fillna(0.0)
    if upper <= lower:
        return pd.Series(0.0, index=series.index)
    clipped = clean.clip(lower=lower, upper=upper)
    return (clipped - lower) / (upper - lower)


def _reference_bounds(df: pd.DataFrame, feature_names: list[str]) -> dict[str, tuple[float, float]]:
    bounds: dict[str, tuple[float, float]] = {}
    for feature in feature_names:
        if feature not in df.columns:
            continue
        clean = pd.to_numeric(df[feature], errors="coerce").fillna(0.0)
        bounds[feature] = (float(clean.quantile(0.05)), float(clean.quantile(0.95)))
    return bounds


def _operational_pressure_score(
    df: pd.DataFrame,
    bounds: dict[str, tuple[float, float]],
) -> pd.Series:
    weights = {
        "p95_speed": 0.25,
        "mean_speed": 0.15,
        "total_violations": 0.10,
        "violations_per_1000_volume": 0.20,
        "low_visibility_hours": 0.12,
        "fog_hours": 0.08,
        "rain_hours": 0.05,
        "daily_volume": 0.05,
    }
    available = {feature: weight for feature, weight in weights.items() if feature in df.columns}
    if not available:
        return pd.Series(0.0, index=df.index)

    score = pd.Series(0.0, index=df.index, dtype=float)
    total_weight = sum(available.values())
    for feature, weight in available.items():
        lower, upper = bounds[feature]
        score += _normalized_series(df[feature], lower=lower, upper=upper) * weight
    return score / total_weight


def analyze_scenarios(
    model_df: pd.DataFrame,
    pipe: Pipeline,
    target_col: str = "has_fatality",
    risk_threshold: float = 0.50,
) -> ScenarioAnalysis:
    working = model_df.copy()
    feature_cols = get_model_feature_columns(working, target_col=target_col)
    pressure_bounds = _reference_bounds(
        working,
        [
            "p95_speed",
            "mean_speed",
            "total_violations",
            "violations_per_1000_volume",
            "low_visibility_hours",
            "fog_hours",
            "rain_hours",
            "daily_volume",
        ],
    )

    baseline_features = working[feature_cols]
    baseline_model_risk = pipe.predict_proba(baseline_features)[:, 1]
    baseline_pressure = _operational_pressure_score(working, bounds=pressure_bounds)
    baseline_risk = (0.65 * baseline_model_risk) + (0.35 * baseline_pressure)
    effective_threshold = max(risk_threshold, float(pd.Series(baseline_risk).quantile(0.85)))
    baseline_high_risk = baseline_risk >= effective_threshold

    scenario_rows: list[dict[str, object]] = []
    opportunities: list[pd.DataFrame] = []
    region_rows: list[pd.DataFrame] = []

    for scenario_name, scenario_fn in SCENARIO_FUNCTIONS.items():
        scenario_df = scenario_fn(working)
        scenario_features = scenario_df[feature_cols]
        scenario_model_risk = pipe.predict_proba(scenario_features)[:, 1]
        scenario_pressure = _operational_pressure_score(scenario_df, bounds=pressure_bounds)
        scenario_risk = (0.65 * scenario_model_risk) + (0.35 * scenario_pressure)
        risk_delta = baseline_risk - scenario_risk
        moved_below_threshold = baseline_high_risk & (scenario_risk < effective_threshold)

        if scenario_name != "Baseline":
            scenario_rows.append(
                {
                    "scenario": scenario_name,
                    "avg_risk_reduction": float(risk_delta.mean()),
                    "median_risk_reduction": float(pd.Series(risk_delta).median()),
                    "max_risk_reduction": float(pd.Series(risk_delta).max()),
                    "avg_baseline_risk": float(pd.Series(baseline_risk).mean()),
                    "avg_scenario_risk": float(pd.Series(scenario_risk).mean()),
                    "baseline_high_risk_road_days": int(baseline_high_risk.sum()),
                    "high_risk_road_days_reduced": int(moved_below_threshold.sum()),
                    "high_risk_reduction_rate": float(moved_below_threshold.sum() / max(1, baseline_high_risk.sum())),
                }
            )

        scenario_output = working[["road_id", "date", "region", "city", "road_type"]].copy()
        scenario_output["scenario"] = scenario_name
        scenario_output["baseline_risk"] = baseline_risk
        scenario_output["scenario_risk"] = scenario_risk
        scenario_output["risk_delta"] = risk_delta
        scenario_output["moved_below_threshold"] = moved_below_threshold.astype(int)

        if scenario_name != "Baseline":
            opportunities.append(
                scenario_output.sort_values(["risk_delta", "baseline_risk"], ascending=False).head(20)
            )
            region_impact = (
                scenario_output.groupby("region", as_index=False)
                .agg(
                    avg_risk_reduction=("risk_delta", "mean"),
                    median_risk_reduction=("risk_delta", "median"),
                    high_risk_road_days_reduced=("moved_below_threshold", "sum"),
                    baseline_mean_risk=("baseline_risk", "mean"),
                    scenario_mean_risk=("scenario_risk", "mean"),
                )
                .sort_values(["avg_risk_reduction", "high_risk_road_days_reduced"], ascending=False)
            )
            region_impact["scenario"] = scenario_name
            region_rows.append(region_impact)

    summary = pd.DataFrame(scenario_rows).sort_values(
        ["avg_risk_reduction", "high_risk_road_days_reduced"],
        ascending=False,
    )
    top_opportunities = pd.concat(opportunities, ignore_index=True) if opportunities else pd.DataFrame()
    region_impact = pd.concat(region_rows, ignore_index=True) if region_rows else pd.DataFrame()

    return ScenarioAnalysis(
        summary=summary,
        top_opportunities=top_opportunities,
        region_impact=region_impact,
    )


def scenario_to_markdown(analysis: ScenarioAnalysis) -> str:
    lines: list[str] = []
    lines.append("# Scenario Analysis Report")
    lines.append("")
    lines.append("This report estimates the relative impact of intervention packages on a blended road-day risk score.")
    lines.append("")
    lines.append("## Scenario Summary")
    lines.append("| Scenario | Avg Risk Reduction | Median Risk Reduction | Max Risk Reduction | Baseline Avg Risk | Scenario Avg Risk | High-Risk Road-Days Reduced | Reduction Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, row in analysis.summary.iterrows():
        lines.append(
            f"| {row['scenario']} | {row['avg_risk_reduction']:.4f} | {row['median_risk_reduction']:.4f} | "
            f"{row['max_risk_reduction']:.4f} | {row['avg_baseline_risk']:.4f} | {row['avg_scenario_risk']:.4f} | "
            f"{int(row['high_risk_road_days_reduced'])} | {row['high_risk_reduction_rate']:.2%} |"
        )
    lines.append("")
    lines.append("## Highest-Leverage Road-Days")
    if analysis.top_opportunities.empty:
        lines.append("- No scenario opportunities were generated.")
    else:
        lines.append("| Scenario | Road | Date | Region | City | Type | Baseline Risk | Scenario Risk | Risk Delta |")
        lines.append("|---|---|---|---|---|---|---:|---:|---:|")
        for _, row in analysis.top_opportunities.head(12).iterrows():
            day = pd.to_datetime(row["date"]).date().isoformat() if pd.notna(row["date"]) else ""
            lines.append(
                f"| {row['scenario']} | {row['road_id']} | {day} | {row['region']} | {row['city']} | {row['road_type']} | "
                f"{row['baseline_risk']:.3f} | {row['scenario_risk']:.3f} | {row['risk_delta']:.3f} |"
            )
    lines.append("")
    lines.append("## Regional Impact")
    if analysis.region_impact.empty:
        lines.append("- No regional impact table was generated.")
    else:
        lines.append("| Scenario | Region | Avg Risk Reduction | High-Risk Road-Days Reduced | Baseline Mean Risk | Scenario Mean Risk |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for _, row in analysis.region_impact.head(15).iterrows():
            lines.append(
                f"| {row['scenario']} | {row['region']} | {row['avg_risk_reduction']:.4f} | "
                f"{int(row['high_risk_road_days_reduced'])} | {row['baseline_mean_risk']:.3f} | {row['scenario_mean_risk']:.3f} |"
            )
    lines.append("")
    lines.append("## Interpretation Notes")
    lines.append("- These scenarios are directional planning tools, not causal proof.")
    lines.append("- The scenario score blends baseline model risk with controllable operational pressure signals.")
    lines.append("- Combined interventions are expected to be strongest when they address speed, behavior, and context together.")
    lines.append("- The output is most useful for prioritization workshops and operational planning discussions.")
    return "\n".join(lines)
