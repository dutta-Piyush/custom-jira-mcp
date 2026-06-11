"""Meta / admin tools: issue types, priorities, statuses, fields, raw API."""

from __future__ import annotations

import json

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def list_issue_types() -> str:
    """List all issue types defined in the Jira instance."""
    c = get_client()
    try:
        types = c.get("/rest/api/2/issuetype")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = ["Issue Types:\n"]
    for t in types:
        sub = " (subtask)" if t.get("subtask") else ""
        lines.append(f"• {t.get('name','')}{sub}")
    return "\n".join(lines)


@mcp.tool()
def list_priorities() -> str:
    """List all priority levels defined in the Jira instance."""
    c = get_client()
    try:
        priorities = c.get("/rest/api/2/priority")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = ["Priorities:\n"]
    for p in priorities:
        lines.append(f"• {p.get('name','')} (ID: {p.get('id','')})")
    return "\n".join(lines)


@mcp.tool()
def list_statuses() -> str:
    """List all workflow statuses in the Jira instance."""
    c = get_client()
    try:
        statuses = c.get("/rest/api/2/status")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = ["Statuses:\n"]
    for s in statuses:
        cat = (s.get("statusCategory") or {}).get("name", "")
        lines.append(f"• {s.get('name','')} [{cat}]")
    return "\n".join(lines)


@mcp.tool()
def list_fields() -> str:
    """List all Jira fields including custom fields and their IDs."""
    c = get_client()
    try:
        fields = c.get("/rest/api/2/field")
    except JiraError as e:
        return f"ERROR: {e}"

    custom = sum(1 for f in fields if f.get("custom"))
    lines = [f"Fields ({len(fields)} total, {custom} custom):\n"]
    for f in fields:
        tag = " [custom]" if f.get("custom") else ""
        lines.append(f"• {f.get('name','')} ({f.get('id','')}){tag}")
    return "\n".join(lines)


@mcp.tool()
def raw_api_call(method: str, path: str, body: str = "") -> str:
    """Make a raw Jira REST API call for advanced operations.

    Args:
        method: HTTP method: GET, POST, or PUT
        path: API path, e.g. /rest/api/2/issue/DEVOPS-123
        body: JSON request body string (for POST/PUT, optional)
    """
    c = get_client()
    method = method.upper()
    payload = None
    if body:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            return f"ERROR: invalid JSON body: {e}"

    try:
        if method == "GET":
            result = c.get(path)
        elif method == "POST":
            result = c.post(path, payload)
        elif method == "PUT":
            result = c.put(path, payload)
        else:
            return f"ERROR: unsupported method '{method}' — use GET, POST, or PUT"
    except JiraError as e:
        return f"ERROR: {e}"

    if not result:
        return "OK (empty response)"
    try:
        return json.dumps(result, indent=2, ensure_ascii=False)[:4000]
    except Exception:
        return str(result)[:4000]
