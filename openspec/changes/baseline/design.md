# Design: Jirasync Architecture

## System Overview

Jirasync is a **one-way synchronization tool** that copies Jira issues from a client's Jira instance (source) to your organization's Jira instance (target).

```
┌─────────────────────────────────────────────────┐
│ Client Jira (Source)                            │
│ https://client.atlassian.net                    │
│                                                 │
│  ┌─────────────────────────────────────┐        │
│  │ Issues (Read-Only Access)           │        │
│  │                                     │        │
│  │  [ACME-123] Feature request         │        │
│  │  [ACME-124] Bug report              │        │
│  │  [ACME-125] Question                │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
                      │
                      │ jirasync.py
                      │ (HTTP Basic Auth)
                      │ GET /rest/api/3/search/jql
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ Your Jira (Target)                              │
│ https://yourcompany.atlassian.net               │
│                                                 │
│  ┌─────────────────────────────────────┐        │
│  │ Synced Issues (Read/Write)          │        │
│  │                                     │        │
│  │  [INT-456] [ACME-123] Feature...    │        │
│  │  [INT-457] [ACME-124] Bug report    │        │
│  │  [INT-458] [ACME-125] Question      │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

**Key Principle**: One-way sync. Changes in your org's board are NOT synced back.

## Current Implementation Status

⚠️ **Configuration Format Mismatch Detected**:
- **jirasync.py** (lines 53-56): Uses OLD format (`remote_org`, `local_org`, `email`, `api_token`)
- **config.example.json**: Uses NEW format (`source_jira_url`, `target_jira_url`, etc.)
- **CLAUDE.md**: Documents NEW format as "current"

The example config file is ahead of the Python implementation. The code needs migration.

## Architecture Components

### 1. Configuration Management

**Current Implementation** (jirasync.py:10-65):

```python
# load_config() function handles:
- JSON file loading
- Environment variable fallback (JIRA_EMAIL, JIRA_***REMOVED***_TOKEN)
- Interactive prompts for missing credentials
- Configuration validation
```

**OLD Format** (currently used by code):
```json
{
  "email": "user@company.com",
  "api_token": "token",
  "remote_org": "client-org",
  "local_org": "your-org",
  "project_key": "PROJ",
  "status_mapping": {...}
}
```

**NEW Format** (documented but not implemented):
```json
{
  "source_jira_url": "https://client.atlassian.net",
  "source_project_key": "CLIENT",
  "target_jira_url": "https://yourcompany.atlassian.net",
  "target_jira_user": "user@company.com",
  "target_jira_token": "token",
  "target_project_key": "INT",
  "status_mapping": {...}
}
```

### 2. Authentication Model

**Single Token Approach**:
- Uses HTTP Basic Auth with email + ***REMOVED*** token
- Same credentials used for BOTH source and target
- Service user must have:
  - **Read access** to client's Jira (granted by client)
  - **Write access** to your org's Jira

Implementation: `jirasync.py:258`
```python
auth = HTTPBasicAuth(config['email'], config['api_token'])
```

### 3. Issue Fetching (Source)

**Function**: `get_remote_issues()` (jirasync.py:68-123)

**Flow**:
```
1. Get approximate count
   POST /rest/api/3/search/approximate-count

2. Fetch all matching issues
   GET /rest/api/3/search/jql
   JQL: "project={key} AND created >= -{days}d ORDER BY created DESC"

3. Extract relevant fields:
   - key (e.g., "ACME-123")
   - summary
   - description
   - status.name
```

**Current Limitation**: Fetches ALL fields (`"fields": "*all"`) even though only a few are used. Could be optimized.

### 4. Issue Synchronization (Target)

**Function**: `sync_issues_to_local()` (jirasync.py:127-183)

**For Each Source Issue**:

```
┌─────────────────────────────────────────┐
│ Search for existing local issue         │
│ JQL: summary ~ "[{remote_key}]"         │
└─────────────┬───────────────────────────┘
              │
         ┌────┴────┐
         │ Found?  │
         └────┬────┘
              │
      ┌───────┴────────┐
      │                │
    YES               NO
      │                │
      ▼                ▼
  ┌──────────┐    ┌──────────┐
  │ UPDATE   │    │ CREATE   │
  │          │    │          │
  │ PUT      │    │ POST     │
  │ /issue/  │    │ /issue   │
  │ {key}    │    │          │
  └────┬─────┘    └────┬─────┘
       │               │
       ▼               │
  ┌──────────┐         │
  │ Sync     │         │
  │ Status?  │         │
  └──────────┘         │
                       │
              ┌────────┴─────────┐
              │ Summary Format:  │
              │ [{remote}] {title}│
              └──────────────────┘
```

**Issue Creation** (jirasync.py:168-182):
- Creates new issue with `issuetype: "Task"` (hardcoded)
- Summary format: `[{remote_key}] {original_summary}`
- Copies description as-is

**Issue Update** (jirasync.py:150-164):
- Updates description field
- Syncs status if mapping exists

### 5. Status Synchronization

**Function**: `sync_status()` (jirasync.py:186-209)

**Flow**:
```
1. GET /issue/{key}/transitions
   ├─ Fetch available transitions
   └─ Find transition to target status

2. Match status (case-insensitive)

3. POST /issue/{key}/transitions
   └─ Apply transition by ID
```

**Status Mapping** (optional config):
```json
{
  "status_mapping": {
    "To Do": "To Do",
    "In Progress": "In Progress",
    "Waiting for Input": "Waiting for Input",
    "Done": "Done"
  }
}
```

If no mapping exists or status unavailable, sync is skipped with warning.

### 6. Connection Validation

**Function**: `validate_connections()` (jirasync.py:213-238)

Pre-flight checks before sync:
```
GET /rest/api/3/myself  (remote org)
GET /rest/api/3/myself  (local org)
```

Ensures credentials work for both Jira instances.

### 7. CLI Interface

**Command**: `jirasync --config <path> --days <number> [--dry-run]`

**Arguments** (jirasync.py:245-252):
- `--config`: Path to JSON config file (optional, falls back to env vars)
- `--days`: Lookback period (default: 90 days)
- `--dry-run`: Validation mode, no writes

**Dry-run behavior** (jirasync.py:274-278):
- Fetches remote issues
- Validates connections
- Does NOT call `sync_issues_to_local()`
- Useful for testing credentials and queries

## Data Flow

```
┌──────────┐
│   CLI    │
│  Args    │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  load_config()   │
│                  │
│  File → Env →    │
│  Interactive     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ validate_        │
│ connections()    │
│                  │
│ /myself × 2      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ get_remote_      │
│ issues()         │
│                  │
│ JQL search       │
│ created >= -Nd   │
└────┬─────────────┘
     │
     │ [Issue List]
     │
     ▼
┌──────────────────┐
│ sync_issues_     │
│ to_local()       │
│                  │
│ For each issue:  │
│  • Search local  │
│  • Create/Update │
│  • Sync status   │
└──────────────────┘
```

## Dependencies

**Python Standard Library**:
- `requests` - HTTP client for Jira REST ***REMOVED***
- `argparse` - CLI argument parsing
- `json` - Config file parsing
- `os`, `sys` - Environment and system operations
- `getpass` - Secure password input

**External**:
- Jira REST ***REMOVED*** v3 (Cloud)
- HTTPBasicAuth authentication

## Error Handling

**Current Strategy**:
- Connection failures → Exit with status 1
- Invalid JSON config → Exit with status 1
- Missing credentials → Prompt interactively (if not in config/env)
- ***REMOVED*** errors during sync → Print error, continue to next issue
- Keyboard interrupt → Graceful shutdown
- Unexpected exceptions → Print error, exit with status 1

**Logging**: Print statements with emoji indicators (✅ ❌ 🔄 ➕ ⚠️)

## Nix Packaging

**Not yet examined** - flake.nix should be analyzed separately.

The Python script is wrapped by Nix to provide:
- `jirasync` command
- Python environment with `requests` library
- Cross-platform builds

## Limitations & Edge Cases

### Current Limitations

1. **Hardcoded issue type**: Always creates "Task" type
2. **Single project**: Only syncs one project at a time
3. **No incremental tracking**: Re-processes all issues within time window
4. **No custom fields**: Only syncs summary, description, status
5. **No attachments**: Attachments are not copied
6. **No comments**: Comments are not synced
7. **Summary-based matching**: Uses text search to find existing issues (fragile)
8. **All fields fetch**: Fetches all fields but uses only 3-4

### Edge Cases

1. **Summary collision**: If local issues have `[{key}]` in title for other reasons
2. **Status unavailable**: If target status doesn't exist or no transition available
3. **Pagination**: Code has pagination logic but seems incomplete (lines 115-121)
4. **Large datasets**: Fetching all issues at once with `maxResults: total`
5. *****REMOVED*** rate limits**: No retry logic or rate limit handling
6. **Concurrent runs**: No locking mechanism for parallel executions

## Security Considerations

**Credential Storage**:
- JSON config files may contain plaintext tokens (mentioned in CLAUDE.md as risk)
- Environment variables supported for sensitive data
- Interactive prompt as fallback (password hidden with getpass)

*****REMOVED*** Security**:
- Uses HTTPS for all ***REMOVED*** calls
- HTTP Basic Auth (email + token)
- No token validation before making ***REMOVED*** calls (relies on first ***REMOVED*** call to fail)

**Logging**:
- Code does NOT currently redact tokens from error messages
- Risk: Tokens could appear in logs if ***REMOVED*** errors include request details

## Open Questions

1. Why does config.example.json use new format but code uses old?
2. Is the migration to new config format planned?
3. Should board_id support be added? (It's in example config but not used)
4. Should we support Jira Server/Data Center or only Cloud?
5. Is the pagination logic (lines 115-121) correct? It seems unreachable.

## Next Steps for Implementation Alignment

1. Migrate jirasync.py to use new configuration format
2. Add backward compatibility for old format
3. Fix pagination logic or remove if unnecessary
4. Add board_id filtering support
5. Improve error messages and token redaction
