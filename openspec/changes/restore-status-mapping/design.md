## Context

The `status_mapping` configuration field allows users to map Jira status names from the source board to different status names in the target board. This field is:
- Fully implemented in jirasync.py (lines 56, 64, 162)
- Documented in CLAUDE.md as optional
- Present in config.example.json.old with example mappings
- Missing from current config.example.json

This is a documentation-only fix to restore consistency.

## Goals / Non-Goals

**Goals:**
- Restore `status_mapping` to config.example.json with clear example values
- Verify all documentation accurately describes this optional field
- Maintain consistency across example files and documentation

**Non-Goals:**
- No code changes to jirasync.py (already works correctly)
- No changes to the functionality or behavior of status mapping
- No migration needed (users with existing configs are unaffected)

## Decisions

### Decision 1: Use mapping from config.example.json.old
**Rationale**: The old example file has a clear, realistic status mapping that demonstrates the feature well:
```json
"status_mapping": {
  "To Do": "To Do",
  "In Progress": "In Progress",
  "Waiting for Input": "Waiting for Input",
  "Done": "Done"
}
```

**Alternatives considered**:
- Create new example mappings - Rejected: the existing ones are already clear and tested
- Leave it out - Rejected: users need to see this optional feature documented

### Decision 2: Verify existing OpenSpec specs
**Rationale**: Check that the existing `configuration` spec in openspec/changes/baseline/ correctly documents status_mapping as optional.

**Alternatives considered**:
- Skip verification - Rejected: we need to ensure complete consistency

## Risks / Trade-offs

- **[Risk] Users may have already adapted to missing status_mapping** → Mitigation: This is purely additive to example file, no breaking changes to actual configuration
- **[Risk] Documentation might be inconsistent in other places** → Mitigation: Verify CLAUDE.md and OpenSpec specs as part of this change
