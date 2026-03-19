# Delta Spec: Configuration Management

This delta spec updates the configuration example to restore the missing `status_mapping` field.

## MODIFIED Requirements

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
  "status_mapping": {
    "To Do": "To Do",
    "In Progress": "In Progress",
    "Waiting for Input": "Waiting for Input",
    "Done": "Done"
  }
}
```

⚠️ **CRITICAL MISMATCH**: Example config uses new format but code uses old format.

#### Scenario: Example config includes status_mapping
- **WHEN** user views config.example.json
- **THEN** the file MUST include a `status_mapping` field with realistic example values

#### Scenario: Status mapping is documented as optional
- **WHEN** user reads the configuration documentation
- **THEN** the documentation MUST clearly indicate that `status_mapping` is optional
- **AND** the default behavior (no status sync) MUST be documented
