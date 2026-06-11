from __future__ import annotations

import os
import pathlib

JIRA_URL: str = os.environ.get("JIRA_URL", "")
JIRA_PAT: str = os.environ.get("JIRA_PAT", "")
JIRA_USER: str = os.environ.get("JIRA_USER", "")
VERIFY_SSL: bool = os.environ.get("JIRA_VERIFY_SSL", "true").lower() == "true"
TRUST_ENV: bool = os.environ.get("JIRA_TRUST_ENV", "false").lower() == "true"

PROJECT_ROOT: pathlib.Path = pathlib.Path(__file__).parent.parent
