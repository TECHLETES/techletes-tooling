"""FastAPI entrypoint for the GitHub webhook authorization proxy."""

from __future__ import annotations

import json
import logging
from urllib import error, request

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .allowed_users import is_user_allowed
from .auth import verify_signature
from .config import Settings, load_settings
from .forwarding import build_unified_payload, forward_to_hermes
from .logging_config import configure_logging
from .models import IncomingGitHubEvent


logger = logging.getLogger(__name__)

ALLOWED_EVENTS = {"issue_comment", "pull_request_review_comment", "commit_comment"}

app = FastAPI(title="GitHub Webhook Authorization Proxy")
app.state.settings = None


def get_settings() -> Settings:
    settings = getattr(app.state, "settings", None)
    if settings is None:
        settings = load_settings()
        app.state.settings = settings
    return settings


def _check_hermes_gateway(url: str) -> None:
    try:
        req = request.Request(url, method="HEAD")
        with request.urlopen(req, timeout=5):
            logger.info("Hermes gateway reachable at %s", url)
    except error.HTTPError as exc:
        logger.info("Hermes gateway responded to HEAD with HTTP %s at %s", exc.code, url)
    except (error.URLError, OSError) as exc:
        logger.warning("Hermes gateway not reachable at startup: %s", exc)


@app.on_event("startup")
async def startup_event() -> None:
    configure_logging()
    settings = load_settings()
    app.state.settings = settings
    _check_hermes_gateway(settings.hermes_gateway_url)


@app.get("/health")
@app.post("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/webhooks/github")
async def github_webhook(request_: Request) -> JSONResponse:
    settings = get_settings()

    try:
        raw_body = await request_.body()
        signature_header = request_.headers.get("X-Hub-Signature-256")
        event_name = request_.headers.get("X-GitHub-Event") or "unknown"

        if not verify_signature(raw_body, signature_header, settings.hermes_secret):
            logger.warning("Rejected webhook with invalid signature for event=%s", event_name)
            return JSONResponse({"status": "ok"})

        # Only process allowed GitHub event types
        if event_name not in ALLOWED_EVENTS:
            logger.info("Rejected event type %s (not in allowed list)", event_name)
            return JSONResponse({"status": "ok"})

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Rejected webhook with malformed JSON for event=%s", event_name)
            return JSONResponse({"status": "ok"})

        event = IncomingGitHubEvent.from_payload(payload, event_name)
        sender_login = event.sender_login or ""

        if not sender_login:
            logger.warning("Blocked webhook with missing sender for event=%s", event_name)
            return JSONResponse({"status": "ok"})

        if not is_user_allowed(sender_login, settings.allowed_users, event_name, settings.event_auth):
            logger.info("Blocked %s for %s", sender_login, event_name)
            return JSONResponse({"status": "ok"})

        unified_payload = build_unified_payload(event)
        forwarded = forward_to_hermes(unified_payload, settings.hermes_gateway_url, settings.hermes_secret)
        if forwarded:
            logger.info("Forwarded %s from %s", event_name, sender_login)
        else:
            logger.warning("Failed to forward %s from %s", event_name, sender_login)

        return JSONResponse({"status": "ok"})
    except Exception:
        logger.exception("Unexpected error while handling GitHub webhook")
        return JSONResponse({"status": "ok"})
