# Implementation Tasks

## 1. Add Format Detection and Conversion Functions

- [x] 1.1 Add function to detect config format by checking for source_jira_url field
- [x] 1.2 Add function to convert old format to new format with proper field mapping
- [x] 1.3 Add function to construct Jira URLs from org names (https://{org}.atlassian.net)
- [x] 1.4 Add deprecation warning function that prints to stderr

## 2. Update Configuration Loading

- [x] 2.1 Read current config loading code in jirasync.py lines 10-65
- [x] 2.2 Add format detection call after config is loaded from JSON
- [x] 2.3 Add conversion call for old format configs
- [x] 2.4 Add deprecation warning display for old format
- [x] 2.5 Ensure status_mapping is preserved during conversion

## 3. Update Configuration Field Access

- [x] 3.1 Find all references to config['email'] and replace with config['target_jira_user']
- [x] 3.2 Find all references to config['api_token'] and replace with config['target_jira_token']
- [x] 3.3 Find all references to config['remote_org'] and update to extract from config['source_jira_url']
- [x] 3.4 Find all references to config['local_org'] and update to extract from config['target_jira_url']
- [x] 3.5 Find all references to config['project_key'] and update to use config['source_project_key'] or config['target_project_key'] as appropriate
- [x] 3.6 Add support for optional config.get('source_board_id') and config.get('target_board_id')

## 4. Testing

- [x] 4.1 Test with old format config (config.example.json.old converted to old format without status_mapping issue)
- [x] 4.2 Test with new format config (config.example.json)
- [x] 4.3 Verify deprecation warning appears for old format
- [x] 4.4 Verify no deprecation warning for new format
- [x] 4.5 Verify status_mapping works with both formats
- [x] 4.6 Test with board_id fields present and absent

## 5. Documentation Updates

- [x] 5.1 Update CLAUDE.md to note both formats are supported with old format deprecated
- [x] 5.2 Verify config.example.json shows new format (already done in previous change)
