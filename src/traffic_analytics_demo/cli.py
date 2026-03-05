from __future__ import annotations

import argparse
import pickle
import shutil
from datetime import UTC, datetime

import pandas as pd

from .artifacts import write_project_artifacts
from .config import get_paths, get_settings
from .data_gen import GenConfig, generate_all
from .diagnostics import build_diagnostic_report
from .ingest import load_sources
from .model import report_to_markdown, train_and_evaluate
from .ops import PipelineRunTracker, configure_logging
from .powerbi_export import export_star_schema
from .quality import run_quality_checks, to_markdown
from .report import build_executive_report
from .scenario import analyze_scenarios, scenario_to_markdown
from .stakeholder_pack import build_stakeholder_pack
from .transform import clean_and_integrate, save_processed


def _runtime() -> tuple:
    paths = get_paths()
    settings = get_settings()
    logger = configure_logging(paths.out, settings.log_level)
    return paths, settings, logger


def _batch_id() -> str:
    return datetime.now(UTC).strftime("B%Y%m%dT%H%M%SZ")


def _save_layer(output_dir, datasets: dict[str, pd.DataFrame]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in datasets.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)


def _curated_csv(paths, filename: str):
    curated_path = paths.data_curated / filename
    if curated_path.exists():
        return curated_path
    return paths.data_processed / filename


def cmd_generate_data(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    cfg = GenConfig(
        days=args.days,
        seed=args.seed,
        road_segments=args.road_segments,
        accidents=args.accidents,
        violations=args.violations,
        sensors_rows=args.sensors_rows,
    )
    generate_all(paths.data_raw, cfg)
    logger.info(
        "Synthetic sources generated | raw_dir=%s | days=%s | seed=%s | roads=%s | accidents=%s | violations=%s | sensors=%s",
        paths.data_raw,
        args.days,
        args.seed,
        args.road_segments,
        args.accidents,
        args.violations,
        args.sensors_rows,
    )
    print(f"Generated synthetic sources in: {paths.data_raw}")


def cmd_run_pipeline(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    batch = args.batch_id or _batch_id()
    sources = load_sources(paths.data_raw, ingest_batch_id=batch)
    _save_layer(paths.data_staged, sources)
    processed = clean_and_integrate(sources)
    save_processed(paths.data_curated, processed)
    save_processed(paths.data_processed, processed)
    logger.info(
        "Pipeline layers saved | staged_dir=%s | curated_dir=%s | processed_dir=%s | batch_id=%s",
        paths.data_staged,
        paths.data_curated,
        paths.data_processed,
        batch,
    )
    print(f"Processed datasets saved in: {paths.data_processed}")


def cmd_quality(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    dfs = {
        "roads": pd.read_csv(_curated_csv(paths, "roads.csv")),
        "accidents": pd.read_csv(_curated_csv(paths, "accidents.csv")),
        "model_df": pd.read_csv(_curated_csv(paths, "model_df.csv")),
    }
    results, summary = run_quality_checks(dfs)
    markdown = to_markdown(results, summary)
    out = paths.out / "quality_report.md"
    out.write_text(markdown, encoding="utf-8")
    logger.info("Quality report written | path=%s | gate=%s", out, summary["gate_status"])
    print(f"Wrote: {out}")


def cmd_model(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    model_df = pd.read_csv(_curated_csv(paths, "model_df.csv"))
    pipe, report = train_and_evaluate(model_df, target_col="has_fatality")

    markdown = report_to_markdown(report)
    report_path = paths.out / "model_report.md"
    report_path.write_text(markdown, encoding="utf-8")

    holdout_path = paths.out / "model_holdout_predictions.csv"
    report.holdout_predictions.to_csv(holdout_path, index=False)

    pipeline_path = paths.out / "model_pipeline.pkl"
    with pipeline_path.open("wb") as fh:
        pickle.dump(pipe, fh)

    logger.info(
        "Model artifacts written | split=%s | auc=%s | f1=%.3f",
        report.split_strategy,
        f"{report.auc:.3f}" if report.auc is not None else "n/a",
        report.f1,
    )
    print(f"Wrote: {report_path}")
    print(f"Wrote: {holdout_path}")
    print(f"Wrote: {pipeline_path}")


def cmd_report(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    accidents = pd.read_csv(_curated_csv(paths, "accidents.csv"), parse_dates=["date_time"])
    model_df = pd.read_csv(_curated_csv(paths, "model_df.csv"))
    markdown = build_executive_report(accidents, model_df)
    out = paths.out / "executive_report.md"
    out.write_text(markdown, encoding="utf-8")

    quality_path = paths.out / "quality_report.md"
    quality_gate = "unknown"
    if quality_path.exists():
        quality_text = quality_path.read_text(encoding="utf-8")
        gate_line = next((line for line in quality_text.splitlines() if "Overall gate" in line), "")
        if "**" in gate_line:
            quality_gate = gate_line.split("**")[1]
    scenario_summary_path = paths.out / "scenario_summary.csv"
    scenario_summary = pd.read_csv(scenario_summary_path) if scenario_summary_path.exists() else None

    stakeholder_pack = build_stakeholder_pack(
        accidents=accidents,
        model_df=model_df,
        quality_gate=quality_gate,
        scenario_summary=scenario_summary,
    )
    stakeholder_out = paths.out / "stakeholder_pack.md"
    stakeholder_out.write_text(stakeholder_pack, encoding="utf-8")

    logger.info("Executive report written | path=%s", out)
    print(f"Wrote: {out}")
    print(f"Wrote: {stakeholder_out}")


def cmd_diagnostics(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    accidents = pd.read_csv(_curated_csv(paths, "accidents.csv"), parse_dates=["date_time"])
    model_df = pd.read_csv(_curated_csv(paths, "model_df.csv"))
    markdown = build_diagnostic_report(accidents, model_df)
    out = paths.out / "diagnostic_report.md"
    out.write_text(markdown, encoding="utf-8")
    logger.info("Diagnostic report written | path=%s", out)
    print(f"Wrote: {out}")


def cmd_scenarios(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    model_df = pd.read_csv(_curated_csv(paths, "model_df.csv"))
    pipeline_path = paths.out / "model_pipeline.pkl"

    if pipeline_path.exists():
        with pipeline_path.open("rb") as fh:
            pipe = pickle.load(fh)
    else:
        pipe, _ = train_and_evaluate(model_df, target_col="has_fatality")
        with pipeline_path.open("wb") as fh:
            pickle.dump(pipe, fh)

    analysis = analyze_scenarios(model_df, pipe, target_col="has_fatality")
    report_path = paths.out / "scenario_report.md"
    report_path.write_text(scenario_to_markdown(analysis), encoding="utf-8")
    analysis.summary.to_csv(paths.out / "scenario_summary.csv", index=False)
    analysis.top_opportunities.to_csv(paths.out / "scenario_top_opportunities.csv", index=False)
    analysis.region_impact.to_csv(paths.out / "scenario_region_impact.csv", index=False)

    accidents = pd.read_csv(_curated_csv(paths, "accidents.csv"), parse_dates=["date_time"])
    quality_path = paths.out / "quality_report.md"
    quality_gate = "unknown"
    if quality_path.exists():
        quality_text = quality_path.read_text(encoding="utf-8")
        gate_line = next((line for line in quality_text.splitlines() if "Overall gate" in line), "")
        if "**" in gate_line:
            quality_gate = gate_line.split("**")[1]
    stakeholder_pack = build_stakeholder_pack(
        accidents=accidents,
        model_df=model_df,
        quality_gate=quality_gate,
        scenario_summary=analysis.summary,
    )
    stakeholder_out = paths.out / "stakeholder_pack.md"
    stakeholder_out.write_text(stakeholder_pack, encoding="utf-8")

    logger.info(
        "Scenario outputs written | best_scenario=%s",
        analysis.summary.iloc[0]["scenario"] if not analysis.summary.empty else "n/a",
    )
    print(f"Wrote: {report_path}")
    print(f"Wrote: {paths.out / 'scenario_summary.csv'}")
    print(f"Wrote: {paths.out / 'scenario_top_opportunities.csv'}")
    print(f"Wrote: {paths.out / 'scenario_region_impact.csv'}")
    print(f"Wrote: {stakeholder_out}")


def cmd_export_powerbi(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    processed = {
        "roads": pd.read_csv(_curated_csv(paths, "roads.csv")),
        "accidents": pd.read_csv(_curated_csv(paths, "accidents.csv"), parse_dates=["date_time"]),
        "violations": pd.read_csv(_curated_csv(paths, "violations.csv"), parse_dates=["date_time"]),
        "sensors": pd.read_csv(_curated_csv(paths, "sensors.csv"), parse_dates=["date_time"]),
        "model_df": pd.read_csv(_curated_csv(paths, "model_df.csv")),
    }
    export_star_schema(processed, paths.out_powerbi)
    for scenario_file in ["scenario_summary.csv", "scenario_region_impact.csv"]:
        src = paths.out / scenario_file
        if src.exists():
            shutil.copy2(src, paths.out_powerbi / scenario_file)
    logger.info("Power BI export written | path=%s", paths.out_powerbi)
    print(f"Power BI export tables in: {paths.out_powerbi}")


def cmd_artifacts(args: argparse.Namespace) -> None:
    paths, _, logger = _runtime()
    datasets = {
        "roads": pd.read_csv(_curated_csv(paths, "roads.csv")),
        "accidents": pd.read_csv(_curated_csv(paths, "accidents.csv")),
        "violations": pd.read_csv(_curated_csv(paths, "violations.csv")),
        "sensors": pd.read_csv(_curated_csv(paths, "sensors.csv")),
        "model_df": pd.read_csv(_curated_csv(paths, "model_df.csv")),
    }
    _, quality_summary = run_quality_checks(
        {
            "roads": datasets["roads"],
            "accidents": datasets["accidents"],
            "model_df": datasets["model_df"],
        }
    )
    _, model_report = train_and_evaluate(datasets["model_df"], target_col="has_fatality")
    model_summary = {
        "split_strategy": model_report.split_strategy,
        "train_rows": model_report.train_rows,
        "test_rows": model_report.test_rows,
        "decision_threshold": model_report.decision_threshold,
        "auc": model_report.auc,
        "f1": model_report.f1,
        "precision": model_report.precision,
        "recall": model_report.recall,
    }
    write_project_artifacts(datasets, quality_summary, model_summary, paths.out)
    logger.info("Metadata artifacts written | path=%s", paths.out)
    print(f"Wrote metadata artifacts in: {paths.out}")


def cmd_all(args: argparse.Namespace) -> None:
    paths, settings, logger = _runtime()
    tracker = PipelineRunTracker(paths.out, settings.pipeline_name, logger=logger)
    tracker.set_metadata(
        days=args.days,
        seed=args.seed,
        road_segments=args.road_segments,
        accidents=args.accidents,
        violations=args.violations,
        sensors_rows=args.sensors_rows,
        batch_id=args.batch_id or "auto",
    )

    try:
        with tracker.step("generate-data"):
            cmd_generate_data(
                argparse.Namespace(
                    days=args.days,
                    seed=args.seed,
                    road_segments=args.road_segments,
                    accidents=args.accidents,
                    violations=args.violations,
                    sensors_rows=args.sensors_rows,
                )
            )
        with tracker.step("run-pipeline"):
            cmd_run_pipeline(argparse.Namespace(batch_id=args.batch_id))
        with tracker.step("quality"):
            cmd_quality(args)
        with tracker.step("model"):
            cmd_model(args)
        with tracker.step("report"):
            cmd_report(args)
        with tracker.step("diagnostics"):
            cmd_diagnostics(args)
        with tracker.step("scenarios"):
            cmd_scenarios(args)
        with tracker.step("export-powerbi"):
            cmd_export_powerbi(args)
        with tracker.step("artifacts"):
            cmd_artifacts(args)
    except Exception as exc:
        summary_path = tracker.write_summary(status="FAILED", error=str(exc))
        logger.error("Pipeline failed | summary=%s | error=%s", summary_path, exc)
        raise

    summary_path = tracker.write_summary(status="SUCCESS")
    logger.info("Pipeline completed successfully | summary=%s", summary_path)


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    default_gen = GenConfig()
    parser = argparse.ArgumentParser(
        prog="traffic_analytics_demo",
        description="Governed traffic safety analytics demo",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    generate_parser = sub.add_parser("generate-data", help="Generate synthetic raw sources")
    generate_parser.add_argument("--days", type=int, default=settings.default_days)
    generate_parser.add_argument("--seed", type=int, default=settings.default_seed)
    generate_parser.add_argument("--road-segments", type=int, default=default_gen.road_segments)
    generate_parser.add_argument("--accidents", type=int, default=default_gen.accidents)
    generate_parser.add_argument("--violations", type=int, default=default_gen.violations)
    generate_parser.add_argument("--sensors-rows", type=int, default=default_gen.sensors_rows)
    generate_parser.set_defaults(func=cmd_generate_data)

    pipeline_parser = sub.add_parser("run-pipeline", help="Ingest + clean + integrate to staged/curated datasets")
    pipeline_parser.add_argument("--batch-id", type=str, default=None)
    pipeline_parser.set_defaults(func=cmd_run_pipeline)

    quality_parser = sub.add_parser("quality", help="Run data quality checks and write markdown report")
    quality_parser.set_defaults(func=cmd_quality)

    model_parser = sub.add_parser("model", help="Train a predictive model and write model outputs")
    model_parser.set_defaults(func=cmd_model)

    report_parser = sub.add_parser("report", help="Build executive KPI report")
    report_parser.set_defaults(func=cmd_report)

    diagnostic_parser = sub.add_parser("diagnostics", help="Build diagnostic / root-cause style report")
    diagnostic_parser.set_defaults(func=cmd_diagnostics)

    scenario_parser = sub.add_parser("scenarios", help="Build prescriptive scenario-analysis outputs")
    scenario_parser.set_defaults(func=cmd_scenarios)

    powerbi_parser = sub.add_parser("export-powerbi", help="Export star schema CSVs for Power BI")
    powerbi_parser.set_defaults(func=cmd_export_powerbi)

    artifacts_parser = sub.add_parser("artifacts", help="Write metadata and governance artifacts")
    artifacts_parser.set_defaults(func=cmd_artifacts)

    all_parser = sub.add_parser("all", help="Run end-to-end demo pipeline")
    all_parser.add_argument("--days", type=int, default=settings.default_days)
    all_parser.add_argument("--seed", type=int, default=settings.default_seed)
    all_parser.add_argument("--road-segments", type=int, default=default_gen.road_segments)
    all_parser.add_argument("--accidents", type=int, default=default_gen.accidents)
    all_parser.add_argument("--violations", type=int, default=default_gen.violations)
    all_parser.add_argument("--sensors-rows", type=int, default=default_gen.sensors_rows)
    all_parser.add_argument("--batch-id", type=str, default=None)
    all_parser.set_defaults(func=cmd_all)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
