"""Build and forward unified GitHub webhook payloads to Hermes."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any
from urllib import error, request

from .models import (
    CommentInfo,
    IncomingGitHubEvent,
    IssueInfo,
    PullRequestInfo,
    RepositoryInfo,
    UnifiedPayload,
    UserInfo,
)


logger = logging.getLogger(__name__)


def build_unified_payload(event: IncomingGitHubEvent) -> dict[str, Any]:
    """Create the payload that gets forwarded to Hermes."""

    comment = None
    if event.comment_body or event.comment_html_url or event.comment_id is not None or event.comment_user:
        comment = CommentInfo(
            comment_id=event.comment_id,
            body=event.comment_body,
            html_url=event.comment_html_url,
            user=UserInfo(login=event.comment_user),
        )

    issue = None
    if event.issue_number is not None or event.issue_title or event.issue_html_url:
        issue = IssueInfo(
            number=event.issue_number,
            title=event.issue_title,
            html_url=event.issue_html_url,
        )

    pull_request = None
    if event.pr_number is not None or event.pr_title or event.pr_html_url:
        pull_request = PullRequestInfo(
            number=event.pr_number,
            title=event.pr_title,
            html_url=event.pr_html_url,
        )

    payload = UnifiedPayload(
        event_name=event.event_name or "unknown",
        action=event.action,
        sender=UserInfo(login=event.sender_login, user_id=event.sender_id, type=event.sender_type),
        repository=RepositoryInfo(
            full_name=event.repo_full_name,
            html_url=event.repo_html_url,
            private=event.repo_private,
        ),
        comment=comment,
        issue=issue,
        pull_request=pull_request,
    )

    dump = getattr(payload, "model_dump", None)
    if callable(dump):
        return dump()
    return payload.dict()


def forward_to_hermes(payload: dict[str, Any], hermes_url: str, secret: str, event_name: str = "unknown") -> bool:
    """POST payload to Hermes with an HMAC signature and the original event type."""

    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    req = request.Request(
        hermes_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": event_name,
        },
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            status = getattr(response, "status", response.getcode())
            return 200 <= int(status) < 300
    except error.HTTPError as exc:
        logger.warning("Hermes returned HTTP %s while forwarding", exc.code)
        return False
    except error.URLError as exc:
        logger.error("Hermes forwarding failed: %s", exc)
        return False
    except OSError as exc:
        logger.error("Hermes forwarding failed: %s", exc)
        return False

