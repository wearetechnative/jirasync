# Capability: Jira Synchronization

## Overview

Synchronizes Jira issues from a client's Jira instance (source) to your organization's Jira instance (target) in a one-way fashion.

## Requirements

### Functional Requirements

#### FR-1: Fetch Source Issues
**Status**: Implemented (jirasync.py:68-123)

The system SHALL fetch issues from the source Jira instance using:
- JQL query: `project={key} AND created >= -{days}d ORDER BY created DESC`
- Jira REST ***REMOVED*** v3: `GET /rest/api/3/search/jql`
- Fields extracted: key, summary, description, status

**Acceptance Criteria**:
- [x] Issues are fetched based on creation date
- [x] Configurable lookback period (days parameter)
- [x] All matching issues are retrieved
- [ ] Pagination works correctly for large datasets (partial implementation)

#### FR-2: Create New Issues
**Status**: Implemented (jirasync.py:166-182)

When a source issue does not exist in target, the system SHALL:
- Create new issue with type "Task"
- Set summary to `[{source_key}] {original_summary}`
- Copy description from source
- Create in specified target project

**Acceptance Criteria**:
- [x] New issues are created with correct format
- [x] Original source key is preserved in summary
- [x] Description is copied verbatim
- [x] Target project is configurable
- [ ] Issue type is configurable (currently hardcoded to "Task")

#### FR-3: Update Existing Issues
**Status**: Implemented (jirasync.py:145-164)

When a source issue already exists in target, the system SHALL:
- Find existing issue by searching for `[{source_key}]` in summary
- Update description to match source
- Synchronize status if mapping exists

**Acceptance Criteria**:
- [x] Existing issues are identified correctly
- [x] Description is updated
- [x] Status is synchronized when mapping exists
- [ ] Handle cases where multiple issues match search pattern

#### FR-4: Status Synchronization
**Status**: Implemented (jirasync.py:186-209)

The system SHALL synchronize status when:
- A status mapping is configured
- The source status exists in mapping
- The target issue status differs from mapped status
- A valid transition exists to target status

**Acceptance Criteria**:
- [x] Status transitions are applied via Jira ***REMOVED***
- [x] Available transitions are queried first
- [x] Case-insensitive status matching
- [x] Graceful handling when no transition available
- [ ] Logging explains why status sync was skipped

#### FR-5: One-Way Sync
**Status**: Implemented (by design)

Changes made in target Jira SHALL NOT be synced back to source.

**Acceptance Criteria**:
- [x] No write operations to source Jira
- [x] Source is read-only throughout process
- [x] Documentation clearly states one-way nature

### Non-Functional Requirements

#### NFR-1: Idempotency
**Status**: Partial

Running the sync multiple times SHALL produce the same result.

**Current State**:
- [x] Existing issues are updated, not duplicated
- [x] Issue matching prevents duplicate creation
- [ ] No change detection - updates happen even if content unchanged
- [ ] Description always overwritten, regardless of changes

**Gap**: Could be more efficient with change detection.

#### NFR-2: Performance
**Status**: Needs Improvement

**Current State**:
- [ ] Fetches all fields with `*all` but uses only 3-4
- [ ] No concurrent processing
- [ ] Sequential ***REMOVED*** calls for each issue
- [x] Single batch fetch for source issues

**Optimization Opportunities**:
- Fetch only needed fields
- Batch operations where possible
- Parallel issue processing

#### NFR-3: Reliability
**Status**: Partial

**Current State**:
- [x] Connection validation before sync
- [x] Per-issue error handling (continues on failure)
- [ ] No retry logic for transient failures
- [ ] No rate limit handling
- [ ] No locking for concurrent executions

#### NFR-4: Observability
**Status**: Basic

**Current State**:
- [x] Console output with emoji indicators
- [x] Error messages printed to stdout
- [ ] No structured logging
- [ ] No log levels (DEBUG, INFO, WARN, ERROR)
- [ ] No metrics or statistics
- [ ] Tokens not redacted in error output

### Data Requirements

#### DR-1: Issue Identification
**Status**: Implemented (fragile)

Source issues SHALL be uniquely identified in target by embedding source key in summary: `[{source_key}] {title}`

**Limitations**:
- Text-based search is fragile
- Could fail if summary is manually edited
- No internal metadata linking
- Depends on JQL search accuracy

**Alternative Approaches** (not implemented):
- Custom field with source issue URL
- Labels or tags
- Issue links

#### DR-2: Field Mapping
**Status**: Minimal

**Currently Synced**:
- Summary (with source key prefix)
- Description
- Status (via mapping)

**Not Synced**:
- Assignee
- Priority
- Labels
- Components
- Custom fields
- Attachments
- Comments
- Subtasks
- Links

### Integration Requirements

#### IR-1: Jira REST ***REMOVED***
**Status**: Implemented

SHALL use Jira REST ***REMOVED*** v3 (Cloud) endpoints:
- `GET /rest/api/3/search/jql` - Fetch issues
- `POST /rest/api/3/search/approximate-count` - Get count
- `GET /rest/api/3/issue/{key}` - Read issue
- `POST /rest/api/3/issue` - Create issue
- `PUT /rest/api/3/issue/{key}` - Update issue
- `GET /rest/api/3/issue/{key}/transitions` - Get transitions
- `POST /rest/api/3/issue/{key}/transitions` - Apply transition
- `GET /rest/api/3/myself` - Validate connection

**Current State**:
- [x] All endpoints implemented
- [x] HTTP Basic Auth used
- [x] JSON content type
- [ ] No support for Jira Server/Data Center

#### IR-2: Authentication
**Status**: Implemented

SHALL authenticate using HTTP Basic Auth with email + ***REMOVED*** token.

**Current State**:
- [x] Single token used for both source and target
- [x] Assumes service user has access to both instances
- [ ] No OAuth support
- [ ] No PAT (Personal Access Token) support

## Edge Cases

### EC-1: Source Issue Deleted
**Status**: Not Handled

If source issue is deleted, target issue remains.

**Current Behavior**: No cleanup of orphaned target issues.

### EC-2: Source Issue Status Changed to Unmapped
**Status**: Handled

If source status has no mapping, sync is skipped with warning.

### EC-3: Target Status Transition Unavailable
**Status**: Handled

If no valid transition exists to desired status, sync is skipped with warning.

### EC-4: Large Description
**Status**: Unknown

Jira has field length limits. No validation or truncation implemented.

### EC-5: Concurrent Sync Runs
**Status**: Not Handled

Multiple sync processes could create duplicate issues.

**Risk**: Race condition if two processes search and both find no existing issue.

### EC-6: ***REMOVED*** Rate Limits
**Status**: Not Handled

Jira Cloud has rate limits. No exponential backoff or retry logic.

## Dependencies

### External Dependencies
- Jira Cloud REST ***REMOVED*** v3
- Network connectivity to both Jira instances
- Valid credentials with appropriate permissions

### Internal Dependencies
- Configuration module (load_config)
- Status mapping configuration (optional)

## Assumptions

1. Service user has read access to source Jira
2. Service user has write access to target Jira
3. Source issues are not deleted frequently
4. Target project exists and user has create permission
5. Network is stable enough for sequential ***REMOVED*** calls
6. ***REMOVED*** rate limits are not exceeded during normal operation

## Future Enhancements

### Incremental Sync
Track last sync time and only fetch changed issues.

**Benefits**:
- Reduced ***REMOVED*** calls
- Faster sync times
- Less chance of rate limiting

**Implementation**:
- Persist last sync timestamp
- Use JQL: `updated >= {last_sync}`
- State file or database

### Bidirectional Sync
Sync changes from target back to source.

**Challenges**:
- Conflict resolution
- Access control (may not have write access to source)
- Risk of sync loops
- Complexity

### Custom Field Mapping
Support syncing custom fields with configurable mapping.

### Attachment Sync
Copy attachments from source to target issues.

### Comment Sync
Replicate comments with attribution.

### Webhook Support
Real-time sync triggered by webhooks instead of polling.

### Multiple Source Boards
Sync from multiple client boards into one target board.

### Filtering
Sync only issues matching specific criteria (labels, components, etc.).

## Metrics

**Proposed Metrics** (not implemented):
- Issues fetched per run
- Issues created
- Issues updated
- Status syncs performed
- Status syncs skipped (with reason)
- ***REMOVED*** calls made
- Sync duration
- Error rate

## Testing Strategy

### Current Testing
**Status**: Unknown - no test files in repository

### Recommended Testing

**Unit Tests**:
- Configuration loading
- Issue matching logic
- Status mapping

**Integration Tests**:
- Mock Jira ***REMOVED*** responses
- Test create/update flows
- Test error handling

**E2E Tests**:
- Real Jira test instances
- Verify end-to-end sync
- Verify idempotency

**Dry-run Testing**:
- Use `--dry-run` flag
- Validate without making changes
