from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

COLUMN_DESCRIPTIONS: dict[str, str] = {
    "road_id": "Unique road segment identifier",
    "incident_id": "Unique accident incident identifier",
    "violation_id": "Unique violation identifier",
    "sensor_id": "Speed sensor identifier",
    "date_time": "Event timestamp in UTC",
    "date": "Calendar date used for road-day grain",
    "region": "Administrative region",
    "city": "City or locality",
    "road_type": "Road classification",
    "speed_limit": "Posted speed limit",
    "lanes": "Lane count",
    "weather": "Incident-level weather context",
    "weather_mode": "Dominant daily weather context",
    "visibility_km": "Visibility in kilometers",
    "precip_mm": "Precipitation in millimeters",
    "temp_c": "Temperature in Celsius",
    "volume": "Observed traffic volume at sensor event level",
    "daily_volume": "Aggregated daily traffic volume by road",
    "avg_speed": "Average observed speed at sensor event level",
    "mean_speed": "Average observed speed by road-day",
    "p95_speed": "95th percentile speed by road-day",
    "violations_per_1000_volume": "Exposure-normalized violation intensity",
    "total_violations": "Total violations aggregated to road-day",
    "accidents": "Accident count aggregated to road-day",
    "injuries": "Injury count",
    "fatalities": "Fatality count",
    "severity": "Incident severity classification",
    "severe": "Severe + fatal incident count on road-day",
    "severe_rate": "Severe incidents divided by accidents",
    "has_fatality": "Binary target flag for any fatality on road-day",
    "source_system": "Logical source system name",
    "ingest_batch_id": "Batch lineage identifier",
    "extracted_at_utc": "Ingest extraction timestamp",
    "record_hash": "Stable row-level traceability hash",
}


def build_data_dictionary(datasets: dict[str, pd.DataFrame]) -> str:
    lines: list[str] = []
    lines.append("# Data Dictionary")
    lines.append("")
    lines.append("This artifact is generated automatically from the processed datasets.")
    lines.append("")

    for dataset_name, df in datasets.items():
        lines.append(f"## {dataset_name}")
        lines.append("")
        lines.append(f"- Rows: {len(df):,}")
        lines.append(f"- Columns: {len(df.columns)}")
        lines.append("")
        lines.append("| Column | Dtype | Null Rate | Description |")
        lines.append("|---|---|---:|---|")
        for column in df.columns:
            description = COLUMN_DESCRIPTIONS.get(
                column, "Business/technical field documented for demo use"
            )
            null_rate = float(df[column].isna().mean())
            lines.append(f"| {column} | {df[column].dtype} | {null_rate:.4f} | {description} |")
        lines.append("")

    return "\n".join(lines)


def build_lineage_summary(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset_name, df in datasets.items():
        source_systems = (
            sorted(df["source_system"].dropna().astype(str).unique().tolist())
            if "source_system" in df.columns
            else []
        )
        batch_ids = (
            sorted(df["ingest_batch_id"].dropna().astype(str).unique().tolist())
            if "ingest_batch_id" in df.columns
            else []
        )
        record_hash_coverage = (
            float(df["record_hash"].notna().mean()) if "record_hash" in df.columns else 0.0
        )
        rows.append(
            {
                "dataset": dataset_name,
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "source_systems": ", ".join(source_systems),
                "batch_ids": ", ".join(batch_ids),
                "record_hash_coverage": record_hash_coverage,
            }
        )
    return pd.DataFrame(rows)


def build_pipeline_manifest(
    datasets: dict[str, pd.DataFrame],
    quality_summary: dict[str, Any],
    model_summary: dict[str, Any],
    output_dir: Path,
    additional_output_files: list[str] | None = None,
) -> dict[str, Any]:
    current_files = {path.name for path in output_dir.iterdir()}
    if additional_output_files:
        current_files.update(additional_output_files)
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_rows": {name: int(len(df)) for name, df in datasets.items()},
        "quality_gate_status": quality_summary["gate_status"],
        "quality_rule_counts": {
            "pass": int(quality_summary["pass"]),
            "warn": int(quality_summary["warn"]),
            "fail": int(quality_summary["fail"]),
            "total": int(quality_summary["total"]),
        },
        "model_summary": model_summary,
        "output_files": sorted(current_files),
    }


def build_solution_overview(
    quality_summary: dict[str, Any],
    model_summary: dict[str, Any],
    manifest: dict[str, Any],
    scenario_summary: pd.DataFrame | None = None,
    run_summary: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Solution Overview")
    lines.append("")
    lines.append("## Solution strengths")
    lines.append("- It demonstrates multi-source integration with record-level traceability.")
    lines.append("- It uses explicit quality gates before reporting or predictive outputs.")
    lines.append("- It delivers both executive reporting and Power BI-ready outputs.")
    lines.append("- It includes intervention scenario analysis to support action planning.")
    lines.append("- It documents assumptions, limitations, and governance considerations.")
    lines.append("")
    lines.append("## Current solution status")
    lines.append(f"- Quality gate: **{quality_summary['gate_status']}**")
    lines.append(
        f"- Quality checks: {quality_summary['pass']} PASS / {quality_summary['warn']} WARN / {quality_summary['fail']} FAIL"
    )
    lines.append(f"- Model validation split: {model_summary['split_strategy']}")
    auc_text = f"{model_summary['auc']:.3f}" if model_summary["auc"] is not None else "n/a"
    lines.append(f"- Holdout AUC: {auc_text}")
    lines.append(f"- Holdout F1: {model_summary['f1']:.3f}")
    if "decision_threshold" in model_summary:
        lines.append(f"- Decision threshold: {model_summary['decision_threshold']:.2f}")
    if scenario_summary is not None and not scenario_summary.empty:
        best = scenario_summary.sort_values(
            ["avg_risk_reduction", "high_risk_road_days_reduced"],
            ascending=False,
        ).iloc[0]
        lines.append(
            f"- Best scenario package: {best['scenario']} "
            f"(avg risk reduction {best['avg_risk_reduction']:.4f}, "
            f"high-risk road-days reduced {int(best['high_risk_road_days_reduced'])})"
        )
    if run_summary is not None:
        lines.append(
            f"- Latest run status: {run_summary.get('status', 'unknown')} "
            f"with {len(run_summary.get('steps', []))} tracked steps"
        )
    lines.append(f"- Generated datasets: {', '.join(sorted(manifest['dataset_rows'].keys()))}")
    lines.append("")
    lines.append("## Scope notes")
    lines.append("- The workflow is governed and repeatable, not notebook-driven.")
    lines.append(
        "- The predictive model is framed as prioritization support, not automated decision-making."
    )
    lines.append(
        "- Power BI delivery is considered from the data-model stage, not afterthought reporting."
    )
    lines.append("")
    lines.append("## Limitations")
    lines.append("- Synthetic data is used for safe demo purposes.")
    lines.append(
        "- Orchestration, authentication, and production monitoring are intentionally out of scope for the demo."
    )
    lines.append(
        "- Model accuracy is secondary to methodological rigor and explainability in this project."
    )
    return "\n".join(lines)


def write_project_artifacts(
    datasets: dict[str, pd.DataFrame],
    quality_summary: dict[str, Any],
    model_summary: dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    scenario_summary = None
    scenario_path = output_dir / "scenario_summary.csv"
    if scenario_path.exists():
        scenario_summary = pd.read_csv(scenario_path)
    run_summary = None
    run_summary_path = output_dir / "run_summary.json"
    if run_summary_path.exists():
        run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))

    data_dictionary = build_data_dictionary(datasets)
    (output_dir / "data_dictionary.md").write_text(data_dictionary, encoding="utf-8")

    lineage_summary = build_lineage_summary(datasets)
    lineage_summary.to_csv(output_dir / "lineage_summary.csv", index=False)

    manifest = build_pipeline_manifest(
        datasets,
        quality_summary,
        model_summary,
        output_dir,
        additional_output_files=[
            "pipeline_manifest.json",
            "solution_overview.md",
            "run_summary.json",
        ],
    )
    solution_overview = build_solution_overview(
        quality_summary,
        model_summary,
        manifest,
        scenario_summary=scenario_summary,
        run_summary=run_summary,
    )
    (output_dir / "solution_overview.md").write_text(solution_overview, encoding="utf-8")
    (output_dir / "pipeline_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
