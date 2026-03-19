# Baseline Documentation - Summary

This change establishes the baseline specification for jirasync by documenting the current implementation as-is.

## What Was Done

Created comprehensive OpenSpec documentation capturing:

1. **Proposal** - Purpose and scope of baseline documentation
2. **Design Document** - Current architecture and implementation
3. **Capability Specifications**:
   - **Jira Sync** - Core synchronization logic
   - **Configuration** - Config loading and validation
   - **CLI** - Command-line interface
   - **Nix Packaging** - Flake structure and build process

## Key Findings

### Critical Mismatch Discovered
⚠️ **Configuration Format Inconsistency**:
- **config.example.json** uses NEW format (`source_jira_url`, `target_jira_url`, etc.)
- **jirasync.py** uses OLD format (`remote_org`, `local_org`, `email`, `api_token`)
- **CLAUDE.md** documents NEW format as "current"

**Impact**: The example configuration file doesn't actually work with the current code.

### Other Issues Found

1. **Platform metadata**: `meta.platforms = platforms.linux` conflicts with multi-platform flake-utils
2. **Language mixing**: Console output mixes Dutch and English
3. **Incomplete pagination**: Lines 115-121 in jirasync.py have unreachable pagination logic
4. **No version in code**: VERSION file and flake.nix must be manually synchronized
5. **Inefficient fetching**: Fetches all fields (`*all`) but uses only 3-4
6. **No token redaction**: Tokens could leak in error messages

### Implementation Gaps

Features documented but not implemented:
- [ ] Board ID filtering (in example config but not used)
- [ ] New configuration format
- [ ] Version command (`--version`)
- [ ] Proper logging levels
- [ ] Incremental sync
- [ ] Change detection (always updates even if no changes)

## File Structure

```
openspec/changes/baseline/
├── README.md (this file)
├── proposal.md
├── design.md
└── specs/
    ├── jira-sync/
    │   └── spec.md
    ├── configuration/
    │   └── spec.md
    ├── cli/
    │   └── spec.md
    └── nix-packaging/
        └── spec.md
```

## What This Enables

Now that we have baseline documentation, we can:

1. **Propose changes** with clear context of current state
2. **Track evolution** by comparing future changes against baseline
3. **Identify improvements** based on documented gaps and issues
4. **Onboard contributors** with comprehensive system understanding
5. **Plan migration** from old config format to new

## Next Steps

Potential follow-up changes:

### High Priority
1. **Migrate to new config format** - Make code match documented format
2. **Fix platform metadata** - Support macOS properly
3. **Standardize language** - English for all output
4. **Add token redaction** - Security improvement

### Medium Priority
5. **Implement board ID filtering** - Use board_id from config
6. **Add version command** - Read from VERSION file
7. **Fix pagination logic** - Or remove if unnecessary
8. **Source filtering in Nix** - Clean up what's included in builds

### Low Priority
9. **Structured logging** - JSON output, log levels
10. **Change detection** - Don't update if nothing changed
11. **Better error messages** - More context, suggestions
12. **Tests** - Unit, integration, E2E

## How to Use This Documentation

### For Understanding
Read in this order:
1. `proposal.md` - What and why
2. `design.md` - How it works
3. `specs/*/spec.md` - Detailed requirements

### For Implementation
Each spec includes:
- Current status (implemented/partial/not implemented)
- Line number references to code
- Acceptance criteria
- Edge cases
- Future enhancements

### For Planning Changes
1. Review relevant specs for affected capabilities
2. Understand current limitations
3. Propose changes with clear before/after
4. Reference spec sections in your proposal

## Validation

To validate this documentation matches reality:

```bash
# Check code structure
grep -n "def load_config" jirasync.py
grep -n "remote_org" jirasync.py
grep -n "source_jira_url" jirasync.py

# Test CLI
python3 jirasync.py --help
python3 jirasync.py --config config.example.json --days 1 --dry-run

# Check Nix build
nix flake show
nix build
./result/bin/jirasync --help

# Verify metadata
nix flake metadata
nix eval .#packages.x86_64-linux.default.meta.description
```

## Feedback

If you find inaccuracies in this documentation:
1. Verify against actual code
2. Update the relevant spec
3. Note the correction in CHANGELOG.md
4. Consider if code should change to match documented behavior

## Version

This baseline documentation was created on 2026-03-13 for jirasync v1.0.0.
