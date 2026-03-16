from typing import Any

from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

from app.core.config import settings

router = APIRouter(prefix="/openai", tags=["openai-webhooks"])


def _build_webhook_client() -> OpenAI:
    if not settings.openai_webhook_secret:
        raise HTTPException(status_code=503, detail="OPENAI_WEBHOOK_SECRET is not configured")

    # The SDK requires an api_key on construction, even when we only verify webhooks.
    return OpenAI(
        api_key=settings.openai_api_key or "webhook-verification-only",
        webhook_secret=settings.openai_webhook_secret,
    )


@router.post("/webhooks")
async def receive_openai_webhook(request: Request) -> dict[str, Any]:
    body = await request.body()

    try:
        event = _build_webhook_client().webhooks.unwrap(body, request.headers)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook signature: {exc}") from exc

    event_type = getattr(event, "type", "unknown")
    event_id = getattr(event, "id", "")
    event_data = getattr(event, "data", None)
    response_id = getattr(event_data, "id", None) if event_data is not None else None

    return {
        "received": True,
        "event_type": event_type,
        "event_id": event_id,
        "response_id": response_id,
    }


