from __future__ import annotations

from traffic_analytics_demo.ai.service import build_snapshot, generate_analyst_insight
from traffic_analytics_demo.config import RuntimeSettings


def _settings(provider: str, gateway_url: str | None = None) -> RuntimeSettings:
    return RuntimeSettings(
        pipeline_name="traffic_safety_analytics",
        default_days=30,
        default_seed=7,
        log_level="INFO",
        streamlit_port=8501,
        llm_provider=provider,
        llm_model="local-analyst-v1",
        llm_gateway_url=gateway_url,
        llm_timeout_seconds=5,
    )


def test_ai_service_disabled_falls_back_to_mock() -> None:
    result = generate_analyst_insight(
        prompt="Give actions",
        snapshot=build_snapshot(
            top_region="North",
            severe_rate=0.12,
            top_hotspot="R-1",
            accidents=100,
            fatalities=5,
            injuries=20,
            dq_gate="PASS",
        ),
        settings=_settings("disabled"),
    )
    assert result.provider == "mock"
    assert result.used_fallback
    assert "offline heuristic mode" in result.text


def test_ai_service_local_gateway_without_url_fails_closed() -> None:
    result = generate_analyst_insight(
        prompt="Give actions",
        snapshot=build_snapshot(
            top_region="North",
            severe_rate=0.12,
            top_hotspot="R-1",
            accidents=100,
            fatalities=5,
            injuries=20,
            dq_gate="PASS",
        ),
        settings=_settings("local_gateway", gateway_url=None),
    )
    assert result.provider == "mock"
    assert result.used_fallback
    assert result.warning is not None
