from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def isolated_runtime_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    out_dir = tmp_path / "out"
    powerbi_dir = out_dir / "powerbi"

    env_map = {
        "TRAFFIC_ANALYTICS_DATA_DIR": data_root,
        "TRAFFIC_ANALYTICS_RAW_DIR": raw_dir,
        "TRAFFIC_ANALYTICS_PROCESSED_DIR": processed_dir,
        "TRAFFIC_ANALYTICS_OUT_DIR": out_dir,
        "TRAFFIC_ANALYTICS_POWERBI_DIR": powerbi_dir,
        "TRAFFIC_ANALYTICS_LOG_LEVEL": "WARNING",
    }
    for key, value in env_map.items():
        monkeypatch.setenv(key, str(value))

    return {
        "data_root": data_root,
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "out_dir": out_dir,
        "powerbi_dir": powerbi_dir,
    }


@pytest.fixture
def prepared_demo_env(
    isolated_runtime_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    from traffic_analytics_demo.cli import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "traffic_analytics_demo",
            "all",
            "--days",
            "30",
            "--seed",
            "7",
            "--road-segments",
            "24",
            "--accidents",
            "500",
            "--violations",
            "1600",
            "--sensors-rows",
            "5000",
        ],
    )
    main()
    return isolated_runtime_env
