"""User and filter tools."""

from __future__ import annotations

from urllib.parse import quote

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def search_users(query: str) -> str:
    """Search for Jira users by username or display name.

    Args:
        query: Username or display name to search for
    """
    c = get_client()
    try:
        users = c.get(f"/rest/api/2/user/search?username={quote(query)}&maxResults=10")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Users matching '{query}' ({len(users)}):\n"]
    for u in users:
        active = "active" if u.get("active") else "inactive"
        lines.append(
            f"• {u.get('displayName','')} ({u.get('name','')}) "
            f"— {u.get('emailAddress','')} [{active}]"
        )
    return "\n".join(lines)


@mcp.tool()
def get_myself() -> str:
    """Get details of the currently authenticated Jira user."""
    c = get_client()
    try:
        user = c.get("/rest/api/2/myself")
    except JiraError as e:
        return f"ERROR: {e}"

    return (
        f"Logged in as: {user.get('displayName','')} ({user.get('name','')})\n"
        f"Email: {user.get('emailAddress','')}\n"
        f"Timezone: {user.get('timeZone','')}"
    )


@mcp.tool()
def get_my_filters() -> str:
    """List your favourite/saved Jira filters."""
    c = get_client()
    try:
        filters = c.get("/rest/api/2/filter/favourite")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"My Filters ({len(filters)}):\n"]
    for f in filters:
        lines.append(f"• {f.get('name')} (ID: {f.get('id','')})\n  JQL: {f.get('jql','')}\n")
    return "\n".join(lines)


@mcp.tool()
def create_filter(name: str, jql: str, description: str = "") -> str:
    """Create and save a new Jira filter.

    Args:
        name: Filter name
        jql: JQL query for the filter
        description: Filter description (optional)
    """
    c = get_client()
    payload: dict = {"name": name, "jql": jql, "favourite": True}
    if description:
        payload["description"] = description

    try:
        result = c.post("/rest/api/2/filter", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Created filter: {result.get('name')} (ID: {result.get('id')})"
