## Why

The `status_mapping` configuration field was accidentally removed from `config.example.json` but is still fully supported by the jirasync.py script and documented in CLAUDE.md and OpenSpec documentation. This creates confusion and inconsistency between the example configuration and actual capabilities.

## What Changes

- Restore `status_mapping` field to `config.example.json` with the same example values from `config.example.json.old`
- Verify consistency across all documentation (CLAUDE.md, OpenSpec specs)
- Ensure the example accurately reflects the optional nature and default behavior of status mapping

## Capabilities

### New Capabilities
<!-- No new capabilities - this is a documentation fix -->

### Modified Capabilities
- `configuration`: Update example configuration to include the missing `status_mapping` field

## Impact

- `config.example.json`: Add status_mapping field back
- Documentation: Verify CLAUDE.md and OpenSpec specs are aligned
- No code changes needed (jirasync.py already supports this field)
- No breaking changes - purely additive to example file
