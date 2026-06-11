"""Jira Agile board and sprint tools."""

from __future__ import annotations

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def list_boards() -> str:
    """List all Agile boards (Scrum and Kanban) accessible to you."""
    c = get_client()
    try:
        data = c.get("/rest/agile/1.0/board?maxResults=50")
    except JiraError as e:
        return f"ERROR: {e}"

    boards = data.get("values", [])
    lines = [f"Boards ({len(boards)}):\n"]
    for b in boards:
        lines.append(f"• ID: {b.get('id')} — {b.get('name')} [{b.get('type','')}]")
    return "\n".join(lines)


@mcp.tool()
def list_sprints(board_id: int) -> str:
    """List active and future sprints on an Agile board.

    Args:
        board_id: Agile board ID (get from list_boards)
    """
    c = get_client()
    try:
        data = c.get(f"/rest/agile/1.0/board/{board_id}/sprint?state=active,future")
    except JiraError as e:
        return f"ERROR: {e}"

    sprints = data.get("values", [])
    lines = [f"Sprints ({len(sprints)}):\n"]
    for s in sprints:
        lines.append(f"• ID: {s.get('id')} — {s.get('name')} [{s.get('state','')}]")
        if s.get("goal"):
            lines.append(f"  Goal: {s['goal'][:200]}")
        start = (s.get("startDate") or "")[:10]
        end = (s.get("endDate") or "")[:10]
        if start:
            lines.append(f"  {start} → {end}")
    return "\n".join(lines)


@mcp.tool()
def get_sprint_issues(sprint_id: int) -> str:
    """Get all issues in a sprint.

    Args:
        sprint_id: Sprint ID (get from list_sprints)
    """
    c = get_client()
    try:
        data = c.get(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue"
            "?maxResults=50&fields=summary,status,assignee,priority,issuetype"
        )
    except JiraError as e:
        return f"ERROR: {e}"

    issues = data.get("issues", [])
    lines = [f"Sprint {sprint_id} issues ({len(issues)}):\n"]
    for iss in issues:
        f = iss.get("fields", {})
        assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
        lines.append(
            f"• {iss['key']} [{(f.get('status') or {}).get('name','')}] "
            f"{f.get('summary','')} — {assignee} ({(f.get('priority') or {}).get('name','')})"
        )
    return "\n".join(lines)


@mcp.tool()
def get_board_backlog(board_id: int) -> str:
    """Get backlog issues for an Agile board.

    Args:
        board_id: Agile board ID (get from list_boards)
    """
    c = get_client()
    try:
        data = c.get(
            f"/rest/agile/1.0/board/{board_id}/backlog"
            "?maxResults=30&fields=summary,status,priority,issuetype"
        )
    except JiraError as e:
        return f"ERROR: {e}"

    issues = data.get("issues", [])
    lines = [f"Backlog (board {board_id}) — {len(issues)} issues:\n"]
    for iss in issues:
        f = iss.get("fields", {})
        lines.append(
            f"• {iss['key']} [{(f.get('issuetype') or {}).get('name','')}|"
            f"{(f.get('priority') or {}).get('name','')}] {f.get('summary','')}"
        )
    return "\n".join(lines)


@mcp.tool()
def move_to_sprint(sprint_id: int, issue_keys: list[str]) -> str:
    """Move issues into a sprint.

    Args:
        sprint_id: Target sprint ID
        issue_keys: List of issue keys to move, e.g. ['DEVOPS-1', 'DEVOPS-2']
    """
    c = get_client()
    try:
        c.post(f"/rest/agile/1.0/sprint/{sprint_id}/issue", {"issues": issue_keys})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Moved {len(issue_keys)} issues to sprint {sprint_id}"


@mcp.tool()
def create_sprint(
    name: str,
    board_id: int,
    start_date: str = "",
    end_date: str = "",
    goal: str = "",
) -> str:
    """Create a new sprint on an Agile board.

    Args:
        name: Sprint name
        board_id: Board ID to create sprint in
        start_date: Start date in ISO-8601 format (optional)
        end_date: End date in ISO-8601 format (optional)
        goal: Sprint goal (optional)
    """
    c = get_client()
    payload: dict = {"name": name, "originBoardId": board_id}
    if start_date:
        payload["startDate"] = start_date
    if end_date:
        payload["endDate"] = end_date
    if goal:
        payload["goal"] = goal

    try:
        result = c.post("/rest/agile/1.0/sprint", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Created sprint: {result.get('name')} (ID: {result.get('id')})"


@mcp.tool()
def start_sprint(sprint_id: int) -> str:
    """Start a sprint (change state from future to active).

    Args:
        sprint_id: Sprint ID to start
    """
    c = get_client()
    try:
        c.post(f"/rest/agile/1.0/sprint/{sprint_id}", {"state": "active"})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Started sprint {sprint_id}"


@mcp.tool()
def complete_sprint(sprint_id: int) -> str:
    """Complete/close a sprint.

    Args:
        sprint_id: Sprint ID to complete
    """
    c = get_client()
    try:
        c.post(f"/rest/agile/1.0/sprint/{sprint_id}", {"state": "closed"})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Completed sprint {sprint_id}"


@mcp.tool()
def get_velocity(board_id: int) -> str:
    """Get velocity (issue count) for the last 5 closed sprints on a board.

    Args:
        board_id: Agile board ID
    """
    c = get_client()
    try:
        data = c.get(f"/rest/agile/1.0/board/{board_id}/sprint?state=closed&maxResults=5")
    except JiraError as e:
        return f"ERROR: {e}"

    sprints = data.get("values", [])
    lines = [f"Velocity (last {len(sprints)} sprints, board {board_id}):\n"]
    for s in sprints:
        try:
            iss_data = c.get(f"/rest/agile/1.0/sprint/{s['id']}/issue?maxResults=0")
            total = iss_data.get("total", 0)
        except JiraError:
            total = "?"
        lines.append(f"• {s.get('name')}: {total} issues")
    return "\n".join(lines)


@mcp.tool()
def get_epic_issues(epic_key: str) -> str:
    """Get all issues belonging to an epic.

    Args:
        epic_key: Epic issue key, e.g. DEVOPS-1
    """
    c = get_client()
    try:
        data = c.get(
            f"/rest/agile/1.0/epic/{epic_key}/issue"
            "?maxResults=50&fields=summary,status,assignee,issuetype"
        )
    except JiraError as e:
        return f"ERROR: {e}"

    issues = data.get("issues", [])
    lines = [f"Issues in epic {epic_key} ({len(issues)}):\n"]
    for iss in issues:
        f = iss.get("fields", {})
        assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
        lines.append(
            f"• {iss['key']} [{(f.get('issuetype') or {}).get('name','')}|"
            f"{(f.get('status') or {}).get('name','')}] {f.get('summary','')} — {assignee}"
        )
    return "\n".join(lines)


@mcp.tool()
def move_to_epic(epic_key: str, issue_keys: list[str]) -> str:
    """Move issues into an epic.

    Args:
        epic_key: Target epic key, e.g. DEVOPS-1
        issue_keys: List of issue keys to move into the epic
    """
    c = get_client()
    try:
        c.post(f"/rest/agile/1.0/epic/{epic_key}/issue", {"issues": issue_keys})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Moved {len(issue_keys)} issues to epic {epic_key}"
