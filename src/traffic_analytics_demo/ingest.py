from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .utils import stable_hash, utc_now_iso


@dataclass(frozen=True)
class IngestMeta:
    ingest_batch_id: str
    extracted_at_utc: str


def _add_traceability(df: pd.DataFrame, source_system: str, meta: IngestMeta) -> pd.DataFrame:
    df = df.copy()
    df["source_system"] = source_system
    df["ingest_batch_id"] = meta.ingest_batch_id
    df["extracted_at_utc"] = meta.extracted_at_utc
    # record hash (based on business columns)
    business_cols = [c for c in df.columns if c not in ["record_hash"]]
    df["record_hash"] = [
        stable_hash({c: row[c] for c in business_cols}) for _, row in df.iterrows()
    ]
    return df


def load_sources(raw_dir: Path, ingest_batch_id: str) -> dict[str, pd.DataFrame]:
    meta = IngestMeta(ingest_batch_id=ingest_batch_id, extracted_at_utc=utc_now_iso())

    roads = pd.read_csv(raw_dir / "road_segments.csv")
    roads = _add_traceability(roads, "roads_registry", meta)

    weather = pd.read_csv(raw_dir / "weather_hourly.csv", parse_dates=["date_time"])
    weather = _add_traceability(weather, "meteo_service", meta)

    sensors = pd.read_csv(raw_dir / "speed_sensors.csv", parse_dates=["date_time"])
    sensors = _add_traceability(sensors, "speed_sensors", meta)

    accidents = pd.read_csv(raw_dir / "accidents.csv", parse_dates=["date_time"])
    accidents = _add_traceability(accidents, "accident_reports", meta)

    violations = pd.read_csv(raw_dir / "violations.csv", parse_dates=["date_time"])
    violations = _add_traceability(violations, "violation_system", meta)

    return {
        "roads": roads,
        "weather": weather,
        "sensors": sensors,
        "accidents": accidents,
        "violations": violations,
    }
