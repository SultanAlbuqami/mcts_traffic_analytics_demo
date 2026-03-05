from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocalGatewayProvider:
    name = "local_gateway"

    def __init__(self, gateway_url: str, model: str, timeout_seconds: int) -> None:
        self.gateway_url = gateway_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, snapshot: dict[str, Any]) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "snapshot": snapshot,
            }
        ).encode("utf-8")
        req = Request(
            url=self.gateway_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError(f"LLM gateway request failed: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM gateway returned non-JSON response.") from exc

        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("LLM gateway JSON must include non-empty 'text'.")
        return text.strip()
