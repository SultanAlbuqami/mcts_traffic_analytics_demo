from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import pandas as pd


@dataclass(frozen=True)
class QualityRuleResult:
    name: str
    status: str
    metric: float | None
    threshold: float | None
    notes: str


@dataclass(frozen=True)
class DatasetContract:
    required_columns: tuple[str, ...]
    key_columns: tuple[str, ...] = ()
    allowed_values: dict[str, set[str]] | None = None
    nonnegative_columns: tuple[str, ...] = ()


CONTRACTS: dict[str, DatasetContract] = {
    "roads": DatasetContract(
        required_columns=("road_id", "region", "city", "road_type", "speed_limit", "lanes"),
        key_columns=("road_id",),
        allowed_values={"road_type": {"Highway", "Urban", "Rural"}},
        nonnegative_columns=("speed_limit", "lanes"),
    ),
    "accidents": DatasetContract(
        required_columns=("incident_id", "date_time", "road_id", "region", "city", "road_type", "severity", "fatalities", "injuries"),
        key_columns=("incident_id",),
        allowed_values={"severity": {"Minor", "Moderate", "Severe", "Fatal"}},
        nonnegative_columns=("fatalities", "injuries", "vehicles_involved"),
    ),
    "model_df": DatasetContract(
        required_columns=(
            "road_id",
            "date",
            "daily_volume",
            "mean_speed",
            "p95_speed",
            "total_violations",
            "accidents",
            "fatalities",
            "region",
            "city",
            "road_type",
            "has_fatality",
            "violations_per_1000_volume",
        ),
        key_columns=("road_id", "date"),
        allowed_values={"road_type": {"Highway", "Urban", "Rural"}},
        nonnegative_columns=(
            "daily_volume",
            "mean_speed",
            "p95_speed",
            "total_violations",
            "accidents",
            "fatalities",
            "violations_per_1000_volume",
        ),
    ),
}


def _null_rate(df: pd.DataFrame, col: str) -> float:
    return float(df[col].isna().mean())


def _duplicate_rate(df: pd.DataFrame, subset: list[str]) -> float:
    return float(df.duplicated(subset=subset).mean())


def _invalid_allowed_rate(series: pd.Series, allowed: set[str]) -> float:
    return float((~series.astype(str).isin(sorted(allowed))).mean())


def _datetime_parse_fail_rate(series: pd.Series) -> float:
    parsed = pd.to_datetime(series, utc=True, errors="coerce")
    return float(parsed.isna().mean())


def _add_result(
    results: list[QualityRuleResult],
    name: str,
    metric: float | None,
    threshold: float | None,
    notes: str,
    pass_limit: float | None = None,
    warn_limit: float | None = None,
    failed: bool = False,
) -> None:
    if failed:
        status = "FAIL"
    elif metric is None or pass_limit is None:
        status = "PASS"
    elif metric <= pass_limit:
        status = "PASS"
    elif warn_limit is not None and metric <= warn_limit:
        status = "WARN"
    else:
        status = "FAIL"

    results.append(
        QualityRuleResult(
            name=name,
            status=status,
            metric=metric,
            threshold=threshold,
            notes=notes,
        )
    )


def _run_contract_checks(results: list[QualityRuleResult], dfs: Dict[str, pd.DataFrame]) -> None:
    for dataset_name, contract in CONTRACTS.items():
        df = dfs[dataset_name]

        missing_columns = [column for column in contract.required_columns if column not in df.columns]
        _add_result(
            results,
            name=f"{dataset_name}.contract_required_columns",
            metric=None,
            threshold=None,
            notes="OK" if not missing_columns else f"Missing columns: {missing_columns}",
            failed=bool(missing_columns),
        )

        if contract.key_columns and not missing_columns:
            dup_rate = _duplicate_rate(df, list(contract.key_columns))
            _add_result(
                results,
                name=f"{dataset_name}.contract_duplicate_key_rate",
                metric=dup_rate,
                threshold=0.0,
                notes=f"Primary grain should be unique on {', '.join(contract.key_columns)}",
                pass_limit=0.0,
                warn_limit=0.002,
            )

        if contract.allowed_values:
            for column, allowed in contract.allowed_values.items():
                if column not in df.columns:
                    continue
                invalid_rate = _invalid_allowed_rate(df[column], allowed)
                _add_result(
                    results,
                    name=f"{dataset_name}.contract_invalid_{column}_rate",
                    metric=invalid_rate,
                    threshold=0.0,
                    notes=f"Allowed values: {sorted(allowed)}",
                    pass_limit=0.0,
                    warn_limit=0.002,
                )

        for column in contract.nonnegative_columns:
            if column not in df.columns:
                continue
            negative_rate = float((pd.to_numeric(df[column], errors="coerce").fillna(0) < 0).mean())
            _add_result(
                results,
                name=f"{dataset_name}.contract_negative_{column}_rate",
                metric=negative_rate,
                threshold=0.0,
                notes=f"{column} should be non-negative",
                pass_limit=0.0,
                warn_limit=0.0,
            )


def run_quality_checks(dfs: Dict[str, pd.DataFrame]) -> Tuple[List[QualityRuleResult], Dict[str, Any]]:
    results: List[QualityRuleResult] = []

    accidents = dfs["accidents"]
    roads = dfs["roads"]
    model_df = dfs["model_df"]

    _run_contract_checks(results, dfs)

    required_acc_cols = [
        "incident_id",
        "date_time",
        "road_id",
        "region",
        "city",
        "road_type",
        "severity",
    ]
    missing = [c for c in required_acc_cols if c not in accidents.columns]
    _add_result(
        results,
        name="accidents.required_columns",
        metric=None,
        threshold=None,
        notes="OK" if not missing else f"Missing columns: {missing}",
        failed=bool(missing),
    )

    traceability_cols = ["source_system", "ingest_batch_id", "record_hash"]
    missing_traceability = [c for c in traceability_cols if c not in accidents.columns]
    _add_result(
        results,
        name="accidents.traceability_columns",
        metric=None,
        threshold=None,
        notes="OK" if not missing_traceability else f"Missing traceability columns: {missing_traceability}",
        failed=bool(missing_traceability),
    )

    road_dup_rate = _duplicate_rate(roads, ["road_id"])
    _add_result(
        results,
        name="roads.duplicate_road_id_rate",
        metric=road_dup_rate,
        threshold=0.0,
        notes="Road registry should have unique road_id values",
        pass_limit=0.0,
        warn_limit=0.002,
    )

    dup_rate = _duplicate_rate(accidents, ["incident_id"])
    _add_result(
        results,
        name="accidents.duplicate_incident_id_rate",
        metric=dup_rate,
        threshold=0.001,
        notes="Duplicate incident_id rate",
        pass_limit=0.001,
        warn_limit=0.01,
    )

    accident_parse_fail = _datetime_parse_fail_rate(accidents["date_time"])
    _add_result(
        results,
        name="accidents.date_time_parse_fail_rate",
        metric=accident_parse_fail,
        threshold=0.0,
        notes="Accident timestamps must parse cleanly to UTC",
        pass_limit=0.0,
        warn_limit=0.0,
    )

    road_null_rate = _null_rate(accidents, "road_id")
    _add_result(
        results,
        name="accidents.null_road_id_rate",
        metric=road_null_rate,
        threshold=0.0005,
        notes="Null rate in road_id",
        pass_limit=0.0005,
        warn_limit=0.01,
    )

    known_roads = set(roads["road_id"].astype(str))
    bad_fk = float((~accidents["road_id"].astype(str).isin(known_roads)).mean())
    _add_result(
        results,
        name="accidents.road_fk_invalid_rate",
        metric=bad_fk,
        threshold=0.0005,
        notes="Accidents whose road_id is missing from the road registry",
        pass_limit=0.0005,
        warn_limit=0.01,
    )

    valid_severity = {"Minor", "Moderate", "Severe", "Fatal"}
    invalid_severity_rate = float((~accidents["severity"].astype(str).isin(valid_severity)).mean())
    _add_result(
        results,
        name="accidents.invalid_severity_rate",
        metric=invalid_severity_rate,
        threshold=0.0,
        notes="Severity must be one of Minor/Moderate/Severe/Fatal",
        pass_limit=0.0,
        warn_limit=0.002,
    )

    accident_ts = pd.to_datetime(accidents["date_time"], utc=True, errors="coerce")
    future_rate = float((accident_ts > pd.Timestamp(datetime.now(UTC))).mean())
    _add_result(
        results,
        name="accidents.future_date_rate",
        metric=future_rate,
        threshold=0.0,
        notes="Accident timestamps should not be in the future",
        pass_limit=0.0,
        warn_limit=0.0,
    )
    latest_accident = accident_ts.max()
    recency_days = (pd.Timestamp(datetime.now(UTC)) - latest_accident).total_seconds() / 86400 if pd.notna(latest_accident) else None
    _add_result(
        results,
        name="accidents.recency_days",
        metric=recency_days,
        threshold=7.0,
        notes="Latest accident feed should be fresh enough for reporting",
        pass_limit=7.0,
        warn_limit=30.0,
        failed=recency_days is None,
    )

    if "weather" in accidents.columns:
        missing_weather_rate = _null_rate(accidents, "weather")
        _add_result(
            results,
            name="accidents.missing_weather_context_rate",
            metric=missing_weather_rate,
            threshold=0.02,
            notes="Incident-level weather enrichment coverage",
            pass_limit=0.02,
            warn_limit=0.10,
        )

    if "p95_speed" in model_df.columns:
        out_speed = float(((model_df["p95_speed"] < 0) | (model_df["p95_speed"] > 220)).mean())
        _add_result(
            results,
            name="model.p95_speed_out_of_range_rate",
            metric=out_speed,
            threshold=0.0,
            notes="P95 speed should be within 0..220 km/h",
            pass_limit=0.0,
            warn_limit=0.005,
        )

    if "daily_volume" in model_df.columns:
        negative_volume_rate = float((model_df["daily_volume"] < 0).mean())
        _add_result(
            results,
            name="model.daily_volume_negative_rate",
            metric=negative_volume_rate,
            threshold=0.0,
            notes="Daily volume cannot be negative",
            pass_limit=0.0,
            warn_limit=0.0,
        )

    if {"road_id", "date"}.issubset(model_df.columns):
        model_dup_rate = _duplicate_rate(model_df, ["road_id", "date"])
        _add_result(
            results,
            name="model.duplicate_road_day_rate",
            metric=model_dup_rate,
            threshold=0.0,
            notes="Model dataset should be unique at road-day grain",
            pass_limit=0.0,
            warn_limit=0.001,
        )

    if "weather_mode" in model_df.columns:
        missing_daily_weather_rate = float(
            model_df["weather_mode"].isna().mean()
            + (model_df["weather_mode"].astype(str).eq("Unknown").mean())
        )
        _add_result(
            results,
            name="model.missing_daily_weather_context_rate",
            metric=missing_daily_weather_rate,
            threshold=0.05,
            notes="Road-day weather enrichment coverage",
            pass_limit=0.05,
            warn_limit=0.15,
        )

    if "has_fatality" in model_df.columns:
        positive_rate = float(model_df["has_fatality"].mean())
        class_balance_gap = abs(positive_rate - 0.10)
        _add_result(
            results,
            name="model.target_positive_rate_gap",
            metric=class_balance_gap,
            threshold=0.10,
            notes="Target prevalence should stay within a workable band for model training",
            pass_limit=0.10,
            warn_limit=0.16,
        )

    gate_status = "PASS"
    if any(r.status == "FAIL" for r in results):
        gate_status = "FAIL"
    elif any(r.status == "WARN" for r in results):
        gate_status = "WARN"

    summary = {
        "pass": sum(r.status == "PASS" for r in results),
        "warn": sum(r.status == "WARN" for r in results),
        "fail": sum(r.status == "FAIL" for r in results),
        "total": len(results),
        "gate_status": gate_status,
    }
    return results, summary


def to_markdown(results: List[QualityRuleResult], summary: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Data Quality Report")
    lines.append("")
    lines.append("This report combines explicit data contracts with operational quality checks.")
    lines.append("")
    lines.append(
        f"- Overall gate: **{summary['gate_status']}**"
    )
    lines.append(
        f"- PASS: {summary['pass']}  |  WARN: {summary['warn']}  |  FAIL: {summary['fail']}  |  TOTAL: {summary['total']}"
    )
    lines.append("")
    lines.append("| Rule | Status | Metric | Threshold | Notes |")
    lines.append("|---|---:|---:|---:|---|")
    for rule in results:
        metric = "" if rule.metric is None else f"{rule.metric:.4f}"
        threshold = "" if rule.threshold is None else f"{rule.threshold:.4f}"
        lines.append(f"| {rule.name} | {rule.status} | {metric} | {threshold} | {rule.notes} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("- **PASS**: within the expected quality threshold.")
    lines.append("- **WARN**: acceptable for demo analytics, but requires remediation before production publication.")
    lines.append("- **FAIL**: blocks trusted reporting or model usage until fixed.")
    return "\n".join(lines)
