from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_smoke(prepared_demo_env: dict[str, Path]) -> None:
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    at = AppTest.from_file(str(app_path))
    at.run(timeout=120)

    assert len(at.exception) == 0
    assert len(at.error) == 0
    assert len(at.warning) == 0
    assert [tab.label for tab in at.tabs] == [
        "Overview",
        "Hotspots",
        "Diagnostics",
        "Interventions",
        "Quality",
        "Model",
        "AI Analyst",
        "Power BI & Governance",
    ]
