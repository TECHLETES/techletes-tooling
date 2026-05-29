"""Pydantic models for GitHub webhook payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    login: str | None = None
    user_id: int | None = Field(default=None, alias="id")
    type: str | None = None


class RepositoryInfo(BaseModel):
    full_name: str | None = None
    html_url: str | None = None
    private: bool | None = None


class CommentInfo(BaseModel):
    comment_id: int | None = Field(default=None, alias="id")
    body: str | None = None
    html_url: str | None = None
    user: UserInfo | None = None


class IssueInfo(BaseModel):
    number: int | None = None
    title: str | None = None
    html_url: str | None = None


class PullRequestInfo(BaseModel):
    number: int | None = None
    title: str | None = None
    html_url: str | None = None


class IncomingGitHubEvent(BaseModel):
    sender_login: str | None = None
    sender_id: int | None = None
    sender_type: str | None = None
    repo_full_name: str | None = None
    repo_html_url: str | None = None
    repo_private: bool | None = None
    event_name: str | None = None
    action: str | None = None
    comment_body: str | None = None
    comment_html_url: str | None = None
    comment_id: int | None = None
    comment_user: str | None = None
    issue_number: int | None = None
    issue_title: str | None = None
    issue_body: str | None = None
    issue_html_url: str | None = None
    pr_number: int | None = None
    pr_title: str | None = None
    pr_body: str | None = None
    pr_html_url: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], event_name: str) -> "IncomingGitHubEvent":
        sender = payload.get("sender") or {}
        repository = payload.get("repository") or {}
        comment = payload.get("comment") or {}
        issue = payload.get("issue") or {}
        pull_request = payload.get("pull_request") or {}

        return cls(
            sender_login=sender.get("login"),
            sender_id=sender.get("id"),
            sender_type=sender.get("type"),
            repo_full_name=repository.get("full_name"),
            repo_html_url=repository.get("html_url"),
            repo_private=repository.get("private"),
            event_name=event_name,
            action=payload.get("action"),
            comment_body=comment.get("body"),
            comment_html_url=comment.get("html_url"),
            comment_id=comment.get("id"),
            comment_user=(comment.get("user") or {}).get("login"),
            issue_number=issue.get("number"),
            issue_title=issue.get("title"),
            issue_body=issue.get("body"),
            issue_html_url=issue.get("html_url"),
            pr_number=pull_request.get("number"),
            pr_title=pull_request.get("title"),
            pr_body=pull_request.get("body"),
            pr_html_url=pull_request.get("html_url"),
        )


class UnifiedPayload(BaseModel):
    source: str = "github-webhook-proxy"
    event_name: str
    action: str | None = None
    sender: UserInfo
    repository: RepositoryInfo
    comment: CommentInfo | None = None
    issue: IssueInfo | None = None
    pull_request: PullRequestInfo | None = None
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
