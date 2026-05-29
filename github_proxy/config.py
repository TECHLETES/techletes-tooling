"""Configuration loading for the GitHub webhook proxy."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_LISTEN_HOST = "0.0.0.0"
DEFAULT_LISTEN_PORT = 8655
DEFAULT_HERMES_GATEWAY_URL = "http://localhost:8644/webhooks/github-mentions"
DEFAULT_HERMES_SECRET = "changeme"
DEFAULT_ALLOWED_USERS = ["thom-techlete"]


@dataclass(slots=True)
class Settings:
    listen_host: str
    listen_port: int
    hermes_gateway_url: str
    hermes_secret: str
    allowed_users: list[str]
    event_auth: dict[str, object]


def _parse_scalar(value: str) -> object:
    token = value.strip()
    if not token:
        return ""

    if token in {"null", "~"}:
        return None
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False
    if token == "{}":
        return {}
    if token == "[]":
        return []

    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
        return token[1:-1]

    try:
        return int(token)
    except ValueError:
        return token


def _strip_comments(line: str) -> str:
    if "#" not in line:
        return line.rstrip()
    in_single = False
    in_double = False
    result: list[str] = []
    for char in line:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            break
        result.append(char)
    return "".join(result).rstrip()


def _preprocess_yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = _strip_comments(raw_line)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.lstrip()))
    return lines


def _parse_yaml_block(lines: list[tuple[int, str]], start: int, indent: int) -> tuple[object, int]:
    if start >= len(lines):
        return {}, start

    current_indent, current_text = lines[start]
    if current_indent < indent:
        return {}, start

    if current_text.startswith("- "):
        items: list[object] = []
        index = start
        while index < len(lines):
            line_indent, line_text = lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                index += 1
                continue
            if not line_text.startswith("- "):
                break

            item_text = line_text[2:].strip()
            index += 1
            if not item_text:
                value, index = _parse_yaml_block(lines, index, indent + 2)
                items.append(value)
                continue

            if ":" in item_text and not item_text.startswith("{"):
                key, rest = item_text.split(":", 1)
                mapping: dict[str, object] = {}
                rest = rest.strip()
                mapping[key.strip()] = _parse_scalar(rest) if rest else {}
                items.append(mapping)
                continue

            items.append(_parse_scalar(item_text))
        return items, index

    mapping: dict[str, object] = {}
    index = start
    while index < len(lines):
        line_indent, line_text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            index += 1
            continue
        if line_text.startswith("- "):
            break
        if ":" not in line_text:
            raise ValueError(f"Invalid YAML line: {line_text!r}")

        key, rest = line_text.split(":", 1)
        key = key.strip().strip('"')
        rest = rest.strip()
        index += 1
        if rest:
            mapping[key] = _parse_scalar(rest)
            continue

        value, index = _parse_yaml_block(lines, index, indent + 2)
        mapping[key] = value

    return mapping, index


def _load_structured_config(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        lines = _preprocess_yaml_lines(text)
        parsed, _ = _parse_yaml_block(lines, 0, 0)

    if not isinstance(parsed, dict):
        raise ValueError("Configuration must be a mapping")
    return parsed


def _coerce_list(value: object, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return default


def _coerce_event_auth(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _flatten_config(raw: dict[str, Any]) -> Settings:
    proxy = raw.get("proxy") if isinstance(raw.get("proxy"), dict) else raw

    listen_host = str(proxy.get("listen_host", DEFAULT_LISTEN_HOST))
    listen_port = int(proxy.get("listen_port", DEFAULT_LISTEN_PORT))
    hermes_gateway_url = str(proxy.get("hermes_gateway_url", DEFAULT_HERMES_GATEWAY_URL))
    hermes_secret = str(proxy.get("hermes_secret", DEFAULT_HERMES_SECRET))

    allowed_users = _coerce_list(raw.get("allowed_users"), DEFAULT_ALLOWED_USERS)
    event_auth = _coerce_event_auth(raw.get("event_auth"))

    return Settings(
        listen_host=listen_host,
        listen_port=listen_port,
        hermes_gateway_url=hermes_gateway_url,
        hermes_secret=hermes_secret,
        allowed_users=allowed_users,
        event_auth=event_auth,
    )


def _candidate_paths() -> list[Path]:
    home = Path(os.path.expanduser("~/.hermes"))
    repo_root = Path(__file__).resolve().parent.parent
    return [
        home / "github-webhook-proxy.json",
        home / "github-webhook-proxy.yaml",
        repo_root / "config" / "github-proxy.yaml.example",
    ]


def load_settings() -> Settings:
    """Load settings from the first available config path."""

    for candidate in _candidate_paths():
        if not candidate.exists():
            continue
        raw = _load_structured_config(candidate.read_text(encoding="utf-8"))
        return _flatten_config(raw)

    return Settings(
        listen_host=DEFAULT_LISTEN_HOST,
        listen_port=DEFAULT_LISTEN_PORT,
        hermes_gateway_url=DEFAULT_HERMES_GATEWAY_URL,
        hermes_secret=DEFAULT_HERMES_SECRET,
        allowed_users=DEFAULT_ALLOWED_USERS.copy(),
        event_auth={},
    )

