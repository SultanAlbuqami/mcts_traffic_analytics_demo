from __future__ import annotations

from typing import Any


class MockProvider:
    name = "mock"

    def generate(self, prompt: str, snapshot: dict[str, Any]) -> str:
        top_region = snapshot.get("top_region", "n/a")
        severe_rate = snapshot.get("severe_rate", 0.0)
        top_hotspot = snapshot.get("top_hotspot", "n/a")
        kpi_summary = snapshot.get("kpi_summary", {})

        return (
            "AI Analyst (offline heuristic mode)\n\n"
            f"Prompt focus: {prompt.strip() or 'General traffic-safety operations'}\n\n"
            "Priority Insights:\n"
            f"- Highest pressure region: {top_region}\n"
            f"- Severe incident rate: {severe_rate:.2%}\n"
            f"- Most critical hotspot: {top_hotspot}\n\n"
            "Operational Actions (next 24h):\n"
            "- Deploy enforcement and signage to the highest-risk corridor.\n"
            "- Increase patrol frequency during high-severity windows.\n"
            "- Validate weather/visibility controls on affected segments.\n"
            "- Re-run scenario package ranking after interventions.\n\n"
            "Evidence Snapshot:\n"
            f"- Accidents: {kpi_summary.get('accidents', 'n/a')}\n"
            f"- Fatalities: {kpi_summary.get('fatalities', 'n/a')}\n"
            f"- Injuries: {kpi_summary.get('injuries', 'n/a')}\n"
            f"- Quality Gate: {kpi_summary.get('dq_gate', 'n/a')}\n"
        )
