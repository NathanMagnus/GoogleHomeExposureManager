# Copilot Instructions

Home Assistant HACS integration for Google Assistant entity exposure management.

---

## Workflow

**Use todo list tool** for each prompt:

1. **Understand** — Gather context
2. **Plan** — Create actionable todo list
3. **Implement** — Complete tasks, mark progress
4. **Clean** — Remove debug code, dead code, unused imports
5. **Refactor** — DRY, simplify, extract
6. **Test** — Write/update tests
7. **Verify** — `pytest tests/ -v`
8. **Document** — Update README if needed

---

## Principles

**KISS · DRY · SOLID · YAGNI**

Prefer HA built-ins: `homeassistant.helpers`, `homeassistant.util`, `voluptuous`

---

## Rules

- Type hints on all functions
- Tests for all new code
- Proper error handling with logging
- Atomic writes (temp → rename)
- Backups before modifications

---

## Docs

- [Home Assistant Dev](https://developers.home-assistant.io/)
- [HACS Integration](https://hacs.xyz/docs/publish/integration)

---

## Structure

```
custom_components/google_home_exposure_manager/
├── __init__.py       # Setup, panel registration
├── config_flow.py    # Config/options flows
├── const.py          # Constants
├── helpers.py        # Utilities
├── repairs.py        # Repair flows
├── rule_engine.py    # Exposure logic
├── sensor.py         # Sensors
├── websocket_api.py  # WebSocket API
├── yaml_manager.py   # YAML I/O
└── frontend/
    ├── google-exposure-panel.js
    ├── panel-styles.js
    ├── panel-tabs.js
    ├── panel-dialogs.js
    └── alias-suggestions.js
```
