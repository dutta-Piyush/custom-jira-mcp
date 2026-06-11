"""Issue comment, watcher and worklog tools."""

from __future__ import annotations

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def get_comments(issue_key: str) -> str:
    """Get all comments on a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/api/2/issue/{issue_key}/comment")
    except JiraError as e:
        return f"ERROR: {e}"

    comments = data.get("comments", [])
    lines = [f"Comments on {issue_key} ({len(comments)}):\n"]
    for cm in comments:
        date = (cm.get("created") or "")[:10]
        author = (cm.get("author") or {}).get("displayName", "")
        body = (cm.get("body") or "")[:500]
        lines.append(f"[{date}] {author}:\n{body}\n")
    return "\n".join(lines)


@mcp.tool()
def add_comment(issue_key: str, body: str) -> str:
    """Add a comment to a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        body: Comment text
    """
    c = get_client()
    try:
        c.post(f"/rest/api/2/issue/{issue_key}/comment", {"body": body})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Comment added to {issue_key}"


@mcp.tool()
def get_watchers(issue_key: str) -> str:
    """List watchers on a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/api/2/issue/{issue_key}/watchers")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Watchers on {issue_key} ({data.get('watchCount', 0)}):\n"]
    for w in data.get("watchers", []):
        lines.append(f"• {w.get('displayName','')}")
    return "\n".join(lines)


@mcp.tool()
def add_watcher(issue_key: str, username: str) -> str:
    """Add a user as a watcher on a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        username: Username to add as watcher
    """
    c = get_client()
    try:
        c.post(f"/rest/api/2/issue/{issue_key}/watchers", username)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Added {username} as watcher on {issue_key}"


@mcp.tool()
def add_worklog(issue_key: str, time_spent: str, comment: str = "") -> str:
    """Log time spent on a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        time_spent: Time spent, e.g. 2h 30m, 1d, 4h
        comment: Worklog comment (optional)
    """
    c = get_client()
    payload: dict = {"timeSpent": time_spent}
    if comment:
        payload["comment"] = comment

    try:
        c.post(f"/rest/api/2/issue/{issue_key}/worklog", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Logged {time_spent} on {issue_key}"
