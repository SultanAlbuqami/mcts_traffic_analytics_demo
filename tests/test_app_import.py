from __future__ import annotations

from pathlib import Path


def test_streamlit_app_file_exists() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    assert app_path.exists()
