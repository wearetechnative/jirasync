# Delta Spec: Configuration Management

This delta spec adds support for the new configuration format while maintaining backward compatibility.

## ADDED Requirements

### Requirement: Dual format support
The system SHALL support both old and new configuration formats without requiring user intervention.

#### Scenario: New format configuration loads successfully
- **WHEN** user provides config with `source_jira_url` field
- **THEN** system SHALL parse it as new format
- **AND** system SHALL NOT show deprecation warning

#### Scenario: Old format configuration loads successfully
- **WHEN** user provides config with `remote_org` and `local_org` fields
- **THEN** system SHALL parse it as old format
- **AND** system SHALL convert it to new format internally
- **AND** system SHALL show deprecation warning

#### Scenario: Format detection is automatic
- **WHEN** user provides any valid config
- **THEN** system SHALL automatically detect format
- **AND** system SHALL NOT require format specification from user

### Requirement: Format detection
The system SHALL detect configuration format by checking for presence of `source_jira_url` field.

#### Scenario: New format detected
- **WHEN** config contains `source_jira_url` field
- **THEN** system SHALL identify it as new format

#### Scenario: Old format detected
- **WHEN** config does NOT contain `source_jira_url` field
- **THEN** system SHALL identify it as old format

#### Scenario: Invalid format rejected
- **WHEN** config lacks both `source_jira_url` AND required old format fields
- **THEN** system SHALL exit with clear error message

### Requirement: Old to new format conversion
The system SHALL convert old format configurations to new format for internal processing.

#### Scenario: Organization names converted to URLs
- **WHEN** old format provides `remote_org: "acme-corp"` and `local_org: "mycompany"`
- **THEN** system SHALL convert to `source_jira_url: "https://acme-corp.atlassian.net"` and `target_jira_url: "https://mycompany.atlassian.net"`

#### Scenario: Credentials mapped correctly
- **WHEN** old format provides `email` and `api_token`
- **THEN** system SHALL map to `target_jira_user` and `target_jira_token`

#### Scenario: Project key mapped to both source and target
- **WHEN** old format provides single `project_key`
- **THEN** system SHALL use same value for both `source_project_key` and `target_project_key`

#### Scenario: Board IDs default to None
- **WHEN** old format config is converted
- **THEN** system SHALL set `source_board_id` and `target_board_id` to `None`

### Requirement: Deprecation warning
The system SHALL warn users when old format is detected.

#### Scenario: Deprecation warning displayed
- **WHEN** old format configuration is loaded
- **THEN** system SHALL print deprecation warning to stderr
- **AND** warning SHALL mention new format with source_*/target_* prefixes
- **AND** warning SHALL reference config.example.json
- **AND** warning SHALL state version when old format will be removed

#### Scenario: No warning for new format
- **WHEN** new format configuration is loaded
- **THEN** system SHALL NOT print deprecation warning

### Requirement: New format field support
The system SHALL support all new format fields including board IDs.

#### Scenario: Full new format configuration
- **WHEN** config provides all new format fields including `source_board_id` and `target_board_id`
- **THEN** system SHALL load all fields successfully

#### Scenario: Board ID fields are optional
- **WHEN** config omits `source_board_id` or `target_board_id`
- **THEN** system SHALL treat them as `None`
- **AND** system SHALL NOT filter by board

### Requirement: Consistent field access
The system SHALL use new format field names throughout for all config access.

#### Scenario: All config references use new format
- **WHEN** script accesses configuration values
- **THEN** script SHALL ONLY use new format field names
- **AND** script SHALL NOT have conditional logic for old vs new format beyond loading

## MODIFIED Requirements

### FR-2: Configuration Sources

#### Config File
**Status**: Implemented

SHALL accept JSON file with configuration in either old or new format.

**Old Format** (deprecated, still supported):
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

**New Format** (recommended):
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

#### Scenario: Old format config is accepted
- **WHEN** user provides config file in old format
- **THEN** system SHALL load it successfully
- **AND** system SHALL convert to new format internally
- **AND** system SHALL display deprecation warning

#### Scenario: New format config is accepted
- **WHEN** user provides config file in new format
- **THEN** system SHALL load it successfully
- **AND** system SHALL use fields directly without conversion

#### Scenario: Mixed format rejected
- **WHEN** user provides config with both old and new format fields
- **THEN** system SHALL use new format (source_jira_url takes precedence)
