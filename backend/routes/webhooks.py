"""Receives PayPal webhook events. Signature-verifies before trusting
anything in the body — see paypal/webhooks.py."""

from fastapi import APIRouter, Request

from paypal.webhooks import handle_event, verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/paypal")
async def paypal_webhook(request: Request):
    body = await request.json()
    headers = {k.lower(): v for k, v in request.headers.items()}

    if not verify_signature(headers, body):
        return {"status": "ignored", "reason": "signature verification failed"}

    handle_event(body)
    return {"status": "ok"}
