"""Jira issue write/mutation tools: create, update, transition, link, bulk ops."""

from __future__ import annotations

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def create_issue(
    project_key: str,
    summary: str,
    issue_type: str,
    description: str = "",
    assignee: str = "",
    priority: str = "",
    labels: list[str] | None = None,
    components: list[str] | None = None,
    fix_version: str = "",
    parent: str = "",
    custom_fields: dict[str, str] | None = None,
) -> str:
    """Create a new Jira issue.

    Args:
        project_key: Project key, e.g. DEVOPS
        summary: Issue summary/title
        issue_type: Bug, Story, Task, Epic, Sub-task
        description: Issue description
        assignee: Assignee username
        priority: Highest, High, Medium, Low, Lowest
        labels: Labels to apply
        components: Component names
        fix_version: Fix version name
        parent: Parent Epic key to link Story/Task under (e.g. DEVOPS-1)
        custom_fields: Custom fields as key-value pairs, e.g. {'customfield_11803': '2025-01-01'}
    """
    c = get_client()
    fields: dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    if description:
        fields["description"] = description
    if assignee:
        fields["assignee"] = {"name": assignee}
    if priority:
        fields["priority"] = {"name": priority}
    if labels:
        fields["labels"] = labels
    if components:
        fields["components"] = [{"name": n} for n in components]
    if fix_version:
        fields["fixVersions"] = [{"name": fix_version}]
    if parent:
        if issue_type.lower() == "sub-task":
            fields["parent"] = {"key": parent}
        else:
            fields["customfield_11802"] = parent
    if issue_type.lower() == "epic":
        fields["customfield_10003"] = summary
    if custom_fields:
        fields.update(custom_fields)

    try:
        result = c.post("/rest/api/2/issue", {"fields": fields})
    except JiraError as e:
        return f"ERROR: {e}"

    key = result.get("key", "")
    return f"Created: {key}\nURL: {c.base_url}/browse/{key}"


@mcp.tool()
def update_issue(
    issue_key: str,
    summary: str = "",
    description: str = "",
    assignee: str = "",
    priority: str = "",
    labels: list[str] | None = None,
    components: list[str] | None = None,
    fix_version: str = "",
) -> str:
    """Update fields on an existing Jira issue.

    Args:
        issue_key: Issue key to update
        summary: New summary
        description: New description
        assignee: New assignee username
        priority: New priority name
        labels: Replace all labels with these
        components: Replace all components with these
        fix_version: Fix version name
    """
    c = get_client()
    fields: dict = {}
    if summary:
        fields["summary"] = summary
    if description:
        fields["description"] = description
    if assignee:
        fields["assignee"] = {"name": assignee}
    if priority:
        fields["priority"] = {"name": priority}
    if labels is not None:
        fields["labels"] = labels
    if components is not None:
        fields["components"] = [{"name": n} for n in components]
    if fix_version:
        fields["fixVersions"] = [{"name": fix_version}]

    try:
        c.put(f"/rest/api/2/issue/{issue_key}", {"fields": fields})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Updated: {issue_key}"


@mcp.tool()
def assign_issue(issue_key: str, assignee: str) -> str:
    """Assign a Jira issue to a user.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        assignee: Username to assign to
    """
    c = get_client()
    try:
        c.put(f"/rest/api/2/issue/{issue_key}/assignee", {"name": assignee})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Assigned {issue_key} to {assignee}"


@mcp.tool()
def transition_issue(
    issue_key: str,
    transition_id: str,
    comment: str = "",
    resolution: str = "",
) -> str:
    """Transition a Jira issue to a new workflow status.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        transition_id: Transition ID (get from get_transitions)
        comment: Optional comment to add with transition
        resolution: Resolution name if required (Done, Won't Do, Duplicate)
    """
    c = get_client()
    payload: dict = {"transition": {"id": transition_id}}
    if comment:
        payload["update"] = {"comment": [{"add": {"body": comment}}]}
    if resolution:
        payload["fields"] = {"resolution": {"name": resolution}}

    try:
        c.post(f"/rest/api/2/issue/{issue_key}/transitions", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Transitioned {issue_key} (transition ID: {transition_id})"


@mcp.tool()
def add_labels(issue_key: str, labels: list[str]) -> str:
    """Add labels to a Jira issue (does not remove existing labels).

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        labels: List of labels to add
    """
    c = get_client()
    try:
        c.put(
            f"/rest/api/2/issue/{issue_key}",
            {"update": {"labels": [{"add": lbl} for lbl in labels]}},
        )
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Added labels {labels} to {issue_key}"


@mcp.tool()
def bulk_transition(issue_keys: list[str], transition_id: str) -> str:
    """Transition multiple Jira issues to a new status.

    Args:
        issue_keys: List of issue keys to transition
        transition_id: Transition ID to apply to all issues
    """
    c = get_client()
    lines = []
    success = 0
    for key in issue_keys:
        try:
            c.post(f"/rest/api/2/issue/{key}/transitions", {"transition": {"id": transition_id}})
            lines.append(f"✓ {key} transitioned")
            success += 1
        except JiraError as e:
            lines.append(f"✗ {key}: {e}")
    lines.append(f"\nResult: {success}/{len(issue_keys)} succeeded")
    return "\n".join(lines)


@mcp.tool()
def bulk_assign(issue_keys: list[str], assignee: str) -> str:
    """Assign multiple Jira issues to the same user.

    Args:
        issue_keys: List of issue keys to assign
        assignee: Username to assign all issues to
    """
    c = get_client()
    lines = []
    success = 0
    for key in issue_keys:
        try:
            c.put(f"/rest/api/2/issue/{key}/assignee", {"name": assignee})
            lines.append(f"✓ {key} → {assignee}")
            success += 1
        except JiraError as e:
            lines.append(f"✗ {key}: {e}")
    lines.append(f"\nResult: {success}/{len(issue_keys)} assigned to {assignee}")
    return "\n".join(lines)


@mcp.tool()
def link_issues(inward_key: str, outward_key: str, link_type: str) -> str:
    """Create a link between two Jira issues.

    Args:
        inward_key: Source issue key, e.g. DEVOPS-1
        outward_key: Target issue key, e.g. DEVOPS-2
        link_type: Link type name, e.g. Blocks, Clones, Relates (use get_link_types to see options)
    """
    c = get_client()
    try:
        c.post("/rest/api/2/issueLink", {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        })
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Linked {inward_key} → {outward_key} ({link_type})"


@mcp.tool()
def add_remote_link(issue_key: str, url: str, title: str) -> str:
    """Add a remote web link to a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
        url: URL to link
        title: Link title/label
    """
    c = get_client()
    try:
        c.post(f"/rest/api/2/issue/{issue_key}/remotelink", {"object": {"url": url, "title": title}})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Added remote link to {issue_key}: {url}"


@mcp.tool()
def rank_issues(
    issue_keys: list[str],
    rank_before: str = "",
    rank_after: str = "",
) -> str:
    """Reorder issues on the Agile board by ranking them before/after another issue.

    Args:
        issue_keys: Issue keys to rank
        rank_before: Place these issues before this issue key (optional)
        rank_after: Place these issues after this issue key (optional)
    """
    c = get_client()
    payload: dict = {"issues": issue_keys}
    if rank_before:
        payload["rankBeforeIssue"] = rank_before
    if rank_after:
        payload["rankAfterIssue"] = rank_after
    try:
        c.put("/rest/agile/1.0/issue/rank", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Ranked {len(issue_keys)} issues"
