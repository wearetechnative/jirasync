# Capability: Nix Packaging

## Overview

Packages jirasync as a Nix flake for reproducible builds, cross-platform support, and integration with NixOS systems and Elastinix.

## Requirements

### FR-1: Flake Structure
**Status**: Implemented (flake.nix)

The flake SHALL provide:
- Package output (`packages.default` and `packages.jirasync`)
- App output (`apps.default`)
- Development shell (`devShells.default`)
- Cross-platform support via `flake-utils.lib.eachDefaultSystem`

**Acceptance Criteria**:
- [x] Flake is valid and evaluates
- [x] Package builds successfully
- [x] App runs correctly
- [x] Dev shell provides Python + dependencies
- [x] Multi-platform support

### FR-2: Package Build
**Status**: Implemented (flake.nix:18-45)

The package SHALL:
- Copy `jirasync.py` to Nix store
- Create executable wrapper at `$out/bin/jirasync`
- Bundle Python environment with `requests` library
- Set appropriate permissions

**Build Process**:
```nix
jirasync = pkgs.stdenv.mkDerivation {
  pname = "jirasync";
  version = "1.0.0";

  src = ./.;  # Current directory

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/share/jirasync
    cp jirasync.py $out/share/jirasync/
    chmod +x $out/share/jirasync/jirasync.py

    makeWrapper ${pythonEnv}/bin/python3 $out/bin/jirasync \
      --add-flags "$out/share/jirasync/jirasync.py"
  '';
};
```

**Output Structure**:
```
/nix/store/{hash}-jirasync-1.0.0/
├── bin/
│   └── jirasync                    # Wrapper script
└── share/
    └── jirasync/
        └── jirasync.py             # Python script
```

### FR-3: Python Environment
**Status**: Implemented (flake.nix:14-16)

The Python environment SHALL include:
- Python 3.x
- `requests` library

```nix
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  requests
]);
```

**Acceptance Criteria**:
- [x] Python 3 available
- [x] Requests library included
- [ ] Version pinning (uses whatever nixpkgs provides)

### FR-4: Wrapper Script
**Status**: Implemented (flake.nix:34-35)

The wrapper SHALL:
- Invoke Python 3 from the Python environment
- Pass script path as argument
- Preserve all user-provided arguments

```nix
makeWrapper ${pythonEnv}/bin/python3 $out/bin/jirasync \
  --add-flags "$out/share/jirasync/jirasync.py"
```

**Invocation**:
```bash
jirasync --config config.json --days 90
# Translates to:
# /nix/store/{hash}-python3/bin/python3 \
#   /nix/store/{hash}-jirasync/share/jirasync/jirasync.py \
#   --config config.json --days 90
```

### FR-5: Metadata
**Status**: Implemented (flake.nix:38-44)

The package SHALL include metadata:

```nix
meta = with pkgs.lib; {
  description = "One-way Jira synchronization tool";
  homepage = "https://github.com/wearetechnative/jirasync";
  license = licenses.mit;
  platforms = platforms.linux;
  maintainers = [ ];
};
```

**Issues**:
- [ ] `platforms = platforms.linux` is too restrictive (should support macOS)
- [ ] `maintainers = [ ]` is empty
- [ ] No LICENSE file in repository to match MIT declaration

### FR-6: Development Shell
**Status**: Implemented (flake.nix:61-65)

The dev shell SHALL provide:
- Python 3
- Requests library
- Same environment as the package

```nix
devShells.default = pkgs.mkShell {
  buildInputs = [
    pythonEnv
  ];
};
```

**Usage**:
```bash
nix develop
python3 jirasync.py --help
```

### FR-7: Flake App
**Status**: Implemented (flake.nix:53-58)

The app SHALL be runnable via `nix run`:

```nix
apps.default = {
  type = "app";
  program = "${jirasync}/bin/jirasync";
};
```

**Usage**:
```bash
# Run from local directory
nix run . -- --config config.json --days 90

# Run from GitHub
nix run github:wearetechnative/jirasync -- --config config.json --days 90
```

## Flake Inputs

### nixpkgs
**Status**: Implemented (flake.nix:5)

```nix
nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
```

**Version**: nixos-25.11 (stable channel)

**Considerations**:
- Uses stable channel for reliability
- Could use nixos-unstable for newer packages
- Version can be overridden by consumers (e.g., Elastinix)

### flake-utils
**Status**: Implemented (flake.nix:6)

```nix
flake-utils.url = "github:numtide/flake-utils";
```

**Purpose**: Provides `eachDefaultSystem` for multi-platform support

**Platforms Supported**:
- x86_64-linux
- aarch64-linux
- x86_64-darwin
- aarch64-darwin

⚠️ **Conflict**: `meta.platforms = platforms.linux` contradicts multi-platform flake-utils usage

## Integration with Elastinix

### Flake Input
Elastinix consumes jirasync as a flake input:

```nix
# In elastinix/flake.nix
inputs = {
  jirasync.url = "github:wearetechnative/jirasync";
  jirasync.inputs.nixpkgs.follows = "nixpkgs";
};
```

**Benefits**:
- `follows` ensures consistent nixpkgs version
- Automatic updates when jirasync is updated
- No manual hash management
- Transitive dependency resolution

### Package Usage
Elastinix uses the jirasync package:

```nix
jirasyncPackage = inputs.jirasync.packages.${pkgs.system}.default;
```

**In NixOS Service Module**:
```nix
ExecStart = "${jirasyncPackage}/bin/jirasync --config ${configFile} --days ${days}";
```

## Build and Installation

### Build Package
```bash
# Build locally
nix build

# Check result
./result/bin/jirasync --help

# Inspect what files are in the package
ls -la result/
ls -la result/bin/
ls -la result/share/jirasync/
```

### Install to Profile
```bash
# Install from local directory
nix profile install .

# Install from GitHub
nix profile install github:wearetechnative/jirasync

# Use directly
jirasync --config config.json --days 90
```

### Run Without Installing
```bash
# Run directly
nix run github:wearetechnative/jirasync -- --config config.json --days 90

# Development iteration
nix run . -- --config config.json --days 30 --dry-run
```

## Versioning

### Current Version
**flake.nix:20**: `version = "1.0.0";`

### Version Sources
1. `flake.nix` - Hardcoded version string
2. `VERSION` file - Single-line version number
3. Git tags - Not currently used

**Inconsistency Risk**: Version must be manually updated in multiple places.

### Recommended Approach
Read version from VERSION file:

```nix
version = builtins.readFile ./VERSION;
# OR
version = pkgs.lib.strings.trim (builtins.readFile ./VERSION);
```

**Benefits**:
- Single source of truth
- Matches git tags
- Consistent with CHANGELOG.md

## Reproducibility

### Source Handling
```nix
src = ./.;  # Current directory
```

**What's Included**:
- All files in repository (except .git)
- Respects .gitignore? **No** - Nix includes everything

**Potential Issues**:
- Build artifacts included if present
- Local config files included
- .venv or __pycache__ directories

**Recommended**: Add `src` filtering:
```nix
src = pkgs.lib.cleanSource ./.;
# OR
src = pkgs.lib.sourceByRegex ./. [
  "^jirasync\.py$"
  "^VERSION$"
];
```

### Dependency Pinning
**Current State**:
- nixpkgs version pinned via flake.lock
- Python 3 version: whatever nixpkgs provides
- requests version: whatever nixpkgs provides

**Implications**:
- ✅ Reproducible given same flake.lock
- ✅ Updates controlled via `nix flake update`
- ❌ No control over Python package versions
- ❌ Breaking changes in requests could occur

## Multi-Platform Support

### Supported Platforms
Via `flake-utils.lib.eachDefaultSystem`:
- x86_64-linux
- aarch64-linux
- x86_64-darwin
- aarch64-darwin

### Platform Metadata Mismatch
```nix
meta.platforms = platforms.linux;  # Too restrictive!
```

**Should be**:
```nix
meta.platforms = platforms.unix;
# OR
meta.platforms = platforms.linux ++ platforms.darwin;
```

### Testing Multi-Platform
```bash
# Check package on different systems
nix flake show

# Build for specific platform
nix build .#packages.x86_64-linux.default
nix build .#packages.aarch64-darwin.default
```

## Testing

### Flake Checks
**Status**: Not Implemented

**Proposed**:
```nix
checks = {
  # Validate flake evaluates
  flake-eval = pkgs.runCommand "flake-eval" {} ''
    echo "Flake evaluates successfully"
    touch $out
  '';

  # Test package builds
  package-builds = jirasync;

  # Test basic functionality
  basic-help = pkgs.runCommand "test-help" {} ''
    ${jirasync}/bin/jirasync --help > $out
    grep -q "Synchronize Jira issues" $out
  '';
};
```

### Development Testing
```bash
# Enter dev shell
nix develop

# Test script directly
python3 jirasync.py --help

# Test with sample config
python3 jirasync.py --config config.example.json --days 1 --dry-run
```

### Package Testing
```bash
# Build and test
nix build
./result/bin/jirasync --help

# Test in isolation
nix run . -- --help

# Test with actual config
nix run . -- --config /path/to/config.json --days 7 --dry-run
```

## Security

### Source Integrity
- Flake provides content-addressed builds
- Git repository determines source
- flake.lock pins exact revisions

### Dependency Security
- nixpkgs provides vetted packages
- Python packages from nixpkgs (not PyPI directly)
- Updates controlled, not automatic

### Secrets Handling
**Package does NOT**:
- Include secrets
- Reference config files with secrets
- Expose tokens in build

**Deployment (NixOS/Elastinix)**:
- Secrets managed via agenix
- Config files generated at runtime
- Tokens never in Nix store

## Future Enhancements

### Version from Git
```nix
version = self.rev or "dirty";
# OR use git describe
version = builtins.readFile (pkgs.runCommand "version" {} ''
  cd ${./.}
  ${pkgs.git}/bin/git describe --tags > $out
'');
```

### Source Filtering
```nix
src = pkgs.lib.cleanSourceWith {
  src = ./.;
  filter = path: type:
    let baseName = baseNameOf path;
    in !(builtins.elem baseName [
      ".git" "result" ".venv" "__pycache__"
      ".claude" ".opencode" "openspec"
    ]);
};
```

### Flake Checks
Add automated tests:
```nix
checks = {
  package-builds = jirasync;
  help-text = /* test --help works */;
  dry-run = /* test dry-run mode */;
};
```

### NixOS Module
Provide a NixOS module in the flake:
```nix
nixosModules.default = { config, lib, pkgs, ... }: {
  options.services.jirasync = { /* ... */ };
  config = lib.mkIf config.services.jirasync.enable { /* ... */ };
};
```

### License File
Add LICENSE file to match `meta.license = licenses.mit`

### Update Script
```nix
passthru.updateScript = pkgs.writeShellScript "update.sh" ''
  # Auto-update logic
'';
```

## Dependencies Graph

```
jirasync flake
    │
    ├─► nixpkgs (nixos-25.11)
    │     │
    │     ├─► python3
    │     │     └─► requests
    │     │
    │     └─► stdenv, makeWrapper
    │
    └─► flake-utils
          └─► eachDefaultSystem
```

## Common Issues

### Issue: Package Not Found
**Symptom**: `nix build` fails with "attribute not found"

**Causes**:
- Flake not evaluated correctly
- Wrong attribute path

**Solutions**:
```bash
nix flake show  # See available outputs
nix build .#packages.x86_64-linux.default
```

### Issue: Python Import Error
**Symptom**: `ModuleNotFoundError: No module named 'requests'`

**Causes**:
- Python environment not set up correctly
- Wrapper not working

**Solutions**:
- Check wrapper is using correct Python
- Verify pythonEnv includes requests

### Issue: Permission Denied
**Symptom**: Cannot execute jirasync

**Causes**:
- Script not marked executable

**Solutions**:
```nix
chmod +x $out/share/jirasync/jirasync.py  # In installPhase
```

### Issue: Version Mismatch
**Symptom**: `jirasync --version` shows wrong version

**Causes**:
- Version not implemented in CLI
- flake.nix version hardcoded

**Solutions**:
- Implement --version flag
- Read from VERSION file

## Integration Examples

### Direct Usage
```bash
nix run github:wearetechnative/jirasync -- \
  --config config.json \
  --days 90
```

### NixOS System
```nix
{ inputs, ... }:
{
  systemd.services.jirasync = {
    script = ''
      ${inputs.jirasync.packages.${pkgs.system}.default}/bin/jirasync \
        --config /run/agenix/jirasync.json \
        --days 90
    '';
  };
}
```

### Home Manager
```nix
{ inputs, pkgs, ... }:
{
  home.packages = [
    inputs.jirasync.packages.${pkgs.system}.default
  ];
}
```

### Development
```nix
{
  inputs.jirasync.url = "github:wearetechnative/jirasync";

  outputs = { self, nixpkgs, jirasync }: {
    devShells.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      buildInputs = [
        jirasync.packages.x86_64-linux.default
      ];
    };
  };
}
```
