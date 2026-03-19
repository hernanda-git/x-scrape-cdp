from __future__ import annotations

import os
from typing import Any

import httpx


async def post_webhook(url: str, payload: dict[str, Any]) -> None:
    secret = os.getenv("WEBHOOK_SECRET", "")
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Webhook-Secret"] = secret

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
