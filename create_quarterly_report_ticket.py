#!/usr/bin/env python3

import json
import requests
import sys
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from pathlib import Path

JIRA_URL = "https://technative.atlassian.net"
JIRA_USER = "wouter@technative.nl"
PROJECT_KEY = "IIMS"
TOKEN_FILE = Path(__file__).parent / "token.jira"


def load_token():
    return TOKEN_FILE.read_text().strip()


def get_previous_quarter():
    now = datetime.now()
    current_q = (now.month - 1) // 3 + 1
    if current_q == 1:
        return 4, now.year - 1
    return current_q - 1, now.year


def create_ticket(token):
    quarter, year = get_previous_quarter()
    due_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
    summary = f"aws-permission-matrix report Q{quarter} {year}"

    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Voor het afgelopen kwartaal (Q{quarter} {year}) dient opnieuw een "
                            "aws-permission-matrix rapport te worden aangemaakt."
                        ),
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Voer het volgende commando uit vanuit repo xyz:",
                    }
                ],
            },
            {
                "type": "codeBlock",
                "attrs": {"language": "bash"},
                "content": [
                    {
                        "type": "text",
                        "text": "./run-compliance-check.sh aws-permission-matrix iit",
                    }
                ],
            },
        ],
    }

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
            "duedate": due_date,
        }
    }

    auth = HTTPBasicAuth(JIRA_USER, token)
    headers = {"Content-Type": "application/json"}

    response = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        auth=auth,
        headers=headers,
        json=payload,
    )

    if response.status_code == 201:
        issue = response.json()
        print(f"Ticket aangemaakt: {issue['key']}")
        print(f"URL: {JIRA_URL}/browse/{issue['key']}")
    else:
        print(f"Fout bij aanmaken ticket: {response.status_code}")
        print(response.text)
        sys.exit(1)


if __name__ == "__main__":
    token = load_token()
    create_ticket(token)
