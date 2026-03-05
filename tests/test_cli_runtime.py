from __future__ import annotations

import json


def test_cli_all_writes_operational_artifacts(prepared_demo_env: dict[str, object]) -> None:
    out_dir = prepared_demo_env["out_dir"]
    powerbi_dir = prepared_demo_env["powerbi_dir"]

    run_summary = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))

    assert run_summary["status"] == "SUCCESS"
    assert run_summary["metadata"]["days"] == 30
    assert len(run_summary["steps"]) == 9
    assert all(step["status"] == "SUCCESS" for step in run_summary["steps"])

    assert (out_dir / "pipeline.log").exists()
    assert (out_dir / "scenario_summary.csv").exists()
    assert (out_dir / "solution_overview.md").exists()
    assert (powerbi_dir / "scenario_summary.csv").exists()
