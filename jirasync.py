#!/usr/bin/env python3
import requests
import os
import re
import sys
import json
import argparse
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from requests.auth import HTTPBasicAuth

# === STATE MANAGEMENT ===

def load_state(state_file):
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  State file corrupt ({e}), starting fresh.", file=sys.stderr)
        return None

def save_state(state_file, last_sync, issues):
    state = {"last_sync": last_sync, "issues": issues}
    dir_path = str(Path(state_file).parent)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, state_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

# === CONFIG FORMAT DETECTION AND CONVERSION ===

def detect_config_format(config):
    return "source_jira_url" in config

def construct_jira_url(org_name):
    return f"https://{org_name}.atlassian.net"

def print_deprecation_warning():
    print("⚠️  DEPRECATION WARNING: Old configuration format detected.", file=sys.stderr)
    print("   Please migrate to new format with source_*/target_* prefixes.", file=sys.stderr)
    print("   See config.example.json for reference. Old format will be removed in v2.0.0.", file=sys.stderr)
    print("", file=sys.stderr)

def convert_old_to_new_format(config):
    new_config = {}
    if "remote_org" in config:
        new_config["source_jira_url"] = construct_jira_url(config["remote_org"])
    if "local_org" in config:
        new_config["target_jira_url"] = construct_jira_url(config["local_org"])
    if "email" in config:
        new_config["target_jira_user"] = config["email"]
    if "api_token" in config:
        new_config["target_jira_token"] = config["api_token"]
    if "project_key" in config:
        new_config["source_project_key"] = config["project_key"]
        new_config["target_project_key"] = config["project_key"]
    new_config["source_board_id"] = None
    new_config["target_board_id"] = None
    if "status_mapping" in config:
        new_config["status_mapping"] = config["status_mapping"]
    return new_config

# === CONFIG LOADING ===

def load_config(config_file=None):
    config = {}
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

    is_new_format = detect_config_format(config)
    if not is_new_format:
        print_deprecation_warning()
        email = config.get("email") or os.environ.get("JIRA_EMAIL")
        if not email:
            print("Warning: JIRA_EMAIL not found in config or environment.")
            email = input("Enter your email: ")
            if not email:
                print("Error: Email is required")
                sys.exit(1)
        config["email"] = email

        api_token = config.get("api_token") or os.environ.get("JIRA_API_TOKEN")
        if not api_token:
            print("Warning: JIRA_API_TOKEN not found in config or environment.")
            import getpass
            api_token = getpass.getpass("Enter your API token: ")
            if not api_token:
                print("Error: API token is required")
                sys.exit(1)
        config["api_token"] = api_token
        config = convert_old_to_new_format(config)
    else:
        target_jira_user = config.get("target_jira_user") or os.environ.get("JIRA_EMAIL")
        if not target_jira_user:
            print("Warning: target_jira_user not found in config or environment.")
            target_jira_user = input("Enter your email: ")
            if not target_jira_user:
                print("Error: target_jira_user is required")
                sys.exit(1)
        config["target_jira_user"] = target_jira_user

        target_jira_token = config.get("target_jira_token") or os.environ.get("JIRA_API_TOKEN")
        if not target_jira_token:
            print("Warning: target_jira_token not found in config or environment.")
            import getpass
            target_jira_token = getpass.getpass("Enter your API token: ")
            if not target_jira_token:
                print("Error: target_jira_token is required")
                sys.exit(1)
        config["target_jira_token"] = target_jira_token

    if "status_mapping" not in config:
        config["status_mapping"] = {}
    if "sync_comments" not in config:
        config["sync_comments"] = False

    return config

# === PAGINATION ===

def paginate_jql(base_url, jql, fields, auth, headers):
    """Fetch all results from a JQL search using nextPageToken cursor pagination."""
    issues = []
    token = None
    url = f"{base_url}/rest/api/3/search/jql"
    field_str = ",".join(fields) if isinstance(fields, list) else fields

    while True:
        params = {"jql": jql, "maxResults": 100, "fields": field_str}
        if token:
            params["nextPageToken"] = token

        response = requests.get(url, headers=headers, params=params, auth=auth)
        response.raise_for_status()
        data = response.json()
        issues.extend(data.get("issues", []))

        if data.get("isLast", True):
            break
        token = data.get("nextPageToken")
        if not token:
            break

    return issues

# === SOURCE ISSUES ===

def get_source_issues(config, auth, headers, last_sync=None, days=None):
    source_url = config['source_jira_url']
    source_project = config['source_project_key']

    if last_sync:
        # Subtract 60s for clock skew overlap
        dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
        dt = dt - timedelta(seconds=60)
        jql_date = dt.strftime('%Y-%m-%d %H:%M')
        jql = f'project={source_project} AND updated >= "{jql_date}" ORDER BY updated DESC'
        print(f"📅 Incrementele sync: tickets bijgewerkt na {jql_date}")
    elif days:
        jql = f'project={source_project} AND updated >= -{days}d ORDER BY updated DESC'
        print(f"📅 Eerste run met --days {days}")
    else:
        jql = f'project={source_project} ORDER BY updated DESC'
        print(f"📅 Eerste run: alle tickets ophalen")

    try:
        raw_issues = paginate_jql(source_url, jql, ["summary", "description", "status", "updated"], auth, headers)
    except requests.exceptions.RequestException as e:
        print(f"❌ Fout bij ophalen source tickets: {e}")
        sys.exit(1)

    return [
        {
            "key": r["key"],
            "fields": {
                "summary": r["fields"]["summary"],
                "description": r["fields"].get("description", ""),
                "status": {"name": r["fields"]["status"]["name"]},
                "updated": r["fields"].get("updated", "")
            }
        }
        for r in raw_issues
    ]

# === TARGET FETCH + ISSUE MAP ===

def fetch_all_target_issues(config, auth, headers):
    target_url = config['target_jira_url']
    target_project = config['target_project_key']
    jql = f'project={target_project} ORDER BY key DESC'
    try:
        return paginate_jql(target_url, jql, ["summary", "status"], auth, headers)
    except requests.exceptions.RequestException as e:
        print(f"❌ Fout bij ophalen target tickets: {e}")
        sys.exit(1)

def build_issue_map_from_target(target_issues):
    """Build issue_map by extracting [SOURCE-KEY] prefix from target ticket summaries."""
    issue_map = {}
    pattern = re.compile(r'^\[([A-Z]+-\d+)\]')
    for issue in target_issues:
        summary = issue["fields"]["summary"]
        match = pattern.match(summary)
        if match:
            source_key = match.group(1)
            issue_map[source_key] = {
                "target_key": issue["key"],
                "source_updated": ""
            }
    return issue_map

# === COMMENT SYNC FUNCTIONS ===

def get_issue_comments(config, auth, headers, issue_key):
    source_url = config['source_jira_url']
    comments = []
    start_at = 0
    max_results = 50

    while True:
        try:
            url = f"{source_url}/rest/api/3/issue/{issue_key}/comment"
            params = {"startAt": start_at, "maxResults": max_results}
            response = requests.get(url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()

            for comment in data.get("comments", []):
                comments.append({
                    "id": comment["id"],
                    "author": comment.get("author", {}).get("displayName", "Unknown"),
                    "created": comment["created"],
                    "body": comment.get("body", "")
                })

            total = data.get("total", 0)
            if start_at + max_results >= total:
                break
            start_at += max_results

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching comments for {issue_key}: {e}")
            break
        except KeyError as e:
            print(f"⚠️ Missing data in comment response for {issue_key}: {e}")
            break

    comments.sort(key=lambda c: c["created"])
    return comments


def parse_comment_marker(comment_body):
    pattern = r'\[synced-from:\s*([A-Z]+-\d+):comment-(\d+)\]'
    match = re.search(pattern, comment_body)
    if match:
        return (match.group(1), match.group(2))
    return (None, None)


def generate_comment_marker(source_issue_key, comment_id):
    return f"[synced-from: {source_issue_key}:comment-{comment_id}]"


def get_synced_comments(config, auth, headers, target_issue_key):
    target_url = config['target_jira_url']
    synced_ids = set()
    start_at = 0
    max_results = 50

    while True:
        try:
            url = f"{target_url}/rest/api/3/issue/{target_issue_key}/comment"
            params = {"startAt": start_at, "maxResults": max_results}
            response = requests.get(url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()

            for comment in data.get("comments", []):
                body = comment.get("body", "")
                _, comment_id = parse_comment_marker(body)
                if comment_id:
                    synced_ids.add(comment_id)

            total = data.get("total", 0)
            if start_at + max_results >= total:
                break
            start_at += max_results

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching synced comments for {target_issue_key}: {e}")
            break
        except KeyError as e:
            print(f"⚠️ Missing data in synced comments response for {target_issue_key}: {e}")
            break

    return synced_ids


def is_comment_synced(comment_id, synced_comment_ids):
    return str(comment_id) in synced_comment_ids


def format_synced_comment(source_issue_key, comment):
    author = comment.get("author", "Unknown")
    timestamp = comment.get("created", "Unknown date")
    body = comment.get("body", "")
    comment_id = comment.get("id")

    max_body_length = 32500
    if len(body) > max_body_length:
        body = body[:max_body_length] + "\n\n[...comment truncated due to length...]"
        print(f"⚠️ Comment {comment_id} truncated (original length: {len(comment.get('body', ''))} chars)")

    marker = generate_comment_marker(source_issue_key, comment_id)
    return f"[Original comment by {author} on {timestamp}]\n\n{body}\n\n{marker}"


def create_comment(config, auth, headers, target_issue_key, comment_body, dry_run=False):
    if dry_run:
        print(f"  [DRY RUN] Would create comment on {target_issue_key}")
        return True

    target_url = config['target_jira_url']
    try:
        url = f"{target_url}/rest/api/3/issue/{target_issue_key}/comment"
        response = requests.post(url, headers=headers, auth=auth, json={"body": comment_body})
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error creating comment on {target_issue_key}: {e}")
        return False


def sync_comments_for_issue(config, auth, headers, source_issue_key, target_issue_key, dry_run=False):
    if not config.get("sync_comments", False):
        return 0

    print(f"  💬 Syncing comments for {source_issue_key} → {target_issue_key}...")
    source_comments = get_issue_comments(config, auth, headers, source_issue_key)

    if not source_comments:
        print(f"  ℹ️ No comments to sync for {source_issue_key}")
        return 0

    synced_comment_ids = get_synced_comments(config, auth, headers, target_issue_key)
    synced_count = 0
    skipped_count = 0

    for comment in source_comments:
        comment_id = comment["id"]
        if is_comment_synced(comment_id, synced_comment_ids):
            skipped_count += 1
            continue
        formatted_body = format_synced_comment(source_issue_key, comment)
        success = create_comment(config, auth, headers, target_issue_key, formatted_body, dry_run)
        if success:
            synced_count += 1
        else:
            print(f"  ⚠️ Failed to sync comment {comment_id}")

    if dry_run:
        print(f"  [DRY RUN] Would sync {synced_count} comments, skip {skipped_count} already-synced")
    else:
        if synced_count > 0:
            print(f"  ✅ Synced {synced_count} comments, skipped {skipped_count} already-synced")
        elif skipped_count > 0:
            print(f"  ℹ️ All {skipped_count} comments already synced")

    return synced_count

# === STATUS SYNC ===

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
        apply_url = f"{target_url}/rest/api/3/issue/{issue_key}/transitions"
        post_response = requests.post(apply_url, headers=headers, auth=auth,
                                      json={"transition": {"id": transition_id}})
        if post_response.status_code == 204:
            print(f"✅ Status gesynchroniseerd naar '{target_status_name}' voor {issue_key}")
        else:
            print(f"❌ Status-sync fout: {post_response.status_code} {post_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error synchronizing status for {issue_key}: {e}")
    except KeyError as e:
        print(f"❌ Missing data in response when synchronizing status for {issue_key}: {e}")

# === SYNC LOOP ===

def sync_issues(config, auth, headers, source_issues, issue_map, dry_run=False):
    """Sync source issues to target using issue_map for O(1) target key lookups."""
    target_url = config['target_jira_url']
    target_project = config['target_project_key']

    for issue in source_issues:
        source_key = issue["key"]
        summary = issue["fields"]["summary"]
        description = issue["fields"].get("description") or None
        remote_status = issue["fields"]["status"]["name"]
        source_updated = issue["fields"].get("updated", "")

        if source_key in issue_map:
            existing = issue_map[source_key]

            # Skip if source hasn't changed since last sync
            if existing.get("source_updated") and existing["source_updated"] == source_updated:
                print(f"⏭️  Overgeslagen (ongewijzigd): {source_key}")
                continue

            target_key = existing["target_key"]
            print(f"🔄 Bijwerken: {target_key} (voor {source_key})")

            if not dry_run:
                # Update description — retry without on ADF error
                update_url = f"{target_url}/rest/api/3/issue/{target_key}"
                try:
                    resp = requests.put(update_url, headers=headers, auth=auth,
                                        json={"fields": {"description": description}})
                    if resp.status_code == 400 and description is not None:
                        print(f"  ⚠️ Description ADF ongeldig voor {target_key}, sla description over")
                        resp = requests.put(update_url, headers=headers, auth=auth,
                                            json={"fields": {"description": None}})
                    resp.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"  ⚠️ Fout bij updaten description voor {target_key}: {e}")

                # Fetch current target status and sync if needed
                desired_status = config['status_mapping'].get(remote_status)
                if desired_status:
                    try:
                        cur = requests.get(f"{target_url}/rest/api/3/issue/{target_key}",
                                           headers=headers, auth=auth, params={"fields": "status"})
                        cur.raise_for_status()
                        local_status = cur.json()["fields"]["status"]["name"]
                        if local_status != desired_status:
                            sync_status(config, auth, headers, target_key, desired_status)
                    except requests.exceptions.RequestException as e:
                        print(f"  ⚠️ Fout bij ophalen status voor {target_key}: {e}")

            sync_comments_for_issue(config, auth, headers, source_key, target_key, dry_run)
            issue_map[source_key]["source_updated"] = source_updated

        else:
            # New ticket — create on target
            print(f"➕ Aanmaken: nieuw issue voor {source_key}")

            if not dry_run:
                create_url = f"{target_url}/rest/api/3/issue"
                payload = {
                    "fields": {
                        "project": {"key": target_project},
                        "summary": f"[{source_key}] {summary}",
                        "description": description,
                        "issuetype": {"name": "Task"}
                    }
                }
                try:
                    resp = requests.post(create_url, headers=headers, auth=auth, json=payload)
                    if resp.status_code == 400 and description is not None:
                        print(f"  ⚠️ Description ADF ongeldig voor {source_key}, aanmaken zonder description")
                        payload["fields"]["description"] = None
                        resp = requests.post(create_url, headers=headers, auth=auth, json=payload)
                    resp.raise_for_status()
                    new_target_key = resp.json()['key']
                    print(f"  ✅ Aangemaakt: {new_target_key}")

                    issue_map[source_key] = {
                        "target_key": new_target_key,
                        "source_updated": source_updated
                    }

                    desired_status = config['status_mapping'].get(remote_status)
                    if desired_status:
                        sync_status(config, auth, headers, new_target_key, desired_status)

                    sync_comments_for_issue(config, auth, headers, source_key, new_target_key, dry_run)

                except requests.exceptions.RequestException as e:
                    print(f"  ❌ Fout bij aanmaken ticket voor {source_key}: {e}")
            else:
                print(f"  [DRY RUN] Zou aanmaken: [{source_key}] {summary}")

    return issue_map

# === VALIDATE CONNECTION ===

def validate_connections(config, auth, headers):
    source_url = config['source_jira_url']
    target_url = config['target_jira_url']

    print(f"🔍 Validating connection to {source_url}...")
    try:
        response = requests.get(f"{source_url}/rest/api/3/myself", headers=headers, auth=auth)
        response.raise_for_status()
        remote_user = response.json().get("displayName", "Unknown")
        print(f"✅ Connected to {source_url} as {remote_user}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to {source_url}: {e}")
        return False

    print(f"🔍 Validating connection to {target_url}...")
    try:
        response = requests.get(f"{target_url}/rest/api/3/myself", headers=headers, auth=auth)
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
        parser = argparse.ArgumentParser(description='Synchronize Jira issues between organizations')
        parser.add_argument('--config', type=str, required=True,
                            help='Path to JSON configuration file')
        parser.add_argument('--state-file', type=str, required=True,
                            help='Full path to state file (e.g. /var/lib/jirasync/iit.state.json)')
        parser.add_argument('--days', type=int, default=None,
                            help='Bootstrap: days to look back on first run (ignored if state file exists)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Only show what would be done, without making changes')
        args = parser.parse_args()

        config = load_config(args.config)
        auth = HTTPBasicAuth(config['target_jira_user'], config['target_jira_token'])
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        print(f"🔄 Starting synchronization from {config['source_jira_url']} to {config['target_jira_url']}...")
        if args.dry_run:
            print("🔍 DRY RUN MODE: No changes will be made")

        if not validate_connections(config, auth, headers):
            print("❌ Connection validation failed. Exiting.")
            sys.exit(1)

        # Load state
        state = load_state(args.state_file)

        if state:
            last_sync = state["last_sync"]
            issue_map = state.get("issues", {})
            if args.days:
                print("⚠️  --days opgegeven maar genegeerd: state file aanwezig, gebruik last_sync")
        else:
            last_sync = None
            print("🔍 Geen state file gevonden — eerste run modus")
            print("🔍 Target tickets ophalen om issue map op te bouwen...")
            target_issues = fetch_all_target_issues(config, auth, headers)
            issue_map = build_issue_map_from_target(target_issues)
            print(f"  ✅ Issue map gebouwd: {len(issue_map)} bestaande mappings gevonden")

        # Fetch source issues
        source_issues = get_source_issues(config, auth, headers,
                                          last_sync=last_sync,
                                          days=args.days if not state else None)
        print(f"🔎 Gevonden: {len(source_issues)} source tickets om te verwerken")

        # Record sync start time before applying changes
        sync_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Sync
        updated_issue_map = sync_issues(config, auth, headers, source_issues, issue_map,
                                        dry_run=args.dry_run)

        # Persist state
        if not args.dry_run:
            save_state(args.state_file, sync_time, updated_issue_map)
            print(f"💾 State opgeslagen: {args.state_file}")

        print("✅ Synchronisatie voltooid")

    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
