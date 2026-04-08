## 1. Configuration Support

- [x] 1.1 Add `sync_comments` boolean field to config loading with default value `false`
- [x] 1.2 Update `config.example.json` with `sync_comments` field and documentation
- [x] 1.3 Verify backward compatibility - old configs work without `sync_comments` field

## 2. Comment Fetching

- [x] 2.1 Create `get_issue_comments()` function to fetch comments from source issue via API
- [x] 2.2 Implement pagination handling for issues with many comments
- [x] 2.3 Add error handling for comment fetch failures (log and continue)
- [x] 2.4 Sort fetched comments by creation timestamp (chronological order)

## 3. Comment Tracking

- [x] 3.1 Create `parse_comment_marker()` function to extract source issue and comment ID from marker
- [x] 3.2 Create `generate_comment_marker()` function to create unique tracking marker
- [x] 3.3 Create `get_synced_comments()` function to fetch target issue comments and extract synced markers
- [x] 3.4 Create `is_comment_synced()` function to check if a comment has already been synced

## 4. Comment Creation

- [x] 4.1 Create `format_synced_comment()` function to format comment with attribution and marker
- [x] 4.2 Create `create_comment()` function to post comment to target issue via API
- [x] 4.3 Add error handling for comment creation failures (log and continue)
- [x] 4.4 Implement comment body truncation if exceeding API limits (32,767 chars)

## 5. Comment Sync Logic

- [x] 5.1 Add `sync_comments()` function to orchestrate comment synchronization for an issue
- [x] 5.2 Implement initial bulk sync - sync all comments when creating new target issue
- [x] 5.3 Implement incremental sync - sync only new comments for existing target issues
- [x] 5.4 Integrate `sync_comments()` call into `sync_issues_to_local()` function

## 6. Dry-Run Support

- [x] 6.1 Add dry-run mode checks to `create_comment()` function
- [x] 6.2 Log comment sync actions in dry-run mode without API calls
- [x] 6.3 Display count of comments that would be synced per issue in dry-run output

## 7. Error Handling and Logging

- [x] 7.1 Add informative log messages for comment sync start/completion per issue
- [x] 7.2 Implement graceful handling of API rate limit errors with logging
- [x] 7.3 Log skipped comments with reason (already synced, fetch failed, etc.)
- [x] 7.4 Ensure comment sync failures don't break issue sync

## 8. Testing and Validation

- [x] 8.1 Test comment sync with source issue containing zero comments
- [x] 8.2 Test comment sync with source issue containing multiple comments
- [x] 8.3 Test incremental sync - verify new comments are synced, old comments skipped
- [x] 8.4 Test dry-run mode - verify no comments created but actions logged
- [x] 8.5 Test with `sync_comments: false` - verify comments not synced
- [x] 8.6 Test with `sync_comments: true` - verify comments synced correctly
- [x] 8.7 Verify comment attribution format (author and timestamp visible)
- [x] 8.8 Verify comment tracking markers work correctly
- [x] 8.9 Test error handling - simulate API failures and verify graceful handling

## 9. Documentation

- [x] 9.1 Update CHANGELOG.md with comment sync feature
- [x] 9.2 Update CLAUDE.md with comment sync implementation details
- [x] 9.3 Document comment tracking marker format in CLAUDE.md
- [x] 9.4 Add comment sync configuration examples to documentation
