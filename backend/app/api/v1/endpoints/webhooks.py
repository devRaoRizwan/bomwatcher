import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, status

from app.api.deps import AppSettings, get_webhook_service
from app.core.exceptions import AuthenticationError, BadRequestError, ServiceUnavailableError
from app.integrations.github.signature import is_valid_signature
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

MAX_WEBHOOK_BYTES = 5 * 1024 * 1024


@router.post("/github", status_code=status.HTTP_202_ACCEPTED, include_in_schema=False)
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    settings: AppSettings,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    x_github_event: Annotated[str, Header()],
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    secret = settings.github_webhook_secret.get_secret_value()
    if not secret:
        raise ServiceUnavailableError("Webhook secret not configured")
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        raise BadRequestError("Payload too large")
    if not is_valid_signature(secret, body, x_hub_signature_256):
        raise AuthenticationError("Invalid webhook signature")
    try:
        payload = json.loads(body)
    except ValueError as e:
        raise BadRequestError("Invalid JSON") from e

    job = service.handle(x_github_event, payload)
    if job:
        background.add_task(job)
    return {"ok": True}
