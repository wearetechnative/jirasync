## Context

The jirasync tool currently synchronizes issue metadata (title, description, status) from client Jira boards to organization boards using one-way synchronization. The current architecture uses the Jira REST API v3 with HTTP Basic Auth, processing issues in batches and creating/updating them in the target board.

Comments are an essential part of issue context, containing important discussions, decisions, and updates that are currently lost during synchronization. The existing codebase already handles API calls, authentication, error handling, and dry-run mode, providing a solid foundation for adding comment sync.

Key constraints:
- Must maintain backward compatibility with existing configurations
- Must respect dry-run mode
- Must not break existing one-way sync model
- Must handle API rate limits and failures gracefully
- Must use only the target user's API token (same auth as existing sync)

## Goals / Non-Goals

**Goals:**
- Synchronize comments from source issues to target issues
- Preserve comment author and timestamp information
- Support both initial bulk sync and incremental sync
- Add configuration option to enable/disable comment sync
- Maintain backward compatibility with existing config format
- Handle comment sync failures without breaking issue sync
- Respect dry-run mode for comment operations

**Non-Goals:**
- Bidirectional comment synchronization (remains one-way like issue sync)
- Editing or deleting existing comments in target
- Syncing comment attachments or rich media
- Real-time comment sync via webhooks
- Comment conflict resolution (one-way only)
- Syncing comment reactions or mentions

## Decisions

### 1. Comment Tracking Strategy: Use Comment Body Markers

**Decision:** Track synced comments by including a unique marker in the target comment body (e.g., `[synced-from: ISSUE-123:comment-456]`) rather than using custom fields or external state.

**Rationale:**
- No additional API permissions needed (custom fields require different permissions)
- No external state management or database required
- Simple to implement and debug
- Works with existing Jira API capabilities
- Markers can be hidden at the end of comments for minimal visual impact

**Alternatives considered:**
- Custom fields: Requires additional permissions, complex setup per Jira instance
- External state file: Adds complexity, requires state persistence, harder to debug
- Issue properties API: Not widely supported, adds API complexity

### 2. Comment Sync Timing: Sync on Every Run

**Decision:** Check for new comments on every sync run rather than maintaining a "last synced" timestamp.

**Rationale:**
- Simpler implementation - no need to track sync state
- More resilient to failures (no risk of missing comments due to state corruption)
- Consistent with current issue sync behavior
- Comment checking is relatively fast compared to issue creation
- Idempotent - safe to run multiple times

**Alternatives considered:**
- Timestamp-based incremental sync: Adds complexity, requires state management, prone to timezone issues
- Event-based sync with webhooks: Outside project scope (no real-time requirement)

### 3. Comment Attribution: Prepend Metadata to Body

**Decision:** Format synced comments with attribution in the first line:
```
[Original comment by John Doe on 2026-03-15 14:30 UTC]

<original comment body>

[synced-from: CLIENT-123:10042]
```

**Rationale:**
- Clear visual indication of source and author
- Preserves original context
- Readable by humans
- Machine-parseable for tracking
- Minimal API calls (single comment create operation)

**Alternatives considered:**
- Creating comments as original author: Not possible with API token auth (would need OAuth impersonation)
- Custom rendering via Jira macros: Overly complex, requires admin configuration

### 4. API Endpoints: Use Jira REST API v3

**Decision:** Use `/rest/api/3/issue/{issueKey}/comment` for both fetching and creating comments.

**Rationale:**
- Consistent with existing code (already using API v3)
- Well-documented and stable API
- Returns all comment metadata (author, timestamp, body)
- Supports pagination for issues with many comments

**Alternatives considered:**
- API v2: Deprecated, should not be used for new features

### 5. Configuration: Add Optional Boolean Flag

**Decision:** Add `sync_comments` boolean field to config JSON, defaulting to `false` for backward compatibility.

**Rationale:**
- Simple and clear configuration
- Backward compatible (existing configs continue to work)
- Follows existing config pattern (like `status_mapping`)
- Easy to enable/disable per deployment

**Alternatives considered:**
- Always sync comments: Breaking change for existing deployments
- Separate config file: Overly complex for single boolean
- Environment variable: Less discoverable than config file

### 6. Error Handling: Continue on Comment Failure

**Decision:** Log comment sync errors but continue processing other issues and comments.

**Rationale:**
- Comment sync is supplementary to issue sync
- Partial sync is better than total failure
- Allows identification of problematic comments without blocking others
- Consistent with current error handling approach

**Alternatives considered:**
- Fail fast on any error: Too aggressive, blocks entire sync
- Retry with backoff: Adds complexity, may hit rate limits

### 7. Comment Ordering: Preserve Chronological Order

**Decision:** Sort comments by creation timestamp (oldest first) when syncing to preserve conversation flow.

**Rationale:**
- Maintains natural conversation order
- Makes synced comments easier to follow
- Matches Jira's default display order

**Alternatives considered:**
- API default order: May not be chronological in all cases
- Reverse chronological: Breaks conversation flow

## Risks / Trade-offs

**[Risk] API Rate Limiting with High Comment Volume**
→ **Mitigation:** Implement exponential backoff on rate limit errors. Log skipped comments for manual review. Consider adding `--max-comments-per-issue` flag if needed.

**[Risk] Large Comment Bodies May Exceed API Limits**
→ **Mitigation:** Jira API supports up to 32,767 characters per comment. Truncate if necessary and add warning. Log truncated comments.

**[Risk] Comment Sync Increases API Call Count**
→ **Mitigation:** Make it opt-in (`sync_comments: false` by default). Document expected API usage increase. Consider `--skip-old-issues` flag to only sync comments on recent issues.

**[Risk] Duplicate Comments if Marker Detection Fails**
→ **Mitigation:** Use robust marker format with regex matching. Include both source issue key and comment ID. Add defensive checks before creating.

**[Risk] Performance Degradation with Many Comments**
→ **Mitigation:** Fetch comments only when needed (after determining issue sync needed). Batch API calls where possible. Add progress indicators for user feedback.

**[Trade-off] Comments Show Service Account as Author**
→ **Accepted:** This is inherent to API token authentication. The attribution line preserves original author info. True impersonation would require OAuth which is out of scope.

**[Trade-off] One-way Sync Means Target Comments Aren't Synced Back**
→ **Accepted:** This is consistent with existing issue sync behavior. Jirasync is explicitly designed for one-way sync from client to organization.

## Migration Plan

1. **Pre-deployment:**
   - Update config.example.json with `sync_comments` field and documentation
   - Test with dry-run mode on production configs to validate behavior
   - Verify API token has comment creation permissions

2. **Deployment:**
   - Update jirasync.py with comment sync logic
   - Bump version to 1.2.0 (minor version for new feature)
   - Update CHANGELOG.md
   - Tag release and push to GitHub
   - Elastinix users run `nix flake update jirasync`

3. **Rollout strategy:**
   - Default is `sync_comments: false` - no behavior change for existing deployments
   - Users opt-in by adding `"sync_comments": true` to their config
   - Initial sync will process all historical comments (within `--days` window)
   - Subsequent syncs are incremental (only new comments)

4. **Rollback plan:**
   - If critical issues found, revert to previous jirasync commit
   - No data loss risk - comments in target are append-only
   - Can disable feature by removing `sync_comments` from config or setting to `false`

5. **Monitoring:**
   - Watch systemd logs for comment sync errors
   - Monitor API usage for rate limiting
   - Validate comment attribution format in target Jira
   - Check for duplicate comment creation

## Open Questions

None - all design decisions have been made. Ready to proceed with implementation.
