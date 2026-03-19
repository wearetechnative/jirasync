# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-13

### Added
- Initial release of jirasync
- One-way synchronization from client/remote Jira boards to organization Jira boards
- Support for configurable sync intervals via systemd timers
- Dry-run mode for testing configurations
- Age-encrypted configuration file support
- Multi-instance support for syncing multiple boards
- Python script with requests library for Jira REST ***REMOVED*** interactions
- Configuration via JSON file with clear source/target separation:
  - `source_jira_url`, `source_project_key`, `source_board_id`
  - `target_jira_url`, `target_jira_user`, `target_jira_token`, `target_project_key`, `target_board_id`

### Documentation
- Complete service documentation for Elastinix integration
- ***REMOVED*** token setup instructions
- Required permissions documentation for source and target boards
- Configuration examples with fictional company names (acme-corp, mycompany)
- Troubleshooting guide

[Unreleased]: https://github.com/wearetechnative/jirasync/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/wearetechnative/jirasync/releases/tag/v1.0.0
