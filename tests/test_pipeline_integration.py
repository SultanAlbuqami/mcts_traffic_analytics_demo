from __future__ import annotations

from pathlib import Path

from traffic_analytics_demo.artifacts import write_project_artifacts
from traffic_analytics_demo.data_gen import GenConfig, generate_all
from traffic_analytics_demo.diagnostics import build_diagnostic_report
from traffic_analytics_demo.ingest import load_sources
from traffic_analytics_demo.model import train_and_evaluate
from traffic_analytics_demo.powerbi_export import export_star_schema
from traffic_analytics_demo.quality import run_quality_checks
from traffic_analytics_demo.report import build_executive_report
from traffic_analytics_demo.scenario import analyze_scenarios, scenario_to_markdown
from traffic_analytics_demo.transform import clean_and_integrate


def test_end_to_end_pipeline(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    powerbi_dir = tmp_path / "powerbi"
    out_dir = tmp_path / "out"
    raw_dir.mkdir(parents=True, exist_ok=True)

    generate_all(
        raw_dir,
        GenConfig(
            days=30, seed=7, road_segments=20, accidents=300, violations=1200, sensors_rows=4000
        ),
    )
    sources = load_sources(raw_dir, ingest_batch_id="BTEST")
    processed = clean_and_integrate(sources)

    assert {"source_system", "ingest_batch_id", "record_hash"}.issubset(
        processed["accidents"].columns
    )
    assert {"region", "city", "road_type", "weather"}.issubset(processed["accidents"].columns)
    assert {
        "daily_volume",
        "p95_speed",
        "total_violations",
        "weather_mode",
        "has_fatality",
    }.issubset(processed["model_df"].columns)

    results, summary = run_quality_checks(
        {
            "roads": processed["roads"],
            "accidents": processed["accidents"],
            "model_df": processed["model_df"],
        }
    )
    assert summary["fail"] == 0, results

    pipe, report = train_and_evaluate(processed["model_df"])
    assert report.test_rows > 0
    assert not report.top_features.empty
    assert not report.holdout_predictions.empty

    scenario_analysis = analyze_scenarios(processed["model_df"], pipe)
    assert not scenario_analysis.summary.empty
    assert not scenario_analysis.top_opportunities.empty
    assert not scenario_analysis.region_impact.empty
    scenario_markdown = scenario_to_markdown(scenario_analysis)
    assert "Scenario Analysis Report" in scenario_markdown

    executive_report = build_executive_report(processed["accidents"], processed["model_df"])
    assert "Executive Summary" in executive_report
    assert "Top Hotspots" in executive_report

    diagnostic_report = build_diagnostic_report(processed["accidents"], processed["model_df"])
    assert "Diagnostic Report" in diagnostic_report
    assert "Root-Cause Style Hypotheses" in diagnostic_report

    export_star_schema(processed, powerbi_dir)
    expected_files = {
        "dim_date.csv",
        "dim_road.csv",
        "fact_accident.csv",
        "fact_sensor.csv",
        "fact_violation.csv",
        "fact_road_day.csv",
        "measures.dax",
        "model_notes.md",
    }
    assert expected_files.issubset({path.name for path in powerbi_dir.iterdir()})

    write_project_artifacts(
        processed,
        summary,
        {
            "split_strategy": report.split_strategy,
            "train_rows": report.train_rows,
            "test_rows": report.test_rows,
            "auc": report.auc,
            "f1": report.f1,
            "precision": report.precision,
            "recall": report.recall,
        },
        out_dir,
    )
    artifact_files = {
        "data_dictionary.md",
        "lineage_summary.csv",
        "pipeline_manifest.json",
        "solution_overview.md",
    }
    assert artifact_files.issubset({path.name for path in out_dir.iterdir()})
