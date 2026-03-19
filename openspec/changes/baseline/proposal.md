# Baseline Documentation

## Summary

Establish the baseline specification for jirasync - a one-way Jira synchronization tool that syncs issues from client Jira instances to your organization's Jira instance.

## Problem

Jirasync is currently operational but lacks formal specification documentation in the OpenSpec format. This makes it harder to:
- Understand the system's capabilities and boundaries
- Plan future enhancements with clear context
- Onboard contributors to the project
- Track changes and evolution over time

## Solution

Create comprehensive OpenSpec documentation that captures:
1. **Current architecture** - How jirasync works today
2. **Core capabilities** - What jirasync can do
3. **Configuration specification** - How to configure the tool
4. **Integration points** - How it integrates with Nix/Elastinix

This is not proposing changes - it's documenting what exists to establish a baseline for future work.

## Scope

### In Scope
- Document existing Python synchronization logic
- Specify configuration format and fields
- Document Nix flake packaging approach
- Describe CLI interface
- Capture authentication model
- Document status mapping feature

### Out of Scope
- Implementing new features
- Changing existing behavior
- Refactoring code
- Adding tests (beyond documenting current test strategy)

## Success Criteria

- [ ] Complete design document describing current architecture
- [ ] Capability specs for each major feature
- [ ] Clear configuration specification
- [ ] Documentation aligns with actual implementation in jirasync.py
- [ ] Foundation for future enhancement proposals

## Dependencies

None - this is baseline documentation.

## Risks

- Documentation may drift from implementation over time (mitigation: reference line numbers in code)
- May reveal undocumented edge cases or assumptions (actually a benefit)

## Timeline

This is documentation work, not implementation. Can be completed in a single session.
