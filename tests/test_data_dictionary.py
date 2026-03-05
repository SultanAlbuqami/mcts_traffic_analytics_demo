"""Smoke test: data dictionary generator runs and includes all curated tables."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CURATED_DIR = Path("data/curated")
OUTPUT_PATH = Path("docs/data_dictionary.md")
EXPECTED_TABLES = {"accidents", "model_df", "roads", "sensors", "violations"}


def test_data_dictionary_generation(tmp_path):
    """Generator writes a markdown file containing all curated table names."""
    output = tmp_path / "data_dictionary.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_data_dictionary.py",
            "--curated-dir",
            str(CURATED_DIR),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Generator failed:\n{result.stderr}"
    assert output.exists(), "Output markdown file was not created"

    content = output.read_text(encoding="utf-8")
    for table in EXPECTED_TABLES:
        assert f"`{table}`" in content, f"Table '{table}' missing from data dictionary"

    # Must contain sensitivity classifications
    assert "PUBLIC" in content
    assert "INTERNAL" in content


def test_data_dictionary_already_written():
    """The committed docs/data_dictionary.md must exist and contain all tables."""
    assert OUTPUT_PATH.exists(), (
        "docs/data_dictionary.md missing — run: python scripts/generate_data_dictionary.py"
    )
    content = OUTPUT_PATH.read_text(encoding="utf-8")
    for table in EXPECTED_TABLES:
        assert f"`{table}`" in content, f"Table '{table}' missing from committed data dictionary"
