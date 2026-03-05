from __future__ import annotations

import pytest

from traffic_analytics_demo.config import get_paths, get_settings


def test_paths_include_staged_and_curated(isolated_runtime_env: dict[str, object]) -> None:
    paths = get_paths()
    assert paths.data_staged.exists()
    assert paths.data_curated.exists()
    assert paths.data_processed.exists()


def test_config_rejects_invalid_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAFFIC_ANALYTICS_LLM_PROVIDER", "invalid_provider")
    with pytest.raises(ValueError, match="TRAFFIC_ANALYTICS_LLM_PROVIDER"):
        get_settings()


def test_config_rejects_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAFFIC_ANALYTICS_STREAMLIT_PORT", "70000")
    with pytest.raises(ValueError, match="TRAFFIC_ANALYTICS_STREAMLIT_PORT"):
        get_settings()
