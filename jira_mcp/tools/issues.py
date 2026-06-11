"""Jira issue read tools: search, get, inspect."""

from __future__ import annotations

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL.

    Args:
        jql: JQL query string, e.g. 'project = DEVOPS AND status = Open'
        max_results: Maximum number of results (default 20, max 50)
    """
    max_results = min(max(1, max_results), 50)
    c = get_client()
    try:
        data = c.post("/rest/api/2/search", {
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "status", "assignee", "priority", "issuetype",
                       "created", "updated", "labels"],
        })
    except JiraError as e:
        return f"ERROR: {e}"

    issues = data.get("issues", [])
    total = data.get("total", 0)
    lines = [f"Results: {total} total (showing {len(issues)})\n"]
    for iss in issues:
        f = iss.get("fields", {})
        assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
        labels = f.get("labels", [])
        lines.append(
            f"• {iss['key']} [{(f.get('status') or {}).get('name','')}] "
            f"{f.get('summary','')}\n"
            f"  Type: {(f.get('issuetype') or {}).get('name','')} | "
            f"Priority: {(f.get('priority') or {}).get('name','')} | "
            f"Assignee: {assignee}"
        )
        if labels:
            lines.append(f"  Labels: {', '.join(labels)}")
    return "\n".join(lines)


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Get full details of a Jira issue including comments, links and attachments.

    Args:
        issue_key: Jira issue key, e.g. DEVOPS-123
    """
    c = get_client()
    fields = (
        "summary,status,assignee,reporter,priority,issuetype,description,"
        "created,updated,labels,components,fixVersions,resolution,subtasks,"
        "issuelinks,comment,worklog,attachment,timetracking"
    )
    try:
        iss = c.get(f"/rest/api/2/issue/{issue_key}?fields={fields}")
    except JiraError as e:
        return f"ERROR: {e}"

    f = iss.get("fields", {})
    assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
    reporter = (f.get("reporter") or {}).get("displayName", "Unknown")
    resolution = (f.get("resolution") or {}).get("name")
    labels = f.get("labels", [])
    components = [c2.get("name", "") for c2 in (f.get("components") or [])]
    fix_versions = [v.get("name", "") for v in (f.get("fixVersions") or [])]
    tt = f.get("timetracking") or {}
    created = (f.get("created") or "")[:10]
    updated = (f.get("updated") or "")[:10]

    lines = [
        f"=== {iss['key']} ===",
        f"Summary: {f.get('summary','')}",
        f"Type: {(f.get('issuetype') or {}).get('name','')} | "
        f"Status: {(f.get('status') or {}).get('name','')} | "
        f"Priority: {(f.get('priority') or {}).get('name','')}",
    ]
    if resolution:
        lines.append(f"Resolution: {resolution}")
    lines.append(f"Assignee: {assignee} | Reporter: {reporter}")
    if created:
        lines.append(f"Created: {created} | Updated: {updated}")
    if labels:
        lines.append(f"Labels: {', '.join(labels)}")
    if components:
        lines.append(f"Components: {', '.join(components)}")
    if fix_versions:
        lines.append(f"Fix Versions: {', '.join(fix_versions)}")
    if tt.get("originalEstimate"):
        lines.append(
            f"Time: Original={tt.get('originalEstimate')} | "
            f"Remaining={tt.get('remainingEstimate')} | "
            f"Spent={tt.get('timeSpent')}"
        )
    desc = f.get("description") or ""
    if desc:
        lines.append(f"\n-- Description --\n{desc[:2000]}")

    subtasks = f.get("subtasks") or []
    if subtasks:
        lines.append(f"\n-- Subtasks ({len(subtasks)}) --")
        for st in subtasks:
            sf = st.get("fields", {})
            lines.append(f"  * {st['key']} [{(sf.get('status') or {}).get('name','')}] {sf.get('summary','')}")

    links = f.get("issuelinks") or []
    if links:
        lines.append(f"\n-- Links ({len(links)}) --")
        for lnk in links:
            ltype = (lnk.get("type") or {}).get("name", "")
            if lnk.get("outwardIssue"):
                oi = lnk["outwardIssue"]
                lines.append(f"  * {ltype} -> {oi['key']} [{(oi.get('fields',{}).get('status') or {}).get('name','')}] {oi.get('fields',{}).get('summary','')}")
            if lnk.get("inwardIssue"):
                ii = lnk["inwardIssue"]
                lines.append(f"  * {ltype} <- {ii['key']} [{(ii.get('fields',{}).get('status') or {}).get('name','')}] {ii.get('fields',{}).get('summary','')}")

    attachments = f.get("attachment") or []
    if attachments:
        lines.append(f"\n-- Attachments ({len(attachments)}) --")
        for a in attachments:
            date = (a.get("created") or "")[:10]
            lines.append(f"  * {a.get('filename')} ({a.get('size',0)//1024} KB) by {(a.get('author') or {}).get('displayName','')} on {date}")

    comments = (f.get("comment") or {}).get("comments") or []
    if comments:
        lines.append(f"\n-- Comments ({len(comments)}) --")
        for cm in comments[:10]:
            date = (cm.get("created") or "")[:10]
            author = (cm.get("author") or {}).get("displayName", "")
            body = (cm.get("body") or "")[:300]
            lines.append(f"  [{date}] {author}:\n    {body}\n")

    return "\n".join(lines)


@mcp.tool()
def get_transitions(issue_key: str) -> str:
    """Get available workflow transitions for a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/api/2/issue/{issue_key}/transitions")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Available transitions for {issue_key}:\n"]
    for t in data.get("transitions", []):
        lines.append(f"* ID: {t['id']} -- \"{t['name']}\" -> {(t.get('to') or {}).get('name','')}")
    return "\n".join(lines)


@mcp.tool()
def get_link_types() -> str:
    """List all available issue link types in Jira."""
    c = get_client()
    try:
        data = c.get("/rest/api/2/issueLinkType")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = ["Link Types:\n"]
    for lt in data.get("issueLinkTypes", []):
        lines.append(f"* {lt['name']} (inward: \"{lt.get('inward','')}\" | outward: \"{lt.get('outward','')}\")")
    return "\n".join(lines)


@mcp.tool()
def get_remote_links(issue_key: str) -> str:
    """List remote web links attached to a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/api/2/issue/{issue_key}/remotelink")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Remote Links on {issue_key} ({len(data)}):\n"]
    for lnk in data:
        obj = lnk.get("object", {})
        lines.append(f"* {obj.get('title','')}\n  {obj.get('url','')}\n")
    return "\n".join(lines)


@mcp.tool()
def list_attachments(issue_key: str) -> str:
    """List attachments on a Jira issue.

    Args:
        issue_key: Issue key, e.g. DEVOPS-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/api/2/issue/{issue_key}?fields=attachment")
    except JiraError as e:
        return f"ERROR: {e}"

    attachments = (data.get("fields") or {}).get("attachment") or []
    lines = [f"Attachments on {issue_key} ({len(attachments)}):\n"]
    for a in attachments:
        date = (a.get("created") or "")[:10]
        author = (a.get("author") or {}).get("displayName", "")
        lines.append(
            f"* {a.get('filename')} ({a.get('size',0)//1024} KB) by {author} on {date}\n"
            f"  URL: {a.get('content','')}"
        )
    return "\n".join(lines)
