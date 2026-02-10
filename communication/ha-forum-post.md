# Home Assistant Community Forum Post

**Category:** Share your Projects!
**Title:** Google Home Exposure Manager - UI for managing which entities are exposed to Google Home

---

Hi everyone,

I built a custom integration that adds a UI for managing which entities are exposed to the manual Google Assistant integration. Instead of hand-editing YAML to control `entity_config`, you get a sidebar panel where you can toggle exposure, set up bulk rules, and preview changes before saving.

**What it does:**
- **Bulk rules** -- expose entire domains, exclude areas, or use wildcard patterns (e.g., `*_battery` to hide all battery sensors)
- **Individual overrides** -- always-expose or never-expose specific entities, overriding bulk rules
- **Device rules** -- control exposure for all entities from a device at once
- **Aliases & custom names** -- set voice-friendly names for Google Home
- **Preview before save** -- see exactly what will change before writing to disk
- **Automatic migration** -- imports your existing `entity_config` on first setup, preserving names, aliases, and room hints
- **Safety** -- automatic timestamped backups, atomic writes, non-destructive uninstall

<!-- Upload these images from the screenshots/ folder in the repo -->
<!-- DeviceAndEntities.png - main entity list view -->
<!-- BulkRules.png - bulk rule configuration -->
<!-- PreviewAndSave.png - preview changes dialog -->
![Devices & Entities](upload://DeviceAndEntities.png)
![Bulk Rules](upload://BulkRules.png)
![Preview & Save](upload://PreviewAndSave.png)

**Requirements:**
- Home Assistant 2024.1.0+
- The [manual Google Assistant integration](https://www.home-assistant.io/integrations/google_assistant/) already set up

**Install via HACS:**
1. HACS -> Three dots -> Custom repositories
2. Add: `https://github.com/NathanMagnus/GoogleHomeExposureManager`
3. Category: Integration
4. Install and restart

GitHub: https://github.com/NathanMagnus/GoogleHomeExposureManager

Feedback, bug reports, and contributions welcome. This is v0.1.0 -- I'd especially appreciate hearing from anyone who tries it on their setup.
