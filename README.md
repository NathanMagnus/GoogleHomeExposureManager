# Google Home Exposure Manager

<p align="center">
  <img src="logo.svg" alt="Google Home Exposure Manager Logo" width="128" height="128">
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Badge"></a>
  <a href="https://github.com/NathanMagnus/GoogleHomeExposureManager/releases"><img src="https://img.shields.io/github/release/NathanMagnus/GoogleHomeExposureManager.svg" alt="GitHub Release"></a>
  <a href="https://github.com/NathanMagnus/GoogleHomeExposureManager/blob/main/LICENSE"><img src="https://img.shields.io/github/license/NathanMagnus/GoogleHomeExposureManager.svg" alt="License"></a>
  <a href="https://github.com/NathanMagnus/GoogleHomeExposureManager/actions/workflows/ci.yml"><img src="https://github.com/NathanMagnus/GoogleHomeExposureManager/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

> ⚠️ **Notice:** This integration was 100% vibe coded with AI assistance. While it includes safety features like automatic backups and atomic writes, it has not been extensively tested in production environments. **Use at your own risk.** Always maintain backups of your Home Assistant configuration.

> ⚠️ **Prerequisite:** This integration requires the **[Manual Google Assistant Integration](https://www.home-assistant.io/integrations/google_assistant/)** to be set up first. This is a core Home Assistant integration ([source code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/google_assistant)) that connects your Home Assistant to Google Home. This HACS integration provides a **UI to manage which entities are exposed** — it does not replace the Google Assistant integration itself.

A Home Assistant custom integration providing a UI to control which entities are exposed to the [manual Google Assistant integration](https://www.home-assistant.io/integrations/google_assistant/), featuring automatic migration of existing configs, bulk rules, individual overrides, and preview before saving.

## Features

- 🔄 **Automatic Migration** - Imports your existing `entity_config` from any Google Assistant config file
- 🎯 **Bulk Rules** - Expose entire domains, exclude areas, or use wildcard patterns
- 🔧 **Individual Overrides** - Fine-tune exposure for specific entities
- 📱 **Device Rules** - Control exposure for all entities from a device at once
- 🏷️ **Aliases & Custom Names** - Set custom names and aliases for voice control
- 👀 **Preview Changes** - See exactly what will be exposed before saving
- 💾 **Automatic Backups** - Creates timestamped backups before modifying files
- ✅ **Preserves Custom Config** - Keeps your entity names, aliases, and other settings

## Screenshots

<!-- TODO: Add screenshots after UI is finalized -->
*Screenshots coming soon - the integration provides a sidebar panel for managing entity exposure.*

### Planned Features

- 🔄 **Auto-Sync** - Automatic Google Assistant sync after changes (requires complex Google Cloud setup - for now, say "Hey Google, sync my devices")

## Safety & Reliability

This integration is designed to be safe for use on production Home Assistant instances:

- ✅ **Automatic Backups** - Always creates backups before modifying any existing files
- ✅ **Atomic Writes** - Uses temporary files to prevent corruption if writes are interrupted
- ✅ **Non-Destructive** - Removing the integration preserves all configuration files
- ✅ **Graceful Failures** - Errors don't break Home Assistant startup
- ✅ **Preserves Settings** - Entity names, aliases, and other Google Assistant settings are preserved
- ✅ **Preview Before Save** - Review changes before they're applied

All backups are stored in `config/backups/google_home_exposure_manager/` with timestamps.

## Requirements

- **Home Assistant Core 2024.1.0 or later**
- **[Manual Google Assistant Integration](https://www.home-assistant.io/integrations/google_assistant/)** — must be set up and working first

## Prerequisites

⚠️ **You must set up the Google Assistant integration before using this tool.**

This HACS integration is a **management UI** for the manual Google Assistant integration. It helps you control which entities are exposed to Google Home — but the underlying Google Assistant integration must already be configured and working.

### Required: Google Assistant Integration Setup

1. **Follow the official setup guide:** [Google Assistant Integration](https://www.home-assistant.io/integrations/google_assistant/)
2. **Source code reference:** [home-assistant/core - google_assistant](https://github.com/home-assistant/core/tree/dev/homeassistant/components/google_assistant)

You will need:
- A Google Cloud project with HomeGraph API enabled
- A service account with JSON key file
- An Actions on Google project linked to your Google Cloud project
- Your Home Assistant instance accessible via HTTPS

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/NathanMagnus/GoogleHomeExposureManager`
5. Select category: "Integration"
6. Click "Add"
7. Search for "Google Home Exposure Manager" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/NathanMagnus/GoogleHomeExposureManager/releases)
2. Extract the `custom_components/google_home_exposure_manager` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Google Home Exposure Manager"
3. Follow the setup wizard:
   - If Google Assistant is already configured, you're ready to go
   - If not, you'll be prompted to paste your service account JSON or confirm manual file placement

### First-Time Configuration (Migration)

When you click **Configure** for the first time, the integration will automatically detect your existing Google Assistant configuration:

1. **Automatic Detection** - The integration scans `configuration.yaml` for your Google Assistant include file (e.g., `google_assistant.yaml`)
2. **Import Prompt** - If existing `entity_config` is found, you'll see:
   - How many entities were found
   - How many are set to be exposed vs. hidden
   - The source file where they were detected
3. **Choose Action**:
   - **Import existing entities** (Recommended) - Migrates your entity configuration to the managed file, preserving all custom settings (names, aliases, room hints, etc.)
   - **Skip and start fresh** - Ignore existing config and start with a clean slate using bulk rules

**What happens during import:**
- Your original config file is backed up with a timestamp
- The `entity_config` section is moved to `google_assistant_entities.yaml`
- Your config file is updated to use `entity_config: !include google_assistant_entities.yaml`
- All other settings (project_id, service_account, report_state, etc.) remain unchanged
- The import is marked as complete so you won't be prompted again

> **Note:** This prompt only appears once. After you import or skip, you won't see it again even if you later remove all entity overrides.

### Configuring Entity Exposure

After migration (or if no migration is needed), you'll see the main menu:

1. Go to **Settings** → **Devices & Services**
2. Find "Google Home Exposure Manager" and click **Configure**
3. Use the menu to access different configuration sections:

#### Bulk Rules

Configure rules that apply to multiple entities:

- **Auto-expose domains**: Select which entity domains to expose (light, switch, cover, etc.)
- **Exclude areas**: Select areas whose entities should never be exposed
- **Exclude patterns**: Use glob patterns to exclude entities by name
  - `*_battery` - Excludes all entities ending with "_battery"
  - `sensor.temperature_*` - Excludes all temperature sensors
  - `*_unavailable` - Excludes entities with "_unavailable" in the name

#### Individual Entities

Override bulk rules for specific entities:

- **Always expose**: These entities will be exposed regardless of bulk rules
- **Never expose**: These entities will be excluded regardless of bulk rules

Individual overrides take priority over bulk rules.

#### Settings

- **Backups**: Create timestamped backups before modifying YAML files (recommended)

#### Preview & Save

Review your changes before applying:

- See the total number of entities that will be exposed
- Preview a list of affected entities
- Confirm or go back to make changes

> **Important:** Changes made in Bulk Rules, Individual Entities, and Settings are held in memory until you click **Preview & Save** and confirm. If you close the configuration dialog (X button) without saving, your changes will be discarded.

## How It Works

This integration manages a YAML file (`google_assistant_entities.yaml`) that is included in your Google Assistant configuration:

```yaml
# Your existing google_assistant config (e.g., google_assistant.yaml)
project_id: your-project-id
service_account: !include SERVICE_ACCOUNT.json
report_state: true
expose_by_default: false
exposed_domains:
  - switch
  - light
entity_config: !include google_assistant_entities.yaml  # ← Managed by this integration
```

The managed file preserves your custom entity settings while controlling exposure:

```yaml
# google_assistant_entities.yaml
# Managed by Google Home Exposure Manager - DO NOT EDIT
light.living_room:
  expose: true
  name: Living Room Light
  aliases:
    - Main Light
switch.coffee_maker:
  expose: true
  name: Coffee Machine
sensor.temperature:
  expose: false
```

**Key behaviors:**
- Only entities with `expose: true` are written to the file
- Entities not in the file are not exposed (due to `expose_by_default: false`)
- Custom properties (name, aliases, room_hint, etc.) are preserved from your original config

## File Structure

After setup, your config folder will contain:

```
config/
├── configuration.yaml              # Contains google_assistant: !include <your-ga-file>
├── google_assistant.yaml           # Your GA config (or whatever filename you use)
├── google_assistant_entities.yaml  # ← MANAGED BY THIS INTEGRATION
├── SERVICE_ACCOUNT.json            # Your Google service account credentials
└── backups/
    └── google_home_exposure_manager/
        ├── google_assistant_premigration_20260127_101500.yaml
        └── google_assistant_entities_20260127_120000.yaml
```

## Troubleshooting

### Reverting Changes / Restoring Backups

This integration automatically creates backups before modifying any files. Backups are stored in:

```
config/backups/google_home_exposure_manager/
```

**To restore a backup:**

1. Stop Home Assistant
2. Navigate to `config/backups/google_home_exposure_manager/`
3. Find the backup file with the timestamp before the problematic change
4. Copy it over the current file
5. Start Home Assistant

**To completely remove this integration's changes:**

1. Remove the integration from Settings → Devices & Services
2. Restore your original Google Assistant config file from backups (if needed)
3. Optionally delete:
   - `google_assistant_entities.yaml`
   - `.storage/google_home_exposure_manager.json`
   - `backups/google_home_exposure_manager/` folder

### "Google Assistant integration not found" warning

This warning appears if `google_assistant:` is not detected in your configuration. You can still configure rules - they will take effect once Google Assistant is set up.

### Changes not appearing in Google Home

After saving your configuration, you need to sync with Google:

1. Say **\"Hey Google, sync my devices\"** to any Google Home device
2. Wait a few minutes - Google can take time to process changes
3. Alternatively, call the `google_assistant.request_sync` service manually (requires proper Google Cloud setup)

### Invalid pattern error

Pattern syntax uses glob patterns:
- `*` matches any characters
- `?` matches a single character
- `[abc]` matches any character in brackets
- `[!abc]` matches any character NOT in brackets

### Permission errors

Ensure Home Assistant has write access to:
- Your Google Assistant config file
- `google_assistant_entities.yaml`
- The `backups/` directory

### Entities not showing up

Check that:
1. The entity is not disabled in the entity registry
2. The entity's domain is in the "Auto-expose domains" list
3. The entity doesn't match an exclude pattern
4. The entity's area isn't in the "Exclude areas" list

## Data Storage

Rules and settings are stored in:
```
.storage/google_home_exposure_manager.json
```

This file is managed by Home Assistant's storage system and should not be edited manually.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/GoogleHomeExposureManager.git

# Copy to your HA custom_components folder for testing
cp -r custom_components/google_home_exposure_manager /path/to/homeassistant/custom_components/
```

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a community integration and is not affiliated with Google or Home Assistant. Use at your own risk.
