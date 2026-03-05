from __future__ import annotations

from typing import Any

from traffic_analytics_demo.ai.providers.base import AIResult
from traffic_analytics_demo.ai.providers.local_gateway_provider import LocalGatewayProvider
from traffic_analytics_demo.ai.providers.mock_provider import MockProvider
from traffic_analytics_demo.config import RuntimeSettings

_FALLBACK_WARNING = (
    "AI gateway unavailable or misconfigured. Showing deterministic offline analyst output."
)


def _fallback(prompt: str, snapshot: dict[str, Any], warning: str | None = None) -> AIResult:
    text = MockProvider().generate(prompt=prompt, snapshot=snapshot)
    return AIResult(
        provider="mock",
        text=text,
        warning=warning,
        used_fallback=warning is not None,
    )


def generate_analyst_insight(
    prompt: str,
    snapshot: dict[str, Any],
    settings: RuntimeSettings,
) -> AIResult:
    provider_name = settings.llm_provider

    if provider_name == "disabled":
        return _fallback(prompt, snapshot, warning="AI provider is disabled by configuration.")

    if provider_name == "mock":
        return _fallback(prompt, snapshot)

    if provider_name == "local_gateway":
        if not settings.llm_gateway_url:
            return _fallback(prompt, snapshot, warning=_FALLBACK_WARNING)
        provider = LocalGatewayProvider(
            gateway_url=settings.llm_gateway_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        try:
            text = provider.generate(prompt=prompt, snapshot=snapshot)
            return AIResult(provider=provider.name, text=text, warning=None, used_fallback=False)
        except Exception:
            return _fallback(prompt, snapshot, warning=_FALLBACK_WARNING)

    return _fallback(prompt, snapshot, warning="Unsupported AI provider; fallback mode enabled.")


def build_snapshot(
    *,
    top_region: str,
    severe_rate: float,
    top_hotspot: str,
    accidents: int,
    fatalities: int,
    injuries: int,
    dq_gate: str,
) -> dict[str, Any]:
    return {
        "top_region": top_region,
        "severe_rate": severe_rate,
        "top_hotspot": top_hotspot,
        "kpi_summary": {
            "accidents": accidents,
            "fatalities": fatalities,
            "injuries": injuries,
            "dq_gate": dq_gate,
        },
    }
