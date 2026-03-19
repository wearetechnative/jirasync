## Why

The jirasync.py script currently only supports the old configuration format (`email`, `api_token`, `remote_org`, `local_org`, `project_key`), but all documentation and config.example.json use the new format with clear source/target prefixes (`source_jira_url`, `target_jira_user`, etc.). This creates a critical mismatch where users cannot use the documented configuration format, making the tool unusable without trial-and-error.

## What Changes

- Add support for new configuration format with `source_*` and `target_*` prefixes
- Maintain backward compatibility with old configuration format
- Auto-detect which format is being used
- Convert old format to new format internally for consistent processing
- Add deprecation warning when old format is detected
- Support new fields: `source_board_id`, `target_board_id` for board-specific filtering
- Use full Jira URLs instead of just organization names

## Capabilities

### New Capabilities
<!-- No new capabilities - this is configuration parsing enhancement -->

### Modified Capabilities
- `configuration`: Update configuration loading to support both old and new formats with automatic detection and conversion

## Impact

- **jirasync.py**: Configuration loading logic (lines 10-65)
  - Add format detection
  - Add old-to-new format conversion
  - Update field access throughout script to use new format
  - Add deprecation warnings for old format
- **Backward compatibility**: Existing config files with old format will continue to work
- **No breaking changes**: Both formats supported
- **User experience**: Users can now use the documented configuration format
- **Future**: Enables eventual deprecation of old format in next major version
