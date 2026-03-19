# Claude Context: Jirasync Development

This document provides context for AI assistants working on the jirasync project. It captures key decisions, architecture, and implementation details.

## Project Overview

Jirasync is a Python-based tool for **one-way synchronization** of Jira issues from client/remote boards to your organization's boards. It enables better DevOps and Agile workflows when working with external clients who have their own Jira instances.

**Repository**: https://github.com/wearetechnative/jirasync

### Key Characteristics

- **One-way sync**: Client board → Organization board (NOT bidirectional)
- **Single ***REMOVED*** token**: Uses one token from target organization user
- **Clear separation**: Distinct source (client) and target (organization) configuration
- **NixOS integration**: Packaged as a Nix flake for use in Elastinix

## Use Case

When working with external clients who maintain their own Jira instances, development teams need visibility into client issues within their own workflow. Jirasync solves this by:

1. Reading issues from client's Jira board (source)
2. Creating/updating corresponding issues in organization's board (target)
3. Maintaining status synchronization via configurable mapping
4. Running on scheduled intervals (via systemd timers in NixOS)

**Important**: Changes made in your organization's board are **NOT** synced back to the client.

## Architecture

### Authentication Model

```
┌─────────────────────────────────────────────────┐
│ Target Organization (Your Company)              │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Service User                             │  │
│  │ (jirasync-service@your-company.com)      │  │
│  │                                          │  │
│  │ • Has ***REMOVED*** token                          │  │
│  │ • Has write access to target board      │  │
│  │ • Has read access to client board ───────┼──┼─┐
│  └──────────────────────────────────────────┘  │  │
│                                                 │  │
│  Target Jira Board                              │  │
│  (Where issues are synced TO)                   │  │
└─────────────────────────────────────────────────┘  │
                                                     │
                                                     │
┌────────────────────────────────────────────────────┼┐
│ Source Organization (Client)                       ││
│                                                     ││
│  Client Jira Board                                 ││
│  (Where issues are synced FROM)                    ││
│                                                     ││
│  • Service user has read-only access ◄─────────────┘│
│  • Client grants access to your user                │
└─────────────────────────────────────────────────────┘
```

**Key Point**: Only ONE ***REMOVED*** token is needed - from your organization. The client must grant your service user read access to their board.

## Configuration

### JSON Configuration File

The configuration uses clear `source_` and `target_` prefixes to distinguish between client (read from) and organization (write to) settings.

```json
{
  "source_jira_url": "https://client-company.atlassian.net",
  "source_project_key": "CLIENT",
  "source_board_id": 123,
  "target_jira_url": "https://your-company.atlassian.net",
  "target_jira_user": "jirasync-service@your-company.com",
  "target_jira_token": "ATATT3xFfGF0...",
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

### Field Descriptions

**Source Configuration (Client - Read From)**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_jira_url` | string | Yes | Full URL to client's Jira instance |
| `source_project_key` | string | Yes | Project key in client's Jira |
| `source_board_id` | integer | Optional | Specific board ID to sync from |

**Target Configuration (Organization - Write To)**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_jira_url` | string | Yes | Full URL to your organization's Jira |
| `target_jira_user` | string | Yes | Email of service user in your org |
| `target_jira_token` | string | Yes | ***REMOVED*** token for the service user |
| `target_project_key` | string | Yes | Project key in your organization |
| `target_board_id` | integer | Optional | Target board ID in your Jira |

**Sync Configuration**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status_mapping` | object | Optional | Maps source statuses to target statuses |

### Configuration Evolution

**Current Support**: As of v1.1.0, jirasync supports both old and new configuration formats with automatic detection. The old format is deprecated and will be removed in v2.0.0.

#### Old Format (Deprecated - Still Supported)
```json
{
  "email": "user@company.com",
  "api_token": "token",
  "remote_org": "client-org",      // Just org name
  "local_org": "your-org",         // Just org name
  "project_key": "PROJ"            // Ambiguous which project
}
```

**Note**: When using old format, a deprecation warning will be displayed. The script automatically converts old format to new format internally.

#### New Format (Recommended)
```json
{
  "source_jira_url": "https://client-org.atlassian.net",  // Full URL
  "source_project_key": "CLIENT",                         // Clear: source
  "target_jira_url": "https://your-org.atlassian.net",   // Full URL
  "target_jira_user": "user@company.com",                 // Clear: target
  "target_jira_token": "token",                           // Clear: target
  "target_project_key": "INT"                             // Clear: target
}
```

**Benefits of New Format**:
- ✅ Clear source vs target distinction
- ✅ Full URLs instead of just org names
- ✅ Explicit about which credentials belong where
- ✅ Supports different project keys for source/target
- ✅ Board ID support for more precise syncing

### Format Detection and Conversion

The script automatically detects which format is being used:
- **Detection**: Checks for presence of `source_jira_url` field
  - Present → new format (no conversion needed)
  - Absent → old format (converts to new format internally)
- **Conversion**: Old format is automatically converted to new format at load time
- **Warning**: Deprecation warning is displayed when old format is detected
- **Backward compatibility**: Both formats work identically after conversion

## Python Script

### Command-Line Interface

```bash
jirasync --config <path> --days <number> [--dry-run]
```

**Arguments**:
- `--config` (required): Path to JSON configuration file
- `--days` (required): Number of days to look back for issues
- `--dry-run` (optional): Run without making actual changes

**Example**:
```bash
# Normal sync of last 90 days
jirasync --config /path/to/config.json --days 90

# Dry-run test
jirasync --config /path/to/config.json --days 30 --dry-run
```

### Dependencies

The script requires:
- Python 3.x
- `requests` library for HTTP/REST ***REMOVED*** calls
- `json` for configuration parsing
- `argparse` for CLI argument handling

### Script Structure

```python
# Key components:
1. Configuration loading (JSON)
2. Jira ***REMOVED*** authentication (HTTPBasicAuth)
3. Source issue fetching (GET /rest/api/3/search)
4. Status mapping logic
5. Target issue creation/update (POST/PUT /rest/api/3/issue)
6. Error handling and logging
```

### Migration Notes

If updating from old field names to new:

```python
# OLD (deprecated)
config['remote_org']  # → source_jira_url (extract org name)
config['local_org']   # → target_jira_url (extract org name)
config['email']       # → target_jira_user
config['api_token']   # → target_jira_token
config['project_key'] # → source_project_key

# NEW (current)
config['source_jira_url']
config['source_project_key']
config['target_jira_url']
config['target_jira_user']
config['target_jira_token']
config['target_project_key']
```

## Nix Flake Integration

### Flake Structure

The jirasync repository is a Nix flake that provides:

1. **Package**: The jirasync executable with Python wrapper
2. **App**: Runnable application via `nix run`
3. **Dev Shell**: Development environment with Python dependencies

### flake.nix Overview

```nix
{
  description = "Jira synchronization tool...";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [ requests ]);

        jirasync = pkgs.stdenv.mkDerivation {
          # Package definition
        };
      in {
        packages.default = jirasync;
        apps.default = { /* ... */ };
        devShells.default = pkgs.mkShell { /* ... */ };
      }
    );
}
```

### Package Build Process

```nix
jirasync = pkgs.stdenv.mkDerivation {
  pname = "jirasync";
  version = "1.0.0";

  src = ./.;  # Current directory

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    # Copy Python script
    mkdir -p $out/share/jirasync
    cp jirasync.py $out/share/jirasync/

    # Create wrapper with Python environment
    makeWrapper ${pythonEnv}/bin/python3 $out/bin/jirasync \
      --add-flags "$out/share/jirasync/jirasync.py"
  '';
};
```

**What this does**:
1. Copies `jirasync.py` to Nix store
2. Creates a wrapper script at `/nix/store/.../bin/jirasync`
3. Wrapper automatically uses the correct Python environment with requests
4. Users can run `jirasync` without worrying about Python dependencies

### Multi-Platform Support

Uses `flake-utils.lib.eachDefaultSystem` to support:
- `x86_64-linux`
- `aarch64-linux`
- `x86_64-darwin`
- `aarch64-darwin`

### Development Shell

```bash
# Enter development environment
nix develop

# Python and requests library are available
python3 jirasync.py --help
```

## Integration with Elastinix

Jirasync is consumed by Elastinix as a flake input:

```nix
# In elastinix/flake.nix
inputs = {
  jirasync.url = "github:wearetechnative/jirasync";
  jirasync.inputs.nixpkgs.follows = "nixpkgs";
};
```

The Elastinix service module then uses:
```nix
jirasyncPackage = inputs.jirasync.packages.${pkgs.system}.default;
```

**Benefits**:
- Elastinix automatically gets updates when jirasync is updated
- No manual hash management
- Consistent nixpkgs version via "follows"
- Users can override jirasync version in their flake

## Versioning

### VERSION File
```
1.0.0
```

Single line with semantic version number.

### CHANGELOG.md

Follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]
- Future changes

## [1.0.0] - 2026-03-13
### Added
- Initial release
- One-way sync functionality
- Configuration file support
```

### Semantic Versioning

- **MAJOR**: Breaking changes (config format, CLI arguments)
- **MINOR**: New features (status mapping, new fields)
- **PATCH**: Bug fixes, documentation

### Release Process

1. Update CHANGELOG.md with new version and date
2. Update VERSION file
3. Update version in flake.nix if needed
4. Commit: `git commit -m "Release v1.1.0"`
5. Tag: `git tag v1.1.0`
6. Push: `git push && git push --tags`
7. Elastinix users run: `nix flake update jirasync`

## Testing

### Local Testing

```bash
# Test the Python script directly
python3 jirasync.py --config config.example.json --days 30 --dry-run

# Test via Nix package
nix run . -- --config config.example.json --days 30 --dry-run

# Build the package
nix build
./result/bin/jirasync --help
```

### Example Configuration

Use `config.example.json` for testing (with fake credentials):
- Never commit real ***REMOVED*** tokens
- Use dry-run mode for initial testing
- Start with small day ranges (7-30 days)

### Integration Testing

When testing with Elastinix:

```bash
# In elastinix repository
cd /path/to/elastinix

# Update to latest jirasync
nix flake update jirasync

# Build configuration
nix build .#packages.x86_64-linux.prodApply

# Check generated systemd service
systemctl cat jirasync-<instance>.service

# Manual test run
systemctl start jirasync-<instance>.service
journalctl -u jirasync-<instance>.service -f
```

## Security Considerations

### ***REMOVED*** Token Security

- **Never commit tokens**: Use `.gitignore` for config files with real tokens
- **Encrypt at rest**: Use agenix in NixOS deployments
- **Rotate regularly**: Change tokens every 90 days minimum
- **Service accounts**: Use dedicated accounts, not personal tokens
- **Least privilege**: Grant only required permissions

### Required Jira Permissions

**Source (Client) Board**:
- Browse Projects (read issues)
- View Development Tools (optional, for board info)

**Target (Organization) Board**:
- Browse Projects
- Create Issues
- Edit Issues
- Assign Issues (if syncing assignees)
- Transition Issues (if syncing status)
- Add Comments (if syncing comments)

### Network Security

- Uses HTTPS for all ***REMOVED*** calls
- Supports proxy configuration (if needed)
- No sensitive data logged (tokens are redacted)

## Common Issues

### Issue: Authentication Failed
**Symptom**: 401 Unauthorized errors
**Causes**:
- Incorrect email/token combination
- Token expired
- User doesn't have access to boards
**Solutions**:
- Verify email matches token owner
- Generate new token
- Check user has been invited to client's Jira

### Issue: Permission Denied
**Symptom**: 403 Forbidden errors
**Causes**:
- Missing required permissions
- IP allowlist restrictions
- Security policies blocking access
**Solutions**:
- Verify user has required permissions on both boards
- Check IP allowlist with client
- Review security policies

### Issue: Issues Not Syncing
**Symptom**: Script runs but issues don't appear
**Causes**:
- Wrong project keys
- Board IDs incorrect
- Status mapping mismatch
**Solutions**:
- Verify project keys in both Jira instances
- Check board IDs are correct
- Review status mapping configuration

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Handle errors gracefully

### Configuration Changes
- Always maintain backward compatibility when possible
- Document breaking changes in CHANGELOG
- Update example configuration files
- Update Elastinix documentation

### Adding Features
1. Update Python script
2. Add/modify configuration fields
3. Update `config.example.json`
4. Update CHANGELOG.md
5. Update this CLAUDE.md
6. Update Elastinix documentation if needed
7. Bump version appropriately
8. Test thoroughly

## Future Enhancements

### Potential Features
- **Bidirectional sync**: Two-way synchronization (requires careful conflict resolution)
- **Incremental sync**: Only sync changed issues (requires state tracking)
- **Custom field mapping**: Map custom fields between instances
- **Attachment sync**: Copy issue attachments
- **Comment sync**: Sync comments between issues
- **Webhook support**: Real-time sync via webhooks
- **Multiple boards**: Sync from multiple source boards to one target
- **Filtering**: Sync only issues matching certain criteria
- **Metrics**: Export sync statistics and metrics

### Architecture Improvements
- Add logging levels (DEBUG, INFO, WARN, ERROR)
- Implement state persistence (track synced issues)
- Add retry logic with exponential backoff
- Support for Jira Server/Data Center (not just Cloud)
- Configuration validation on startup
- Health check endpoint for monitoring

## Related Documentation

- [Elastinix CLAUDE.md](https://github.com/wearetechnative/elastinix/blob/main/CLAUDE.md)
- [Elastinix Service Documentation](https://github.com/wearetechnative/elastinix/blob/main/docs/services/jirasync.md)
- [Jira REST ***REMOVED*** Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

## File Structure

```
jirasync/
├── jirasync.py              # Main Python script
├── flake.nix                # Nix flake definition
├── config.example.json      # Example configuration
├── VERSION                  # Current version number
├── CHANGELOG.md            # Version history and changes
├── CLAUDE.md               # This file - AI assistant context
├── README.md               # User-facing documentation (to be created)
└── .gitignore              # Git ignore rules (tokens, etc.)
```

## Changelog

### 2026-03-13
- Initial project setup
- Python script implementation
- Nix flake packaging
- Configuration structure with source/target prefixes
- Integration with Elastinix as flake input
- Documentation created

---

**Note**: Keep this document updated as the project evolves. Document major architectural decisions and breaking changes.
