# Capability: Configuration Management

## Overview

Loads and validates configuration from multiple sources with fallback priority: config file → environment variables → interactive prompts.

## Requirements

### FR-1: Configuration Loading
**Status**: Implemented (jirasync.py:10-65)

The system SHALL load configuration in the following priority order:
1. JSON configuration file (if `--config` provided)
2. Environment variables
3. Interactive prompts (for missing values)

**Acceptance Criteria**:
- [x] JSON files are parsed correctly
- [x] Invalid JSON triggers clear error message
- [x] Missing config file triggers clear error message
- [x] Environment variables override defaults
- [x] Interactive prompts for missing credentials

### FR-2: Configuration Sources

#### Config File
**Status**: Implemented

SHALL accept JSON file with configuration.

**Current Format** (in code):
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

**Documented Format** (in config.example.json):
```json
{
  "source_jira_url": "https://client.atlassian.net",
  "source_project_key": "CLIENT",
  "source_board_id": 123,
  "target_jira_url": "https://yourcompany.atlassian.net",
  "target_jira_user": "user@company.com",
  "target_jira_token": "token",
  "target_project_key": "INT",
  "target_board_id": 456,
  "status_mapping": {...}
}
```

⚠️ **CRITICAL MISMATCH**: Example config uses new format but code uses old format.

#### Environment Variables
**Status**: Partial

SHALL support environment variables:
- `JIRA_EMAIL` → email
- `JIRA_***REMOVED***_TOKEN` → api_token

**Limitations**:
- [ ] No env vars for org names
- [ ] No env vars for project keys
- [ ] Only credentials are supported

#### Interactive Prompts
**Status**: Implemented

SHALL prompt for missing credentials:
- Email: visible input
- ***REMOVED*** token: hidden input (via getpass)

**Acceptance Criteria**:
- [x] Prompts only for missing values
- [x] ***REMOVED*** token input is hidden
- [x] Clear instructions provided
- [x] Empty input triggers error

### FR-3: Configuration Validation
**Status**: Minimal

SHALL validate that required fields are present:
- Email/user
- ***REMOVED*** token
- Organization names/URLs
- Project key(s)

**Current State**:
- [x] Validates email and token are non-empty
- [ ] Does not validate URL format
- [ ] Does not validate org names exist
- [ ] Does not validate project keys exist
- [ ] Does not pre-validate status mapping

**Recommended Additions**:
- URL format validation
- Required field checking
- Status mapping validation

### FR-4: Secure Credential Handling
**Status**: Partial

SHALL handle credentials securely:
- No plaintext passwords in logs
- Hidden input for interactive prompts
- Warning about plaintext storage

**Current State**:
- [x] getpass for hidden password input
- [x] Warning messages about environment/config
- [ ] Tokens NOT redacted in error logs
- [ ] No validation of token format

**Security Gaps**:
- Error messages may expose tokens if ***REMOVED*** errors include request details
- No validation that token follows expected format (starts with ATATT...)

## Configuration Schema

### Old Format (Currently Used)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `email` | string | Yes* | env: JIRA_EMAIL | User email for authentication |
| `api_token` | string | Yes* | env: JIRA_***REMOVED***_TOKEN | Jira ***REMOVED*** token |
| `remote_org` | string | Yes | "" | Client organization name (e.g., "acme-corp") |
| `local_org` | string | Yes | "" | Your organization name (e.g., "mycompany") |
| `project_key` | string | Yes | "" | Project key (used for BOTH source and target) |
| `status_mapping` | object | No | {} | Map of source → target statuses |

*Can be provided via environment or interactive prompt

**Issues with Old Format**:
- Ambiguous which org is source vs target
- Only org name, not full URL
- Same project key for source and target
- No board ID support

### New Format (Documented but Not Implemented)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source_jira_url` | string | Yes | - | Full URL to client's Jira |
| `source_project_key` | string | Yes | - | Project key in client's Jira |
| `source_board_id` | integer | No | null | Specific board to sync from |
| `target_jira_url` | string | Yes | - | Full URL to your org's Jira |
| `target_jira_user` | string | Yes* | env: JIRA_EMAIL | Email of service user |
| `target_jira_token` | string | Yes* | env: JIRA_***REMOVED***_TOKEN | ***REMOVED*** token |
| `target_project_key` | string | Yes | - | Project key in your org |
| `target_board_id` | integer | No | null | Target board ID |
| `status_mapping` | object | No | {} | Map of source → target statuses |

**Benefits of New Format**:
- ✅ Clear source vs target distinction
- ✅ Full URLs instead of org names
- ✅ Different project keys for source/target
- ✅ Board ID support for filtering
- ✅ Explicit about which credentials belong where

### Status Mapping Format

```json
{
  "status_mapping": {
    "Source Status Name": "Target Status Name",
    "To Do": "Backlog",
    "In Progress": "In Development",
    "Done": "Completed"
  }
}
```

**Behavior**:
- Keys = source status names (exact match, case-insensitive in code)
- Values = target status names
- If source status not in mapping, status sync is skipped
- If target status has no available transition, sync is skipped

## Error Handling

### Config File Errors

**File Not Found** (jirasync.py:21-22):
```
❌ Config file not found: {path}
Exit code: 1
```

**Invalid JSON** (jirasync.py:24-25):
```
❌ Invalid JSON in config file: {error}
Exit code: 1
```

### Missing Credentials

**Missing Email** (jirasync.py:30-36):
```
Warning: JIRA_EMAIL not found in config or environment.
Please set it with: export JIRA_EMAIL='your-email'
Or enter your email now (input will be visible):
```

**Missing Token** (jirasync.py:42-48):
```
Warning: JIRA_***REMOVED***_TOKEN not found in config or environment.
Please set it with: export JIRA_***REMOVED***_TOKEN='your-token'
Or enter your ***REMOVED*** token now (input will be hidden):
```

**Empty Input** (jirasync.py:34-36, 46-48):
```
Error: Email is required
Exit code: 1
```

## Migration Path

### Phase 1: Support Both Formats
1. Detect which format is used (check for `source_jira_url` vs `remote_org`)
2. Parse accordingly
3. Convert old format to new format internally
4. Log deprecation warning for old format

### Phase 2: Deprecate Old Format
1. Loud warnings when old format detected
2. Documentation updated
3. Migration guide provided

### Phase 3: Remove Old Format
1. Only accept new format
2. Major version bump (breaking change)

## Environment Variable Expansion

**Proposed** (not implemented):
Support environment variable substitution in config files:

```json
{
  "target_jira_token": "${JIRA_***REMOVED***_TOKEN}",
  "target_jira_user": "${JIRA_EMAIL}"
}
```

Benefits:
- Avoid plaintext tokens in config files
- Config file can be committed safely
- Tokens loaded from secure sources

## Configuration Validation Examples

### Valid Configurations

**Minimal (old format)**:
```json
{
  "remote_org": "acme-corp",
  "local_org": "mycompany",
  "project_key": "PROJ"
}
```
Note: email and api_token from environment

**Complete (new format)**:
```json
{
  "source_jira_url": "https://acme-corp.atlassian.net",
  "source_project_key": "ACME",
  "target_jira_url": "https://mycompany.atlassian.net",
  "target_jira_user": "jirasync@mycompany.com",
  "target_jira_token": "ATATT...",
  "target_project_key": "INT",
  "status_mapping": {
    "To Do": "Backlog",
    "Done": "Completed"
  }
}
```

### Invalid Configurations

**Missing required fields**:
```json
{
  "remote_org": "acme-corp"
  // Missing local_org, project_key
}
```

**Malformed JSON**:
```json
{
  "remote_org": "acme-corp",
  "local_org": "mycompany"  // Missing comma
  "project_key": "PROJ"
}
```

## Security Best Practices

### DO:
- ✅ Use environment variables for credentials
- ✅ Use agenix or similar for encrypted storage in NixOS
- ✅ Rotate tokens regularly
- ✅ Use dedicated service accounts
- ✅ Add config files with real tokens to .gitignore

### DON'T:
- ❌ Commit real tokens to git
- ❌ Share config files with real credentials
- ❌ Use personal tokens for service accounts
- ❌ Log credentials in error messages

## Testing

### Test Cases

1. **Config file loading**
   - Valid JSON → Success
   - Invalid JSON → Error with line number
   - Missing file → Clear error
   - Empty file → Error

2. **Environment variable fallback**
   - No config file + env vars → Success
   - Config file + env vars → Config file wins
   - Partial config + env vars → Merged

3. **Interactive prompts**
   - Missing email → Prompt → Success
   - Missing token → Hidden prompt → Success
   - Empty input → Error
   - Ctrl+C → Graceful exit

4. **Configuration validation**
   - All required fields → Success
   - Missing email → Prompt or error
   - Missing org → Error
   - Empty values → Error

5. **Status mapping**
   - Valid mapping → Loaded
   - Missing mapping → Empty dict
   - Invalid format → Error
