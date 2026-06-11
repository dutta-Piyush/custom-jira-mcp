"""Entry point for the Jira MCP server."""

import os
import sys

import jira_mcp.tools  # noqa: F401 — registers all tools via side-effects
from jira_mcp.app import mcp

if __name__ == "__main__":
    # Fail fast with clear messages if required env vars are missing
    missing = [v for v in ("JIRA_URL", "JIRA_PAT") if not os.environ.get(v)]
    if missing:
        print(
            f"ERROR: required environment variable(s) not set: {', '.join(missing)}\n"
            "Set JIRA_URL and JIRA_PAT before starting the server.",
            file=sys.stderr,
        )
        sys.exit(1)

    port = os.environ.get("PORT")
    if port:
        try:
            port_int = int(port)
        except ValueError:
            print(
                f"ERROR: PORT must be a valid integer, got: {port!r}",
                file=sys.stderr,
            )
            sys.exit(1)
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port_int)
    else:
        mcp.run(transport="stdio")
