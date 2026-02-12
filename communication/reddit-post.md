# Reddit Post (r/homeassistant)

**Title:** I built a UI for managing which entities are exposed to Google Home (HACS integration)

---

If you use the manual Google Assistant integration, you know the pain of editing YAML to control which entities are exposed. I built a HACS custom integration that gives you a sidebar panel to manage all of it visually.

**Features:**
- Toggle entity exposure on/off from a sidebar panel
- Bulk rules: expose entire domains, exclude areas, wildcard patterns
- Individual entity overrides
- Custom names and aliases for voice control
- Preview changes before saving
- Automatic backups before any file modification
- Migrates your existing entity_config on first setup

<!-- Upload these images from the screenshots/ folder in the repo -->
<!-- When posting to Reddit, upload DeviceAndEntities.png, BulkRules.png, and PreviewAndSave.png -->
<!-- Reddit supports image posts or you can upload to imgur and link them -->
[Screenshots in the GitHub repo](https://github.com/NathanMagnus/GoogleHomeExposureManager#screenshots)

**Install via HACS** (custom repository): `https://github.com/NathanMagnus/GoogleHomeExposureManager`

Requires HA 2024.1.0+ and the manual Google Assistant integration.

Full disclosure: this was vibe coded with AI assistance, but it has full test coverage, automatic backups, and atomic writes so it shouldn't break anything. This is v0.1.0 -- feedback and bug reports welcome. GitHub link in the HACS listing or here: https://github.com/NathanMagnus/GoogleHomeExposureManager
