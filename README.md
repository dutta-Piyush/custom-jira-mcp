# Jira MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes **50 Jira tools** to GitHub Copilot and other MCP-compatible AI agents. Written in Python using [FastMCP](https://github.com/jlowin/fastmcp).

**Security:** No destructive operations. The HTTP DELETE method is not implemented — no tool can permanently delete issues, comments, or any data. `raw_api_call` is restricted to GET/POST/PUT only.

## Features

- **Issues**: search, get, create, update, assign, transition, link, bulk operations
- **Projects**: list, get details, roles, components, versions
- **Agile**: boards, sprints, backlog, velocity, epics
- **Comments & time**: add comments, watchers, worklog
- **Users & filters**: search users, saved filters
- **Service Management (JSM)**: service desks, request types, approvals, SLA, queues
- **Admin / meta**: issue types, priorities, statuses, fields, raw API call

## Requirements

- Python 3.11+
- A Jira Personal Access Token (PAT)

## Setup

```powershell
# 1. Clone and enter the directory
cd devopsjira-mcp-master

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

Set the following environment variables before starting the server:

| Variable          | Required | Default | Description                                                             |
| ----------------- | -------- | ------- | ----------------------------------------------------------------------- |
| `JIRA_URL`        | ✅       | —       | Base URL of your Jira instance, e.g. `https://your-jira.company.com`    |
| `JIRA_PAT`        | ✅       | —       | Personal Access Token                                                   |
| `JIRA_VERIFY_SSL` | ❌       | `true`  | Set to `false` only if your Jira uses a self-signed/internal cert       |
| `JIRA_TRUST_ENV`  | ❌       | `false` | Set to `true` to route traffic through your system proxy (e.g. Zscaler) |
| `PORT`            | ❌       | —       | Set to an integer (e.g. `8080`) to run in HTTP mode instead of stdio    |

> **Security note:** `JIRA_VERIFY_SSL` defaults to `true`. Only set it to `false` if you are connecting to an internal Jira with a self-signed certificate and you understand the risk.

## VS Code / GitHub Copilot Integration

Add the following to your `.vscode/mcp.json` (or user-level `mcp.json`):

```json
{
  "servers": {
    "jira-mcp": {
      "type": "stdio",
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\devopsjira-mcp-master\\server.py"],
      "env": {
        "JIRA_URL": "https://your-jira.company.com",
        "JIRA_PAT": "your-personal-access-token"
      }
    }
  }
}
```

## Running manually

```powershell
$env:JIRA_URL = "https://your-jira.company.com"
$env:JIRA_PAT = "your-pat"
python server.py
```

## HTTP mode

Set the `PORT` environment variable to start an HTTP server instead of stdio:

```powershell
$env:PORT = "8080"
python server.py
```

## Tool reference

### Issues

| Tool               | Description                  |
| ------------------ | ---------------------------- |
| `search_issues`    | Search with JQL              |
| `get_issue`        | Get full issue details       |
| `create_issue`     | Create a new issue           |
| `update_issue`     | Update issue fields          |
| `assign_issue`     | Assign to a user             |
| `get_transitions`  | List available transitions   |
| `transition_issue` | Move to new status           |
| `add_labels`       | Add labels (non-destructive) |
| `bulk_transition`  | Transition multiple issues   |
| `bulk_assign`      | Assign multiple issues       |
| `link_issues`      | Create issue link            |
| `get_link_types`   | List link type names         |
| `get_remote_links` | List web links               |
| `add_remote_link`  | Add a web link               |
| `list_attachments` | List attachments             |
| `rank_issues`      | Reorder on board             |

### Projects

| Tool                | Description           |
| ------------------- | --------------------- |
| `list_projects`     | List all projects     |
| `get_project`       | Project details       |
| `get_project_roles` | List roles            |
| `list_components`   | List components       |
| `create_component`  | Create component      |
| `list_versions`     | List fix versions     |
| `create_version`    | Create fix version    |
| `release_version`   | Mark version released |

### Agile (Boards & Sprints)

| Tool                | Description            |
| ------------------- | ---------------------- |
| `list_boards`       | List boards            |
| `list_sprints`      | List sprints on board  |
| `get_sprint_issues` | Issues in sprint       |
| `get_board_backlog` | Backlog issues         |
| `move_to_sprint`    | Move issues to sprint  |
| `create_sprint`     | Create sprint          |
| `start_sprint`      | Start sprint           |
| `complete_sprint`   | Complete sprint        |
| `get_velocity`      | Last 5 sprint velocity |
| `get_epic_issues`   | Issues in epic         |
| `move_to_epic`      | Move issues to epic    |

### Comments, Watchers & Worklog

| Tool           | Description   |
| -------------- | ------------- |
| `get_comments` | List comments |
| `add_comment`  | Add comment   |
| `get_watchers` | List watchers |
| `add_watcher`  | Add watcher   |
| `add_worklog`  | Log time      |

### Users & Filters

| Tool             | Description       |
| ---------------- | ----------------- |
| `search_users`   | Find users        |
| `get_myself`     | Current user info |
| `get_my_filters` | Saved filters     |
| `create_filter`  | Save a new filter |

### Service Management (JSM)

| Tool                      | Description             |
| ------------------------- | ----------------------- |
| `list_service_desks`      | List service desks      |
| `list_request_types`      | Request types in desk   |
| `get_request_type_fields` | Fields for request type |
| `create_service_request`  | Submit a new request    |
| `get_service_request`     | Get request details     |
| `get_my_requests`         | My requests             |
| `search_service_requests` | Search requests         |
| `get_request_comments`    | Request comments        |
| `add_request_comment`     | Add comment to request  |
| `get_approvals`           | Approval details        |
| `approve_request`         | Approve a request       |
| `get_sla`                 | SLA status              |
| `list_queues`             | List agent queues       |
| `get_queue_issues`        | Issues in queue         |

### Admin / Meta

| Tool               | Description               |
| ------------------ | ------------------------- |
| `list_issue_types` | All issue types           |
| `list_priorities`  | All priorities            |
| `list_statuses`    | All statuses              |
| `list_fields`      | All fields (incl. custom) |
| `raw_api_call`     | Raw GET/POST/PUT          |

## License

MIT
