## Context

Current state:
- jirasync.py (lines 10-65) loads config and expects old format fields
- All documentation (CLAUDE.md, config.example.json) shows new format
- Users cannot run the tool without converting documented config to old format
- Both formats documented in baseline spec as "CRITICAL MISMATCH"

Old format:
```python
email, api_token, remote_org, local_org, project_key
```

New format:
```python
source_jira_url, source_project_key, source_board_id,
target_jira_url, target_jira_user, target_jira_token, target_project_key, target_board_id
```

## Goals / Non-Goals

**Goals:**
- Support both old and new configuration formats
- Auto-detect format without user intervention
- Convert old format to new format internally for consistent processing
- Maintain 100% backward compatibility (no breaking changes)
- Warn users about old format deprecation
- Support new board_id fields for filtering

**Non-Goals:**
- Remove old format support (that's for a future major version)
- Validate that Jira URLs are reachable
- Validate board IDs exist
- Change ***REMOVED*** interaction logic (only config parsing)

## Decisions

### Decision 1: Format Detection Strategy
**Choice**: Check for presence of `source_jira_url` field

**Rationale**:
- `source_jira_url` is required in new format, never exists in old format
- Simple, unambiguous check: `if "source_jira_url" in config`
- Fails fast with clear error if neither format detected

**Alternatives considered**:
- Check multiple fields: Rejected - unnecessary complexity
- Version field in config: Rejected - breaks existing configs
- Command-line flag: Rejected - adds user burden

### Decision 2: Conversion Approach
**Choice**: Convert old → new at load time, use new format throughout script

**Rationale**:
- Single code path for all config access
- Simplifies rest of script (no dual-format conditionals)
- New format is clearer and more maintainable
- Enables easier removal of old format in future

**Conversion mapping**:
```python
old → new
---
remote_org → source_jira_url (construct: https://{org}.atlassian.net)
project_key → source_project_key (same value)
None → source_board_id (default: None)

local_org → target_jira_url (construct: https://{org}.atlassian.net)
email → target_jira_user
api_token → target_jira_token
project_key → target_project_key (same value)
None → target_board_id (default: None)
```

**Alternatives considered**:
- Keep dual paths throughout: Rejected - doubles maintenance burden
- Convert new → old: Rejected - moves away from better format

### Decision 3: Deprecation Warning
**Choice**: Print warning to stderr when old format detected

**Rationale**:
- Users should know to migrate
- Non-blocking (doesn't break existing workflows)
- Visible but not intrusive
- Prepares users for future removal

**Warning message**:
```
⚠️  DEPRECATION WARNING: Old configuration format detected.
   Please migrate to new format with source_*/target_* prefixes.
   See config.example.json for reference. Old format will be removed in v2.0.0.
```

**Alternatives considered**:
- No warning: Rejected - users won't know to migrate
- Error/fail: Rejected - breaks backward compatibility
- Log to file: Rejected - less visible

### Decision 4: URL Construction for Old Format
**Choice**: Always use `.atlassian.net` domain

**Rationale**:
- 99% of Jira Cloud instances use this domain
- Simple, predictable behavior
- Old format was already assuming Cloud

**Alternatives considered**:
- Support custom domains: Rejected - old format doesn't have that info
- Prompt user: Rejected - breaks non-interactive use
- Environment variable: Rejected - too complex for compatibility feature

### Decision 5: Field Access Updates
**Choice**: Update all config access throughout script to use new field names

**Rationale**:
- Consistent with conversion approach
- Clearer code (source vs target explicit)
- No conditional logic needed

**Changes needed**:
```python
# Old access → New access
config['email'] → config['target_jira_user']
config['api_token'] → config['target_jira_token']
config['remote_org'] → extract from config['source_jira_url']
config['local_org'] → extract from config['target_jira_url']
config['project_key'] → config['source_project_key'] or config['target_project_key']
```

## Risks / Trade-offs

**[Risk] Old format users might not see deprecation warning** → Mitigation: Print to stderr immediately after load, hard to miss

**[Risk] URL construction might be wrong for self-hosted Jira** → Mitigation: Old format already didn't support self-hosted, document this limitation

**[Risk] Users with both source and target project_key different in old format** → Mitigation: Old format uses same project_key for both, this is expected behavior

**[Risk] Conversion logic has bugs** → Mitigation: Comprehensive testing with both formats, validate all fields present

**[Trade-off] Two code paths to maintain (detection + conversion)** → Acceptable: Isolated to load function, enables future removal

**[Trade-off] Old format users get deprecation warning** → Acceptable: Necessary for migration path, can be suppressed if needed

## Migration Plan

### Phase 1: Support Both Formats (This Change)
1. Deploy updated jirasync.py
2. Old configs continue working (with warning)
3. New configs now work
4. Users can migrate at their own pace

### Phase 2: Encourage Migration (v1.x releases)
1. Keep deprecation warning
2. Update all examples to new format
3. Documentation clearly states old format deprecated

### Phase 3: Remove Old Format (v2.0.0 - Future)
1. Remove format detection
2. Remove conversion logic
3. Only accept new format
4. Major version bump (breaking change)

### Rollback Strategy
If issues found:
1. Revert jirasync.py to previous version
2. Users with new format configs need to convert back to old format
3. No data loss risk (read-only config changes)

## Open Questions

None - design is straightforward with clear requirements.
