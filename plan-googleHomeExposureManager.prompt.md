# Plan: Google Home Exposure Manager HACS Integration

A HACS custom integration providing a single-page UI to control entity exposure to the manual Google Assistant integration, with bulk rules, individual overrides, validation, and preview before saving.

## Steps

1. **Create HACS integration structure** — Set up `custom_components/google_home_exposure_manager/` with `__init__.py`, `manifest.json`, `config_flow.py`, `const.py`, `strings.json`, `translations/en.json`, and `hacs.json`.

2. **Build config flow with smart detection**:
   - **No config**: Check for `SERVICE_ACCOUNT.json` → if missing, offer paste or file placement → auto-extract `project_id` → create all files → append `!include` to `configuration.yaml`
   - **Inline config**: Inject `entity_config: !include google_assistant_entities.yaml`
   - **Existing include**: Modify included file to add `entity_config: !include`
   - **Existing `entity_config`**: Backup → migrate entries → replace with `!include`

3. **Implement file management module**:
   - Use `ruamel.yaml` to preserve comments/formatting
   - Create timestamped backups before any modification
   - Store rules/state in `.storage/google_home_exposure_manager.json`

4. **Build single-page options flow with collapsible sections**:
   - **Warning banner** (if `google_assistant:` not found): Show at top of page with link to setup guide
   - **Bulk Rules** (expanded): Domain multi-select, area excludes, pattern excludes
   - **Individual Entities** (collapsed): Entity picker for explicit expose/exclude
   - **Settings** (collapsed): Auto-sync (default on), backups toggle

5. **Implement validation** — Before save: valid patterns, no conflicts, areas exist, at least one entity exposed. Block save on failure.

6. **Implement preview step** — Show entity count and list before committing.

7. **Implement rule engine** — Generate `google_assistant_entities.yaml` from rules + overrides.

8. **Add sync trigger** — Auto-call `google_assistant.request_sync` after save (unless disabled).

9. **Create README documentation**:
   - Installation via HACS
   - Manual installation
   - Prerequisites (link to Google Assistant integration setup)
   - Configuration guide
   - Troubleshooting

10. **Package for HACS** — `hacs.json`, repository structure, validate against HACS requirements.

---

## Warning Banner (No Google Config Detected)

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  Google Assistant integration not found                 │
├─────────────────────────────────────────────────────────────┤
│  This integration manages entity exposure for the manual    │
│  Google Assistant integration, which is not yet configured. │
│                                                             │
│  → Set up Google Assistant first (opens docs link)          │
│                                                             │
│  You can still configure rules below. They will take effect │
│  once Google Assistant is set up.                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Options Flow Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Configure Rules                                    │
├─────────────────────────────────────────────────────────────┤
│  ▼ Bulk Rules                                               │
│  │  Auto-expose domains: ☑ light ☑ switch ☐ sensor ...    │
│  │  Exclude areas: [Garage] [Basement]                     │
│  │  Exclude patterns: *_battery, sensor.temp_*             │
│                                                             │
│  ▶ Individual Entities                                      │
│  │  Expose: [entity picker with search]                    │
│  │  Exclude: [entity picker with search]                   │
│                                                             │
│  ▶ Settings                                                 │
│  │  ☑ Auto-sync  ☑ Backups                                 │
│                                                             │
│  [Preview]                                                  │
└─────────────────────────────────────────────────────────────┘
         ↓
    Validation
         ↓
┌─ Pass? ──────────────────────────────────────────────────────┐
│ No  → Show errors, return to Step 1                          │
│ Yes → Step 2                                                 │
└──────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Preview                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  This will expose 47 entities to Google Assistant:          │
│                                                             │
│  • light.living_room                                        │
│  • light.bedroom                                            │
│  • light.kitchen                                            │
│  • switch.coffee_maker                                      │
│  • ... and 43 more                                          │
│                                                             │
│  Excluded: 12 entities                                      │
│                                                             │
│  [Back]  [Save]                                             │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Writes google_assistant_entities.yaml                      │
│  Calls google_assistant.request_sync (if enabled)           │
│  Done                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

| Check | Error Message |
|-------|---------------|
| Invalid glob pattern | "Invalid pattern: `[unclosed` — check syntax" |
| Entity in both lists | "Conflict: `light.kitchen` is in both expose and exclude" |
| Area doesn't exist | "Area not found: `garage`" |
| No entities exposed | "No entities will be exposed — add domains or entities" |
| YAML write failure | "Could not write config — check file permissions" |

---

## File Structure

### Repository

```
google-home-exposure-manager/
├── hacs.json
├── README.md
├── LICENSE
└── custom_components/
    └── google_home_exposure_manager/
        ├── __init__.py
        ├── manifest.json
        ├── config_flow.py
        ├── const.py
        ├── yaml_manager.py
        ├── rule_engine.py
        ├── strings.json
        └── translations/
            └── en.json
```

### User's Config Folder (After Setup)

```
config/
├── configuration.yaml                    # Auto-modified if needed
├── google_assistant.yaml                 # Modified to add entity_config !include
├── google_assistant_entities.yaml        # FULLY MANAGED
├── SERVICE_ACCOUNT.json                  # User-provided or created from paste
└── .storage/
    └── google_home_exposure_manager.json # Rules + state
```

---

## Data Storage

**.storage/google_home_exposure_manager.json**:
```json
{
  "version": 1,
  "data": {
    "managed_file": "google_assistant_entities.yaml",
    "parent_file": "google_assistant.yaml",
    "bulk_rules": {
      "expose_domains": ["light", "switch", "cover"],
      "exclude_areas": ["garage"],
      "exclude_patterns": ["*_battery", "sensor.temperature_*"]
    },
    "entity_overrides": {
      "light.garage_main": { "expose": true },
      "light.kids_room": { "expose": false }
    },
    "settings": {
      "auto_sync": true,
      "backups": true
    },
    "last_sync": "2026-01-26T12:00:00Z"
  }
}
```

---

## Generated YAML

**google_assistant_entities.yaml**:
```yaml
# Managed by Google Home Exposure Manager - DO NOT EDIT
light.living_room:
  expose: true
light.bedroom:
  expose: true
switch.coffee_maker:
  expose: true
light.garage:
  expose: false
sensor.temperature:
  expose: false
```

---

## Config Flow Detection Logic

| Scenario | Detection | Action |
|----------|-----------|--------|
| **No config** | `google_assistant:` not in `configuration.yaml` | Prompt for credentials → create `google_assistant.yaml` → add `!include` to `configuration.yaml` |
| **Inline config** | `google_assistant:` with nested keys | Backup → inject `entity_config: !include` line |
| **Existing include (our file)** | `google_assistant: !include google_assistant.yaml` | Modify that file to add `entity_config: !include` |
| **Existing include (other file)** | `google_assistant: !include custom.yaml` | Modify that file to add `entity_config: !include` |
| **Existing `entity_config`** | `entity_config:` with entries | Backup → migrate to `google_assistant_entities.yaml` → replace with `!include` |

---

## Service Account Handling

| Scenario | Action |
|----------|--------|
| `SERVICE_ACCOUNT.json` exists | Use it, skip credential input |
| Referenced via `service_account: !include X.json` | Use referenced file |
| Not found | Show paste or manual placement option → auto-extract `project_id` from JSON |
