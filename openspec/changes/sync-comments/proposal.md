## Why

Currently, jirasync only synchronizes issue metadata (title, description, status, assignee) from client Jira boards to organization boards. Comments on issues are not synced, leading to loss of important context and discussions when issues are moved between systems. This makes it difficult for teams to understand the full history and rationale behind issue updates.

## What Changes

- Add comment synchronization from source (client) issues to target (organization) issues
- Sync all comments when an issue is first created in the target board
- Sync new comments on subsequent sync runs (incremental sync)
- Preserve comment author information and timestamps
- Add configuration option to enable/disable comment sync
- Handle comment ordering to maintain conversation flow
- Add proper error handling for comment sync failures

## Capabilities

### New Capabilities
- `comment-sync`: Synchronize comments from source Jira issues to target Jira issues, including initial bulk sync and incremental updates

### Modified Capabilities
<!-- No existing capability requirements are changing - this is purely additive functionality -->

## Impact

- **Code**: Modifications to `jirasync.py` to add comment fetching and creation logic
- **Configuration**: New optional configuration field `sync_comments` (boolean, defaults to false for backward compatibility)
- **API Usage**: Additional Jira REST API calls to fetch comments from source and create comments in target
- **Performance**: Increased sync time due to additional API calls per issue
- **Data**: Comments will be created in target Jira with attribution information in the comment body
