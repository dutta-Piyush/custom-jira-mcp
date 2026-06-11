"""Jira project tools: list/get projects, components, versions, roles."""

from __future__ import annotations

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def list_projects() -> str:
    """List all Jira projects accessible with your credentials."""
    c = get_client()
    try:
        projects = c.get("/rest/api/2/project?expand=description,lead")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Projects ({len(projects)}):\n"]
    for p in projects:
        lead = (p.get("lead") or {}).get("displayName", "")
        lines.append(f"• {p.get('key')} — {p.get('name')} [{p.get('projectTypeKey','')}] (Lead: {lead})")
    return "\n".join(lines)


@mcp.tool()
def get_project(project_key: str) -> str:
    """Get details of a Jira project including components, versions and issue types.

    Args:
        project_key: Jira project key, e.g. DEVOPS
    """
    c = get_client()
    try:
        p = c.get(f"/rest/api/2/project/{project_key}?expand=description,issueTypes,components,versions")
    except JiraError as e:
        return f"ERROR: {e}"

    lead = (p.get("lead") or {}).get("displayName", "")
    issue_types = [it.get("name", "") for it in (p.get("issueTypes") or [])]
    lines = [
        f"Project: {p.get('key')} — {p.get('name')}",
        f"Lead: {lead}",
    ]
    if p.get("description"):
        lines.append(f"Description: {p['description'][:300]}")
    lines.append(f"\nIssue Types: {', '.join(issue_types)}")

    components = p.get("components") or []
    if components:
        lines.append(f"\nComponents ({len(components)}):")
        for comp in components:
            clead = (comp.get("lead") or {}).get("displayName", "")
            lines.append(f"  • {comp.get('name')} (Lead: {clead})")

    versions = p.get("versions") or []
    if versions:
        lines.append(f"\nVersions ({len(versions)}):")
        for v in versions:
            status = "released" if v.get("released") else "unreleased"
            lines.append(f"  • {v.get('name')} [{status}]")

    return "\n".join(lines)


@mcp.tool()
def get_project_roles(project_key: str) -> str:
    """List roles defined in a Jira project.

    Args:
        project_key: Jira project key, e.g. DEVOPS
    """
    c = get_client()
    try:
        roles = c.get(f"/rest/api/2/project/{project_key}/role")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Project Roles for {project_key}:\n"]
    for name in roles:
        lines.append(f"• {name}")
    return "\n".join(lines)


@mcp.tool()
def list_components(project_key: str) -> str:
    """List components in a Jira project.

    Args:
        project_key: Jira project key, e.g. DEVOPS
    """
    c = get_client()
    try:
        comps = c.get(f"/rest/api/2/project/{project_key}/components")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Components for {project_key} ({len(comps)}):\n"]
    for comp in comps:
        lead = (comp.get("lead") or {}).get("displayName", "no lead")
        lines.append(f"• {comp.get('name')} [ID: {comp.get('id','')}] (Lead: {lead})")
    return "\n".join(lines)


@mcp.tool()
def create_component(
    project_key: str,
    name: str,
    lead: str = "",
    description: str = "",
) -> str:
    """Create a new component in a Jira project.

    Args:
        project_key: Jira project key, e.g. DEVOPS
        name: Component name
        lead: Lead username (optional)
        description: Component description (optional)
    """
    c = get_client()
    payload: dict = {"name": name, "project": project_key}
    if lead:
        payload["leadUserName"] = lead
    if description:
        payload["description"] = description

    try:
        result = c.post("/rest/api/2/component", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Created component: {result.get('name')} (ID: {result.get('id')})"


@mcp.tool()
def list_versions(project_key: str) -> str:
    """List fix versions in a Jira project.

    Args:
        project_key: Jira project key, e.g. DEVOPS
    """
    c = get_client()
    try:
        versions = c.get(f"/rest/api/2/project/{project_key}/versions")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"Versions for {project_key} ({len(versions)}):\n"]
    for v in versions:
        status = "released" if v.get("released") else "unreleased"
        lines.append(f"• {v.get('name')} [ID: {v.get('id','')}] {status} (date: {v.get('releaseDate','')})")
    return "\n".join(lines)


@mcp.tool()
def create_version(
    project_key: str,
    name: str,
    description: str = "",
    release_date: str = "",
) -> str:
    """Create a new fix version in a Jira project.

    Args:
        project_key: Jira project key, e.g. DEVOPS
        name: Version name, e.g. v1.2.0
        description: Version description (optional)
        release_date: Release date in YYYY-MM-DD format (optional)
    """
    c = get_client()
    payload: dict = {"name": name, "project": project_key}
    if description:
        payload["description"] = description
    if release_date:
        payload["releaseDate"] = release_date

    try:
        result = c.post("/rest/api/2/version", payload)
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Created version: {result.get('name')} (ID: {result.get('id')})"


@mcp.tool()
def release_version(version_id: str) -> str:
    """Mark a Jira fix version as released.

    Args:
        version_id: Version ID (get from list_versions)
    """
    c = get_client()
    try:
        c.put(f"/rest/api/2/version/{version_id}", {"released": True})
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Released version ID: {version_id}"
