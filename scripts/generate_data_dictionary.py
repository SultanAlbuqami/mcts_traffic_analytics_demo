"""
Generate docs/data_dictionary.md from data/curated/*.csv

Sensitivity classification rules (documented):
  - Columns containing: incident_id, violation_id, sensor_id, record_hash,
    ingest_batch_id, extracted_at_utc → INTERNAL
    (traceability fields; not public-facing but not sensitive PII)
  - Columns containing: driver_age_band → INTERNAL
    (demographic proxy; no PII but treated with care)
  - All other columns → PUBLIC
    (aggregated, anonymised, synthetic demo data)

Usage:
    python scripts/generate_data_dictionary.py
    python scripts/generate_data_dictionary.py --curated-dir data/curated --output docs/data_dictionary.md
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path


def _sensitivity(col: str) -> str:
    """Return PUBLIC | INTERNAL | CONFIDENTIAL based on column name patterns."""
    internal_patterns = {
        "incident_id",
        "violation_id",
        "sensor_id",
        "record_hash",
        "ingest_batch_id",
        "extracted_at_utc",
        "driver_age_band",
        "source_system",
    }
    col_lower = col.lower()
    for p in internal_patterns:
        if p in col_lower:
            return "INTERNAL"
    return "PUBLIC"


def _safe_samples(series, n: int = 3) -> list[str]:
    """Return up to n unique non-null sample values as strings."""
    try:
        vals = series.dropna().unique()[:n]
        return [str(v) for v in vals]
    except Exception:
        return []


def generate(curated_dir: Path, output: Path) -> None:
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is required. Run: pip install pandas", file=sys.stderr)
        sys.exit(1)

    csvs = sorted(curated_dir.glob("*.csv"))
    if not csvs:
        print(f"ERROR: No CSV files found in {curated_dir}", file=sys.stderr)
        sys.exit(1)

    lines: list[str] = [
        "# Data Dictionary — Curated Layer",
        "",
        f"> **Generated:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  ",
        f"> **Source:** `{curated_dir}`  ",
        "> **Data:** 100% synthetic (seed=42) — no real personal data.  ",
        ">",
        "> **Sensitivity levels:**",
        "> - `PUBLIC` — safe for external sharing; aggregated or anonymised.",
        "> - `INTERNAL` — traceability / operational fields; share within team only.",
        "> - `CONFIDENTIAL` — not present in this dataset (would require access controls).",
        "",
    ]

    for csv_path in csvs:
        df = pd.read_csv(csv_path)
        table_name = csv_path.stem
        row_count = len(df)
        col_count = len(df.columns)

        lines += [
            f"## `{table_name}`",
            "",
            f"- **File:** `{csv_path.name}`",
            f"- **Rows:** {row_count:,}",
            f"- **Columns:** {col_count}",
            "",
            "| Column | Type | Null % | Sensitivity | Sample Values |",
            "|--------|------|--------|-------------|---------------|",
        ]

        for col in df.columns:
            dtype = str(df[col].dtype)
            null_pct = round(df[col].isna().mean() * 100, 1)
            sensitivity = _sensitivity(col)
            samples = _safe_samples(df[col])
            sample_str = ", ".join(f"`{s}`" for s in samples) if samples else "—"
            lines.append(f"| `{col}` | {dtype} | {null_pct}% | {sensitivity} | {sample_str} |")

        lines += ["", "---", ""]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: Data dictionary written to {output} ({len(csvs)} tables)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate data dictionary from curated CSVs")
    parser.add_argument(
        "--curated-dir",
        default="data/curated",
        help="Path to curated CSV directory (default: data/curated)",
    )
    parser.add_argument(
        "--output",
        default="docs/data_dictionary.md",
        help="Output markdown path (default: docs/data_dictionary.md)",
    )
    args = parser.parse_args()

    curated_dir = Path(args.curated_dir)
    output = Path(args.output)

    if not curated_dir.exists():
        print(f"ERROR: curated dir not found: {curated_dir}", file=sys.stderr)
        sys.exit(1)

    generate(curated_dir, output)


if __name__ == "__main__":
    main()
