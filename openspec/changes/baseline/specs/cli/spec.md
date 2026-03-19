# Capability: Command-Line Interface

## Overview

Provides command-line interface for running Jira synchronization with configuration options and dry-run mode.

## Requirements

### FR-1: Command Structure
**Status**: Implemented (jirasync.py:244-252)

The CLI SHALL follow this format:
```bash
jirasync --config <path> --days <number> [--dry-run]
```

**Acceptance Criteria**:
- [x] Command accepts configuration file path
- [x] Command accepts lookback period in days
- [x] Command supports dry-run mode
- [x] Arguments are optional with sensible defaults

### FR-2: Arguments

#### --config
**Status**: Implemented

Specifies path to JSON configuration file.

| Aspect | Value |
|--------|-------|
| Required | No |
| Type | String (file path) |
| Default | None |
| Fallback | Environment variables + interactive prompts |

**Behavior**:
- If provided, loads config from file
- If not provided, falls back to env vars
- Missing credentials trigger interactive prompts

**Examples**:
```bash
# With config file
jirasync --config /path/to/config.json --days 90

# Without config (uses env vars)
export JIRA_EMAIL="user@company.com"
export JIRA_***REMOVED***_TOKEN="token"
jirasync --days 90
```

#### --days
**Status**: Implemented

Specifies how many days to look back for issues.

| Aspect | Value |
|--------|-------|
| Required | No |
| Type | Integer |
| Default | 90 |
| Valid Range | 1 to ? (no validation) |

**Behavior**:
- Generates JQL: `created >= -{days}d`
- Filters source issues by creation date
- Does not use `updated` date (no incremental sync)

**Examples**:
```bash
# Last 30 days
jirasync --config config.json --days 30

# Last year
jirasync --config config.json --days 365

# Default (90 days)
jirasync --config config.json
```

#### --dry-run
**Status**: Implemented

Runs validation without making changes.

| Aspect | Value |
|--------|-------|
| Required | No |
| Type | Flag (boolean) |
| Default | False |

**Behavior**:
- Validates connections to both Jira instances
- Fetches remote issues
- Does NOT call `sync_issues_to_local()`
- Does NOT create or update any issues
- Shows what would be synchronized

**Use Cases**:
- Testing credentials
- Validating configuration
- Previewing sync scope
- Troubleshooting

**Example**:
```bash
jirasync --config config.json --days 30 --dry-run
```

**Output**:
```
🔍 DRY RUN MODE: No changes will be made
🔍 Validating connection to acme-corp...
✅ Connected to acme-corp as Service User
🔍 Validating connection to mycompany...
✅ Connected to mycompany as Service User
🔎 Gevonden 42 issues in acme-corp
✅ Dry run completed successfully
```

### FR-3: Exit Codes
**Status**: Implemented

The CLI SHALL return appropriate exit codes:

| Exit Code | Meaning | Triggers |
|-----------|---------|----------|
| 0 | Success | Normal completion |
| 1 | Error | Config errors, connection failures, unexpected exceptions |

**Implementation** (jirasync.py):
- Line 22: Config file not found → exit(1)
- Line 25: Invalid JSON → exit(1)
- Line 36: Empty email → exit(1)
- Line 48: Empty token → exit(1)
- Line 99: ***REMOVED*** error → exit(1)
- Line 269: Connection validation failed → exit(1)
- Line 281: Keyboard interrupt → exit(1)
- Line 284: Unexpected error → exit(1)

### FR-4: Output Format
**Status**: Basic Implementation

The CLI SHALL provide user-friendly output:
- Emoji indicators for status (✅ ❌ 🔄 ➕ ⚠️ 🔍 🔎)
- Clear progress messages
- Error messages with context

**Current Output Types**:

#### Success Messages
```
✅ Loaded configuration from {file}
✅ Connected to {org} as {user}
✅ Aangemaakt: {key}
✅ Description updated for {key}
✅ Status gesynchroniseerd naar '{status}' voor {key}
✅ Synchronization completed successfully
✅ Dry run completed successfully
```

#### Progress Messages
```
🔄 Starting synchronization from {remote} to {local}...
📅 Looking back {days} days for issues
🔍 Validating connection to {org}...
🔍 DRY RUN MODE: No changes will be made
🔎 Gevonden {count} issues in {org}
🔄 Bijwerken: {local_key} (voor {remote_key})
➕ Aanmaken: nieuw issue voor {remote_key}
```

#### Warning Messages
```
Warning: JIRA_EMAIL not found in config or environment.
⚠️ Geen overgang beschikbaar naar '{status}' voor {key}
⚠️ Process interrupted by user
```

#### Error Messages
```
❌ Config file not found: {path}
❌ Invalid JSON in config file: {error}
❌ Failed to connect to {org}: {error}
❌ Connection validation failed. Exiting.
❌ Status-sync fout: {code} {text}
❌ Error synchronizing status for {key}: {error}
❌ Missing data in response when synchronizing status for {key}: {error}
❌ Unexpected error: {error}
```

**Language**: Mixed Dutch/English (inconsistent)

### FR-5: Error Handling
**Status**: Implemented

The CLI SHALL handle errors gracefully:

#### Keyboard Interrupt
```python
except KeyboardInterrupt:
    print("\n⚠️ Process interrupted by user")
    sys.exit(1)
```

#### Expected Errors
- Config file errors → Clear message + exit
- Connection errors → Clear message + exit
- ***REMOVED*** errors during sync → Print error + continue

#### Unexpected Errors
```python
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
```

## Command-Line Help

### Current Help Output
```bash
jirasync --help
```

**Expected Output**:
```
usage: jirasync.py [-h] [--config CONFIG] [--days DAYS] [--dry-run]

Synchronize Jira issues between organizations

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  Path to JSON configuration file
  --days DAYS      Number of days to look back for issues (default: 90)
  --dry-run        Only show what would be done, without making changes
```

## Usage Examples

### Basic Usage
```bash
# Sync last 90 days (default)
jirasync --config /etc/jirasync/config.json

# Sync specific timeframe
jirasync --config config.json --days 30
jirasync --config config.json --days 180
```

### Testing
```bash
# Test configuration
jirasync --config config.json --days 7 --dry-run

# Test credentials without config file
export JIRA_EMAIL="test@company.com"
export JIRA_***REMOVED***_TOKEN="test-token"
jirasync --days 1 --dry-run
```

### Interactive Mode
```bash
# Prompt for credentials
jirasync --days 30
# Will prompt for email and token
```

### Integration
```bash
# In NixOS systemd service
ExecStart=${jirasyncPackage}/bin/jirasync \
  --config /run/agenix/jirasync-config.json \
  --days 90

# In cron job
0 */6 * * * /usr/bin/jirasync --config /etc/jirasync/config.json --days 90

# In CI/CD
jirasync --config $CONFIG_FILE --days 7 --dry-run
if [ $? -eq 0 ]; then
  echo "Dry run successful"
else
  echo "Dry run failed"
  exit 1
fi
```

## Non-Functional Requirements

### NFR-1: Usability
**Status**: Partial

**Current State**:
- [x] Clear argument names
- [x] Sensible defaults
- [x] Help text available
- [ ] Language consistency (mixed Dutch/English)
- [ ] No examples in --help output
- [ ] No verbose/quiet modes

### NFR-2: Documentation
**Status**: Partial

**Current State**:
- [x] Argument descriptions in help
- [x] Example in CLAUDE.md
- [ ] No man page
- [ ] No --version flag
- [ ] No detailed usage guide

### NFR-3: Logging
**Status**: Basic

**Current State**:
- [x] Console output
- [ ] No log files
- [ ] No log levels
- [ ] No structured logging (JSON)
- [ ] No quiet mode
- [ ] No verbose mode

## Future Enhancements

### Version Information
```bash
jirasync --version
# jirasync v1.2.3
```

### Verbose Mode
```bash
jirasync --config config.json --days 30 --verbose
# Show detailed ***REMOVED*** calls, request/response info
```

### Quiet Mode
```bash
jirasync --config config.json --days 30 --quiet
# Only show errors
```

### Log File Output
```bash
jirasync --config config.json --days 30 --log /var/log/jirasync.log
```

### Structured Logging
```bash
jirasync --config config.json --days 30 --format json > sync.log
# {"level":"info","msg":"Connected to acme-corp","user":"Service User"}
```

### Configuration Validation
```bash
jirasync --config config.json --validate
# Validate configuration without running sync
```

### Status Output
```bash
jirasync --config config.json --days 30 --status
# Show sync status at end:
# ✅ Issues fetched: 42
# ✅ Issues created: 5
# ✅ Issues updated: 37
# ⚠️ Errors: 2
```

### Board ID Filtering
```bash
jirasync --config config.json --days 30 --source-board 123 --target-board 456
# Override board IDs from command line
```

### Multiple Configs
```bash
jirasync --config client1.json client2.json --days 30
# Sync from multiple sources
```

### Progress Bar
```bash
jirasync --config config.json --days 30 --progress
# [=====>    ] 42/100 issues synced
```

## Compatibility

### Python Version
**Minimum**: Python 3.x (not specified exactly)
**Recommended**: Python 3.8+

### Shebang
```python
#!/usr/bin/env python3
```

Uses `env` for portability across systems.

### Platform Support
- ✅ Linux
- ✅ macOS
- ✅ Windows (should work but not tested)

### Nix Integration
When packaged with Nix:
```bash
# Run via Nix
nix run github:wearetechnative/jirasync -- --config config.json --days 90

# Install to profile
nix profile install github:wearetechnative/jirasync
jirasync --config config.json --days 90
```

## Testing

### Manual Testing
```bash
# Test help output
jirasync --help

# Test dry-run
jirasync --config test-config.json --days 1 --dry-run

# Test with env vars
export JIRA_EMAIL="test@example.com"
export JIRA_***REMOVED***_TOKEN="fake-token"
jirasync --days 1 --dry-run

# Test error handling
jirasync --config nonexistent.json  # Should show clear error
jirasync --config malformed.json    # Should show JSON parse error
```

### Automated Testing
**Proposed**:
```python
# Test argument parsing
def test_parse_args_defaults():
    args = parse_args(['--config', 'test.json'])
    assert args.config == 'test.json'
    assert args.days == 90
    assert args.dry_run == False

def test_parse_args_custom():
    args = parse_args(['--config', 'test.json', '--days', '30', '--dry-run'])
    assert args.days == 30
    assert args.dry_run == True

# Test exit codes
def test_exit_code_success():
    result = subprocess.run(['jirasync', '--help'], capture_output=True)
    assert result.returncode == 0

def test_exit_code_error():
    result = subprocess.run(['jirasync', '--config', 'nonexistent.json'])
    assert result.returncode == 1
```

## Localization

**Current State**: Mixed Dutch/English

**Issues**:
- Console messages use Dutch ("Gevonden", "Aanmaken", "Bijwerken")
- Code comments use Dutch ("STAP 1", "Haal issues op")
- Error messages use English
- Argument help uses English

**Recommendation**:
- Standardize on English for all user-facing output
- Keep Dutch for internal comments if preferred
- Consider i18n framework for future localization
