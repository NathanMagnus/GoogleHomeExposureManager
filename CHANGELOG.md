# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflows for validation (HACS Action + Hassfest)
- GitHub Actions workflow for automated releases
- CONTRIBUTING.md with development guidelines and HACS submission checklist
- Unsaved changes confirmation dialog when switching tabs
- Browser beforeunload warning when leaving page with unsaved changes

### Changed
- Updated HACS badge link to point to hacs.xyz
- Added validation status badge to README
- Cleaned up hacs.json (removed plugin-only keys)
- Fixed placeholder URLs in README

## [0.1.0] - 2026-01-27

### ⚠️ Prerelease

This is an early prerelease version. Expect bugs and breaking changes.

### Added
- Initial release
- **Bulk Rules**: Expose entire domains, exclude areas, exclude by pattern
- **Individual Entity Overrides**: Always expose or never expose specific entities
- **Device Rules**: Control exposure for all entities from a device at once
- **Automatic Migration**: Import existing `entity_config` from Google Assistant configuration
- **Preview Changes**: See exactly what will be exposed before saving
- **Automatic Backups**: Creates timestamped backups before modifying files
- **Preserves Custom Config**: Keeps entity names, aliases, room hints, and other settings
- **Exclusion Priority**: Exclusions always win over inclusions at any level
- **Repair Issues**: Guides users through setup with actionable repair items
- French translations

### Technical
- Atomic file writes to prevent corruption
- Non-destructive uninstall (preserves configuration files)
- Graceful error handling that won't break Home Assistant startup
- Support for Home Assistant 2024.1.0+
