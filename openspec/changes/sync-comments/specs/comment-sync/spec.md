## ADDED Requirements

### Requirement: Configuration for comment synchronization
The system SHALL provide a configuration option to enable or disable comment synchronization.

#### Scenario: Comment sync enabled
- **WHEN** the configuration contains `"sync_comments": true`
- **THEN** the system synchronizes comments from source to target issues

#### Scenario: Comment sync disabled
- **WHEN** the configuration contains `"sync_comments": false` or the field is absent
- **THEN** the system skips comment synchronization

### Requirement: Fetch comments from source issue
The system SHALL fetch all comments from source (client) Jira issues via the Jira REST API.

#### Scenario: Fetch comments for synced issue
- **WHEN** processing an issue that needs comment synchronization
- **THEN** the system retrieves all comments using GET /rest/api/3/issue/{issueKey}/comment

#### Scenario: Source issue has no comments
- **WHEN** a source issue has zero comments
- **THEN** the system skips comment creation for that issue

### Requirement: Initial bulk comment sync
The system SHALL synchronize all existing comments when creating a new target issue.

#### Scenario: First sync of issue with comments
- **WHEN** creating a new target issue from a source issue that has comments
- **THEN** the system creates all source comments in the target issue

#### Scenario: Comments are created in chronological order
- **WHEN** syncing multiple comments from a source issue
- **THEN** the system creates them in the target issue ordered by creation timestamp (oldest first)

### Requirement: Incremental comment sync
The system SHALL synchronize only new comments on subsequent sync runs.

#### Scenario: Sync detects new comments
- **WHEN** a source issue has comments created after the last sync
- **THEN** the system creates only those new comments in the target issue

#### Scenario: No new comments since last sync
- **WHEN** all source comments already exist in the target issue
- **THEN** the system skips comment creation for that issue

### Requirement: Preserve comment metadata
The system SHALL preserve comment author and timestamp information when synchronizing.

#### Scenario: Comment includes original author
- **WHEN** creating a comment in the target issue
- **THEN** the comment body includes the original author's name and timestamp

#### Scenario: Comment attribution format
- **WHEN** a comment is synced from source
- **THEN** the target comment body starts with "[Original author: {author} on {timestamp}]" followed by the original comment text

### Requirement: Handle comment sync failures gracefully
The system SHALL continue processing other issues when comment synchronization fails.

#### Scenario: Comment API call fails
- **WHEN** fetching or creating comments fails for an issue
- **THEN** the system logs the error and continues syncing other issues

#### Scenario: Partial comment sync failure
- **WHEN** some comments sync successfully but others fail
- **THEN** the system creates the successful comments and logs errors for failed ones

### Requirement: Track synced comments
The system SHALL track which comments have been synchronized to avoid duplicates.

#### Scenario: Identify already-synced comments
- **WHEN** determining which comments to sync
- **THEN** the system compares source comment IDs with previously synced comment metadata

#### Scenario: Store comment sync metadata
- **WHEN** successfully creating a comment in the target issue
- **THEN** the system stores the source comment ID in the target comment's metadata or custom field

### Requirement: Dry-run mode for comments
The system SHALL respect dry-run mode when synchronizing comments.

#### Scenario: Dry-run skips comment creation
- **WHEN** running with --dry-run flag enabled
- **THEN** the system logs which comments would be synced without creating them

#### Scenario: Dry-run reports comment sync plan
- **WHEN** running with --dry-run flag enabled
- **THEN** the system outputs the number of comments that would be synced for each issue
