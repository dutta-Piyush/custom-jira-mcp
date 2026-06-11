from __future__ import annotations

import threading
import time
from typing import Any

import httpx

from jira_mcp.config import JIRA_PAT, JIRA_URL, TRUST_ENV, VERIFY_SSL


class JiraError(Exception):
    """Raised when the Jira API returns an error."""


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {JIRA_PAT}",
        "Accept": "application/json",
        "X-Atlassian-Token": "no-check",
        "X-ExperimentalApi": "opt-in",
    }


def _parse_error(response: httpx.Response) -> str:
    codes = {
        400: "Bad request — check your input fields",
        401: "Unauthorized — check your JIRA_PAT",
        403: "Forbidden — your PAT lacks permissions for this operation",
        404: "Not found — issue/project/board does not exist",
        409: "Conflict — resource was modified concurrently",
        429: "Rate limited — too many requests, try again shortly",
    }
    base = codes.get(response.status_code, f"Jira API error {response.status_code}")
    try:
        body = response.json()
        msgs = body.get("errorMessages", [])
        errs = body.get("errors", {})
        if msgs:
            base += ": " + "; ".join(msgs)
        if errs:
            base += " [" + ", ".join(f"{k}: {v}" for k, v in errs.items()) + "]"
    except Exception:
        text = response.text[:200]
        if text:
            base += f": {text}"
    return base


class JiraClient:
    """HTTP client wrapping Jira REST API with retry logic."""

    def __init__(self) -> None:
        if not JIRA_URL:
            raise JiraError("JIRA_URL environment variable is not set")
        if not JIRA_PAT:
            raise JiraError("JIRA_PAT environment variable is not set")
        self._base = JIRA_URL.rstrip("/")
        self._client = httpx.Client(
            headers=_headers(),
            verify=VERIFY_SSL,
            timeout=httpx.Timeout(total=60, connect=10),
            trust_env=TRUST_ENV,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = path if path.startswith("http") else self._base + path
        max_retries = 3
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = self._client.request(method, url, **kwargs)
            except httpx.TransportError as exc:
                last_err = exc
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                raise JiraError(f"Connection error: {exc}") from exc

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * (2 if resp.status_code == 429 else 1))
                    continue
                raise JiraError(_parse_error(resp))
            if resp.status_code >= 400:
                raise JiraError(_parse_error(resp))
            if resp.status_code == 204:
                return {}
            return resp.json()
        raise JiraError(f"Max retries exceeded for {method} {path}")  # safeguard

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, payload: Any = None) -> Any:
        return self._request("POST", path, json=payload)

    def put(self, path: str, payload: Any = None) -> Any:
        return self._request("PUT", path, json=payload)

    def close(self) -> None:
        self._client.close()

    @property
    def base_url(self) -> str:
        return self._base


# Module-level singleton — created lazily on first use
_client: JiraClient | None = None
_client_lock = threading.Lock()


def get_client() -> JiraClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = JiraClient()  # raises JiraError if config is missing
    return _client
