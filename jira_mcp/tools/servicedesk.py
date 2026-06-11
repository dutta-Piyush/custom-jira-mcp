"""Jira Service Management (JSM) / Service Desk tools."""

from __future__ import annotations

import json
from urllib.parse import quote

from jira_mcp.app import mcp
from jira_mcp.client import JiraError, get_client


@mcp.tool()
def list_service_desks() -> str:
    """List all Jira Service Management (JSM) service desks."""
    c = get_client()
    try:
        data = c.get("/rest/servicedeskapi/servicedesk")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Service Desks ({len(values)}):\n"]
    for sd in values:
        lines.append(f"• ID: {sd.get('id')} — {sd.get('projectName','')} ({sd.get('projectKey','')})")
    return "\n".join(lines)


@mcp.tool()
def list_request_types(service_desk_id: str) -> str:
    """List request types available in a service desk.

    Args:
        service_desk_id: Service desk ID (get from list_service_desks)
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Request Types ({len(values)}):\n"]
    for rt in values:
        lines.append(f"• ID: {rt.get('id')} — {rt.get('name','')}\n  {(rt.get('description') or '')[:200]}\n")
    return "\n".join(lines)


@mcp.tool()
def get_request_type_fields(service_desk_id: str, request_type_id: str) -> str:
    """Get the fields required to create a request of a specific type.

    Args:
        service_desk_id: Service desk ID
        request_type_id: Request type ID (get from list_request_types)
    """
    c = get_client()
    try:
        data = c.get(
            f"/rest/servicedeskapi/servicedesk/{service_desk_id}"
            f"/requesttype/{request_type_id}/field"
        )
    except JiraError as e:
        return f"ERROR: {e}"

    lines = ["Request Type Fields:\n"]
    for f in data.get("requestTypeFields", []):
        req = " *REQUIRED*" if f.get("required") else ""
        lines.append(f"• {f.get('name','')} ({f.get('fieldId','')}){req}")
    return "\n".join(lines)


@mcp.tool()
def create_service_request(
    service_desk_id: str,
    request_type_id: str,
    summary: str,
    description: str = "",
    extra_fields: str = "",
) -> str:
    """Create a new service request in a JSM service desk.

    Args:
        service_desk_id: Service desk ID
        request_type_id: Request type ID
        summary: Request summary/title
        description: Request description (optional)
        extra_fields: Additional field values as a JSON object string, e.g. '{"customfield_123":"value"}'
    """
    c = get_client()
    field_values: dict = {"summary": summary}
    if description:
        field_values["description"] = description
    if extra_fields:
        try:
            extra = json.loads(extra_fields)
            field_values.update(extra)
        except json.JSONDecodeError:
            return "ERROR: extra_fields must be valid JSON"

    try:
        result = c.post("/rest/servicedeskapi/request", {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": field_values,
        })
    except JiraError as e:
        return f"ERROR: {e}"

    key = result.get("issueKey", "")
    return f"Created request: {key}\nURL: {c.base_url}/browse/{key}"


@mcp.tool()
def get_service_request(issue_key: str) -> str:
    """Get details of a JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
    """
    c = get_client()
    try:
        req = c.get(f"/rest/servicedeskapi/request/{issue_key}")
    except JiraError as e:
        return f"ERROR: {e}"

    return (
        f"Request: {req.get('issueKey','')}\n"
        f"Type: {(req.get('requestType') or {}).get('name','')}\n"
        f"Status: {(req.get('currentStatus') or {}).get('status','')}\n"
        f"Reporter: {(req.get('reporter') or {}).get('displayName','')}\n"
        f"Created: {(req.get('createdDate') or {}).get('friendly','')}"
    )


@mcp.tool()
def get_my_requests() -> str:
    """List your own JSM service requests (last 20)."""
    c = get_client()
    try:
        data = c.get("/rest/servicedeskapi/request?requestOwnership=MY_REQUESTS&maxResults=20")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"My Requests ({len(values)}):\n"]
    for r in values:
        lines.append(
            f"• {r.get('issueKey','')} [{(r.get('currentStatus') or {}).get('status','')}]"
            f" — {(r.get('requestType') or {}).get('name','')}"
        )
    return "\n".join(lines)


@mcp.tool()
def search_service_requests(search_term: str = "", status: str = "") -> str:
    """Search JSM service requests by text or status.

    Args:
        search_term: Text to search for in requests (optional)
        status: Filter by status: OPEN, CLOSED, ALL_REQUESTS (optional)
    """
    c = get_client()
    path = "/rest/servicedeskapi/request?maxResults=20"
    if search_term:
        path += f"&searchTerm={quote(search_term)}"
    if status:
        path += f"&requestStatus={status}"

    try:
        data = c.get(path)
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Requests ({len(values)}):\n"]
    for r in values:
        lines.append(
            f"• {r.get('issueKey','')} [{(r.get('currentStatus') or {}).get('status','')}]"
            f" — {(r.get('requestType') or {}).get('name','')}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_request_comments(issue_key: str) -> str:
    """Get comments on a JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/request/{issue_key}/comment")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Comments on request {issue_key} ({len(values)}):\n"]
    for cm in values:
        vis = "public" if cm.get("public") else "internal"
        date = (cm.get("created") or {}).get("friendly", "")
        author = (cm.get("author") or {}).get("displayName", "")
        body = (cm.get("body") or "")[:300]
        lines.append(f"[{date}] {author} ({vis}):\n{body}\n")
    return "\n".join(lines)


@mcp.tool()
def add_request_comment(issue_key: str, body: str, public: bool = True) -> str:
    """Add a comment to a JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
        body: Comment text
        public: True for customer-visible comment, False for internal-only (default True)
    """
    c = get_client()
    try:
        c.post(f"/rest/servicedeskapi/request/{issue_key}/comment", {"body": body, "public": public})
    except JiraError as e:
        return f"ERROR: {e}"

    vis = "public" if public else "internal"
    return f"Added {vis} comment to request {issue_key}"


@mcp.tool()
def get_approvals(issue_key: str) -> str:
    """Get approval details for a JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/request/{issue_key}/approval")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Approvals for {issue_key} ({len(values)}):\n"]
    for a in values:
        lines.append(f"• {a.get('name','')} [ID: {a.get('id','')}] — {a.get('status','')}")
        for ap in a.get("approvers", []):
            approver = (ap.get("approver") or {}).get("displayName", "")
            lines.append(f"    {approver}: {ap.get('approverDecision','')}")
    return "\n".join(lines)


@mcp.tool()
def approve_request(issue_key: str, approval_id: str) -> str:
    """Approve a pending JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
        approval_id: Approval ID (get from get_approvals)
    """
    c = get_client()
    try:
        c.post(
            f"/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}",
            {"decision": "approve"},
        )
    except JiraError as e:
        return f"ERROR: {e}"
    return f"Approved: {issue_key} (approval {approval_id})"


@mcp.tool()
def get_sla(issue_key: str) -> str:
    """Get SLA information for a JSM service request.

    Args:
        issue_key: Request issue key, e.g. SD-123
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/request/{issue_key}/sla")
    except JiraError as e:
        return f"ERROR: {e}"

    lines = [f"SLA for {issue_key}:\n"]
    for sla in data.get("values", []):
        cycle = sla.get("ongoingCycle")
        if cycle:
            breached = "BREACHED" if cycle.get("breached") else "OK"
            remaining = (cycle.get("remainingTime") or {}).get("friendly", "")
            lines.append(f"• {sla.get('name','')} [{breached}] (remaining: {remaining})")
        else:
            lines.append(f"• {sla.get('name','')}: completed")
    return "\n".join(lines)


@mcp.tool()
def list_queues(service_desk_id: str) -> str:
    """List queues in a JSM service desk.

    Args:
        service_desk_id: Service desk ID (get from list_service_desks)
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/servicedesk/{service_desk_id}/queue")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Queues ({len(values)}):\n"]
    for q in values:
        lines.append(f"• {q.get('name','')} (ID: {q.get('id','')} — {q.get('issueCount',0)} issues)")
    return "\n".join(lines)


@mcp.tool()
def get_queue_issues(service_desk_id: str, queue_id: str) -> str:
    """Get issues in a JSM service desk queue.

    Args:
        service_desk_id: Service desk ID
        queue_id: Queue ID (get from list_queues)
    """
    c = get_client()
    try:
        data = c.get(f"/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}/issue")
    except JiraError as e:
        return f"ERROR: {e}"

    values = data.get("values", [])
    lines = [f"Queue issues ({len(values)}):\n"]
    for iss in values:
        f = iss.get("fields", {})
        lines.append(
            f"• {iss.get('key','')} [{(f.get('status') or {}).get('name','')}] "
            f"{f.get('summary','')}"
        )
    return "\n".join(lines)
