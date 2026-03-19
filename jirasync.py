#!/usr/bin/env python3
import requests
import os
import sys
import argparse
import json
from requests.auth import HTTPBasicAuth

# === CONFIG FORMAT DETECTION AND CONVERSION ===
def detect_config_format(config):
    """Detect if config uses new format (source_/target_ prefixes) or old format"""
    return "source_jira_url" in config

def construct_jira_url(org_name):
    """Construct full Jira URL from organization name"""
    return f"https://{org_name}.atlassian.net"

def print_deprecation_warning():
    """Print deprecation warning for old config format"""
    print("⚠️  DEPRECATION WARNING: Old configuration format detected.", file=sys.stderr)
    print("   Please migrate to new format with source_*/target_* prefixes.", file=sys.stderr)
    print("   See config.example.json for reference. Old format will be removed in v2.0.0.", file=sys.stderr)
    print("", file=sys.stderr)

def convert_old_to_new_format(config):
    """Convert old format config to new format"""
    new_config = {}

    # Convert organization names to full URLs
    if "remote_org" in config:
        new_config["source_jira_url"] = construct_jira_url(config["remote_org"])

    if "local_org" in config:
        new_config["target_jira_url"] = construct_jira_url(config["local_org"])

    # Map credentials
    if "email" in config:
        new_config["target_jira_user"] = config["email"]

    if "api_token" in config:
        new_config["target_jira_token"] = config["api_token"]

    # Map project key to both source and target
    if "project_key" in config:
        new_config["source_project_key"] = config["project_key"]
        new_config["target_project_key"] = config["project_key"]

    # Board IDs default to None for old format
    new_config["source_board_id"] = None
    new_config["target_board_id"] = None

    # Preserve status_mapping
    if "status_mapping" in config:
        new_config["status_mapping"] = config["status_mapping"]

    return new_config

# === CONFIG LOADING ===
def load_config(config_file=None):
    """Load configuration from file, environment variables, or prompt user"""
    config = {}

    # Try to load from config file first
    if config_file:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"✅ Loaded configuration from {config_file}")
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            sys.exit(1)

    # Detect config format and convert if needed
    is_new_format = detect_config_format(config)

    if not is_new_format:
        # Old format detected - show deprecation warning and convert
        print_deprecation_warning()

        # Get credentials for old format (from config, env, or prompt)
        email = config.get("email") or os.environ.get("JIRA_EMAIL")
        if not email:
            print("Warning: JIRA_EMAIL not found in config or environment.")
            print("Please set it with: export JIRA_EMAIL='your-email'")
            print("Or enter your email now (input will be visible):")
            email = input()
            if not email:
                print("Error: Email is required")
                sys.exit(1)
        config["email"] = email

        api_token = config.get("api_token") or os.environ.get("JIRA_***REMOVED***_TOKEN")
        if not api_token:
            print("Warning: JIRA_***REMOVED***_TOKEN not found in config or environment.")
            print("Please set it with: export JIRA_***REMOVED***_TOKEN='your-token'")
            print("Or enter your ***REMOVED*** token now (input will be hidden):")
            import getpass
            api_token = getpass.getpass()
            if not api_token:
                print("Error: ***REMOVED*** token is required")
                sys.exit(1)
        config["api_token"] = api_token

        # Convert old format to new format
        config = convert_old_to_new_format(config)
    else:
        # New format - get credentials from config or env
        target_jira_user = config.get("target_jira_user") or os.environ.get("JIRA_EMAIL")
        if not target_jira_user:
            print("Warning: target_jira_user not found in config or environment.")
            print("Please set it with: export JIRA_EMAIL='your-email'")
            print("Or enter your email now (input will be visible):")
            target_jira_user = input()
            if not target_jira_user:
                print("Error: target_jira_user is required")
                sys.exit(1)
        config["target_jira_user"] = target_jira_user

        target_jira_token = config.get("target_jira_token") or os.environ.get("JIRA_***REMOVED***_TOKEN")
        if not target_jira_token:
            print("Warning: target_jira_token not found in config or environment.")
            print("Please set it with: export JIRA_***REMOVED***_TOKEN='your-token'")
            print("Or enter your ***REMOVED*** token now (input will be hidden):")
            import getpass
            target_jira_token = getpass.getpass()
            if not target_jira_token:
                print("Error: target_jira_token is required")
                sys.exit(1)
        config["target_jira_token"] = target_jira_token

    # Ensure status_mapping exists
    if "status_mapping" not in config:
        config["status_mapping"] = {}

    return config

# === STAP 1: Haal issues op uit themorg ===
def get_remote_issues(config, auth, headers, days=360):
    issues = []
    start_at = 0

    source_url = config['source_jira_url']
    source_project = config['source_project_key']

    while True:

        # Get the total of issues
        total_url = f"{source_url}/rest/api/3/search/approximate-count"
        payload = json.dumps({"jql": f"project={source_project}"})
        response_total = requests.request("POST", total_url, data=payload, headers=headers, auth=auth)
        data_total = response_total.json()
        total = data_total["count"]

        url = f"{source_url}/rest/api/3/search/jql"
        # Use the days parameter for the time constraint
        query = f"project={source_project} AND created >= -{days}d ORDER BY created DESC"
        params = {
            "jql": query,
            "maxResults": total,
            "fields": "*all"
        }
        try:
            response = requests.get(url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()

            if "issues" not in data:
                print(f"Warning: No 'issues' found in response: {data}")
                break
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issues from {source_url}: {e}")
            sys.exit(1)

        # Convert the JQL search results to the format expected by the rest of the code
        for result in data["issues"]:
            issue = {
                "key": result["key"],
                "fields": {
                    "summary": result["fields"]["summary"],
                    "description": result["fields"].get("description", ""),
                    "status": {
                        "name": result["fields"]["status"]["name"]
                    }
                }
            }
            issues.append(issue)

        if start_at + total >= total:
            break
        start_at += total

        # The JQL search endpoint might have different pagination behavior
        if len(data.get("results", [])) < total:
            break

    return issues


# === STAP 2: Synchroniseer issues naar lokaal project ===
def sync_issues_to_local(config, auth, headers, issues):
    target_url = config['target_jira_url']
    target_project = config['target_project_key']

    for issue in issues:
        remote_key = issue["key"]
        summary = issue["fields"]["summary"]
        description = issue["fields"].get("description", "")
        remote_status = issue["fields"]["status"]["name"]

        # Zoek lokaal issue op basis van [remote_key] in summary
        search_url = f"{target_url}/rest/api/3/search/jql"
        jql = f'project = {target_project} AND summary ~ "\\"[{remote_key}]\\""'
        try:
            response = requests.get(search_url, headers=headers, params={"jql": jql, "fields": "*all"}, auth=auth)
            response.raise_for_status()
            results = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching for issue in {target_url}: {e}")
            continue

        if results["issues"]:
            local_issue = results["issues"][0]
            local_key = local_issue["key"]
            print(f"🔄 Bijwerken: {local_key} (voor {remote_key})")

            # Description bijwerken
            update_url = f"{target_url}/rest/api/3/issue/{local_key}"
            update_payload = {"fields": {"description": description}}
            try:
                update_response = requests.put(update_url, headers=headers, auth=auth, json=update_payload)
                update_response.raise_for_status()
                print(f"✅ Description updated for {local_key}")
            except requests.exceptions.RequestException as e:
                print(f"Error updating description for {local_key}: {e}")

            # Status synchroniseren
            local_status = local_issue["fields"]["status"]["name"]
            desired_status = config['status_mapping'].get(remote_status)
            if desired_status and local_status != desired_status:
                sync_status(config, auth, headers, local_key, desired_status)
        else:
            # Issue bestaat nog niet, dus aanmaken
            print(f"➕ Aanmaken: nieuw issue voor {remote_key}")
            create_url = f"{target_url}/rest/api/3/issue"
            payload = {
                "fields": {
                    "project": {"key": target_project},
                    "summary": f"[{remote_key}] {summary}",
                    "description": description,
                    "issuetype": {"name": "Task"}
                }
            }
            try:
                response = requests.post(create_url, headers=headers, auth=auth, json=payload)
                response.raise_for_status()
                print(f"✅ Aangemaakt: {response.json()['key']}")
            except requests.exceptions.RequestException as e:
                print(f"Error creating issue for {remote_key}: {e}")


# === STAP 3: Status overzetten via transition ===
def sync_status(config, auth, headers, issue_key, target_status_name):
    target_url = config['target_jira_url']
    try:
        trans_url = f"{target_url}/rest/api/3/issue/{issue_key}/transitions"
        response = requests.get(trans_url, headers=headers, auth=auth)
        response.raise_for_status()
        transitions = response.json()["transitions"]

        matching = [t for t in transitions if t["to"]["name"].lower() == target_status_name.lower()]
        if not matching:
            print(f"⚠️ Geen overgang beschikbaar naar '{target_status_name}' voor {issue_key}")
            return

        transition_id = matching[0]["id"]
        transition_payload = {"transition": {"id": transition_id}}
        apply_url = f"{target_url}/rest/api/3/issue/{issue_key}/transitions"
        post_response = requests.post(apply_url, headers=headers, auth=auth, json=transition_payload)
        if post_response.status_code == 204:
            print(f"✅ Status gesynchroniseerd naar '{target_status_name}' voor {issue_key}")
        else:
            print(f"❌ Status-sync fout: {post_response.status_code} {post_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error synchronizing status for {issue_key}: {e}")
    except KeyError as e:
        print(f"❌ Missing data in response when synchronizing status for {issue_key}: {e}")


# === VALIDATE CONNECTION ===
def validate_connections(config, auth, headers):
    """Validate connections to both Jira instances before starting sync"""
    source_url = config['source_jira_url']
    target_url = config['target_jira_url']

    print(f"🔍 Validating connection to {source_url}...")
    try:
        url = f"{source_url}/rest/api/3/myself"
        response = requests.get(url, headers=headers, auth=auth)
        print(response)
        response.raise_for_status()
        remote_user = response.json().get("displayName", "Unknown")
        print(f"✅ Connected to {source_url} as {remote_user}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to {source_url}: {e}")
        return False

    print(f"🔍 Validating connection to {target_url}...")
    try:
        url = f"{target_url}/rest/api/3/myself"
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        local_user = response.json().get("displayName", "Unknown")
        print(f"✅ Connected to {target_url} as {local_user}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to {target_url}: {e}")
        return False

    return True


# === MAIN ===
if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Synchronize Jira issues between organizations')
        parser.add_argument('--config', type=str, default=None,
                            help='Path to JSON configuration file')
        parser.add_argument('--days', type=int, default=90,
                            help='Number of days to look back for issues (default: 90)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Only show what would be done, without making changes')
        args = parser.parse_args()

        # Load configuration
        config = load_config(args.config)

        # Set up authentication and headers
        auth = HTTPBasicAuth(config['target_jira_user'], config['target_jira_token'])
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        print(f"🔄 Starting synchronization from {config['source_jira_url']} to {config['target_jira_url']}...")
        print(f"📅 Looking back {args.days} days for issues")

        if args.dry_run:
            print("🔍 DRY RUN MODE: No changes will be made")

        if not validate_connections(config, auth, headers):
            print("❌ Connection validation failed. Exiting.")
            sys.exit(1)

        remote_issues = get_remote_issues(config, auth, headers, days=args.days)
        print(f"🔎 Gevonden {len(remote_issues)} issues in {config['source_jira_url']}")

        if not args.dry_run:
            sync_issues_to_local(config, auth, headers, remote_issues)
            print("✅ Synchronization completed successfully")
        else:
            print("✅ Dry run completed successfully")
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

