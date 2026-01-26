"""WebSocket API handlers for Google Home Exposure Manager.

This module contains all WebSocket command handlers for the frontend panel.
Extracted from __init__.py to follow Single Responsibility Principle.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Final

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.storage import Store

from .const import (
    CONF_BACKUPS,
    CONF_ENTITY_CONFIG,
    CONF_ENTITY_OVERRIDES,
    CONF_SETTINGS,
    DEFAULT_BACKUPS,
    DOMAIN,
    SUPPORTED_DOMAINS,
)

if TYPE_CHECKING:
    from .rule_engine import RuleEngine
    from .yaml_manager import YamlManager

_LOGGER: Final = logging.getLogger(__name__)

# Type alias for stored data structure
type StoredData = dict[str, Any]


def _get_entry_data(hass: HomeAssistant) -> dict[str, Any] | None:
    """Get the first config entry's data.

    Args:
        hass: The Home Assistant instance.

    Returns:
        The entry data dictionary or None if not found.
    """
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id, data in domain_data.items():
        if entry_id != "websocket_registered" and isinstance(data, dict):
            return data
    return None


def require_entry_data(
    func: Callable[
        [HomeAssistant, websocket_api.ActiveConnection, dict[str, Any], dict[str, Any]],
        Coroutine[Any, Any, None],
    ],
) -> Callable[
    [HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]],
    Coroutine[Any, Any, None],
]:
    """Decorator to require and inject entry_data into websocket handlers.

    Reduces boilerplate of checking for entry_data in every handler.
    """

    @wraps(func)
    async def wrapper(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        entry_data = _get_entry_data(hass)
        if not entry_data:
            connection.send_error(msg["id"], "not_found", "Integration not set up")
            return
        await func(hass, connection, msg, entry_data)

    return wrapper


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all websocket commands for this integration.

    This function is idempotent - it will only register commands once.

    Args:
        hass: The Home Assistant instance.
    """
    if hass.data[DOMAIN].get("websocket_registered"):
        return

    hass.data[DOMAIN]["websocket_registered"] = True

    # Register all command handlers
    websocket_api.async_register_command(hass, websocket_get_config)
    websocket_api.async_register_command(hass, websocket_get_entities)
    websocket_api.async_register_command(hass, websocket_compute_preview)
    websocket_api.async_register_command(hass, websocket_save_config)
    websocket_api.async_register_command(hass, websocket_handle_migration)


@websocket_api.websocket_command(
    {vol.Required("type"): "google_home_exposure_manager/get_config"}
)
@websocket_api.require_admin
@websocket_api.async_response
@require_entry_data
async def websocket_get_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    entry_data: dict[str, Any],
) -> None:
    """Get current configuration via websocket.

    Returns the stored configuration along with migration status.
    """
    yaml_manager: YamlManager = entry_data["yaml_manager"]
    stored_data: StoredData = entry_data["data"]

    # Check for migration
    migration_needed = False
    migration_data: dict[str, Any] | None = None

    if not stored_data.get("import_completed"):
        parent_file = await yaml_manager.find_google_assistant_config_file()
        if parent_file:
            entity_config = await yaml_manager.read_entity_config(parent_file)
            if entity_config:
                migration_needed = True
                exposed = sum(
                    1
                    for e in entity_config.values()
                    if isinstance(e, dict) and e.get("expose") is True
                )
                excluded = sum(
                    1
                    for e in entity_config.values()
                    if isinstance(e, dict) and e.get("expose") is False
                )
                migration_data = {
                    "source_file": parent_file,
                    "count": len(entity_config),
                    "exposed": exposed,
                    "excluded": excluded,
                }

    connection.send_result(
        msg["id"],
        {
            "config": stored_data,
            "migration_needed": migration_needed,
            "migration_data": migration_data,
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "google_home_exposure_manager/get_entities"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_get_entities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all manageable entities, devices, and areas via websocket."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)

    entities: list[dict[str, Any]] = []
    for entity in entity_reg.entities.values():
        domain = entity.entity_id.split(".")[0]
        if domain not in SUPPORTED_DOMAINS:
            continue
        if entity.disabled:
            continue
        if entity.entity_category is not None:
            continue

        entities.append(
            {
                "entity_id": entity.entity_id,
                "name": entity.name or entity.original_name,
                "domain": domain,
                "device_id": entity.device_id,
                "area_id": entity.area_id,
            }
        )

    # Get devices with entity counts
    device_entity_counts: dict[str, int] = {}
    for entity in entities:
        device_id = entity.get("device_id")
        if device_id:
            device_entity_counts[device_id] = device_entity_counts.get(device_id, 0) + 1

    devices: list[dict[str, Any]] = []
    for device in device_reg.devices.values():
        if device.id in device_entity_counts:
            devices.append(
                {
                    "id": device.id,
                    "name": device.name_by_user or device.name or device.id,
                    "area_id": device.area_id,
                    "entity_count": device_entity_counts[device.id],
                }
            )

    areas = [
        {"area_id": area.id, "name": area.name} for area in area_reg.async_list_areas()
    ]

    connection.send_result(
        msg["id"],
        {"entities": entities, "devices": devices, "areas": areas},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "google_home_exposure_manager/compute_preview",
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
@require_entry_data
async def websocket_compute_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    entry_data: dict[str, Any],
) -> None:
    """Compute preview for a given configuration via websocket."""
    rule_engine: RuleEngine = entry_data["rule_engine"]
    current_config: dict[str, Any] = entry_data["data"]
    new_config: dict[str, Any] = msg["config"]

    try:
        (
            exposed,
            excluded,
            _,
            unset,
            exclusion_reasons,
        ) = await rule_engine.compute_entities(new_config)

        # Get entity configs (aliases, names, rooms)
        new_entity_config = new_config.get(CONF_ENTITY_CONFIG, {})
        old_entity_config = current_config.get(CONF_ENTITY_CONFIG, {})

        # Build exposed entities with their configs
        exposed_with_config = []
        for entity_id in exposed:
            config = new_entity_config.get(entity_id, {})
            exposed_with_config.append(
                {
                    "entity_id": entity_id,
                    "name": config.get("name"),
                    "aliases": config.get("aliases", []),
                    "room": config.get("room"),
                }
            )

        # Detect changes in entity_config
        config_changes = []
        all_entity_ids = set(new_entity_config.keys()) | set(old_entity_config.keys())
        for entity_id in all_entity_ids:
            old_cfg = old_entity_config.get(entity_id, {})
            new_cfg = new_entity_config.get(entity_id, {})

            changes = []
            # Check name
            if old_cfg.get("name") != new_cfg.get("name"):
                changes.append(
                    {
                        "field": "name",
                        "old": old_cfg.get("name"),
                        "new": new_cfg.get("name"),
                    }
                )
            # Check aliases
            old_aliases = set(old_cfg.get("aliases", []))
            new_aliases = set(new_cfg.get("aliases", []))
            if old_aliases != new_aliases:
                changes.append(
                    {
                        "field": "aliases",
                        "added": list(new_aliases - old_aliases),
                        "removed": list(old_aliases - new_aliases),
                    }
                )
            # Check room
            if old_cfg.get("room") != new_cfg.get("room"):
                changes.append(
                    {
                        "field": "room",
                        "old": old_cfg.get("room"),
                        "new": new_cfg.get("room"),
                    }
                )

            if changes:
                config_changes.append(
                    {
                        "entity_id": entity_id,
                        "changes": changes,
                    }
                )

        connection.send_result(
            msg["id"],
            {
                "exposed": exposed,
                "excluded": excluded,
                "unset": unset,
                "exclusion_reasons": exclusion_reasons,
                "exposed_with_config": exposed_with_config,
                "config_changes": config_changes,
            },
        )
    except Exception as ex:
        _LOGGER.exception("Failed to compute preview")
        connection.send_error(msg["id"], "compute_error", str(ex))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "google_home_exposure_manager/save_config",
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
@require_entry_data
async def websocket_save_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    entry_data: dict[str, Any],
) -> None:
    """Save configuration via websocket."""
    store: Store[StoredData] = entry_data["store"]
    yaml_manager: YamlManager = entry_data["yaml_manager"]
    rule_engine: RuleEngine = entry_data["rule_engine"]
    new_config: StoredData = msg["config"]

    try:
        # Compute what to write
        (
            exposed,
            excluded,
            explicit_exclusions,
            _,
            _,
        ) = await rule_engine.compute_entities(new_config)

        # Get entity_config (name, aliases, room)
        entity_config = new_config.get(CONF_ENTITY_CONFIG, {})

        # Create backup if enabled
        settings = new_config.get(CONF_SETTINGS, {})
        if settings.get(CONF_BACKUPS, DEFAULT_BACKUPS):
            await yaml_manager.create_backup()

        # Write entities file with entity_config
        await yaml_manager.write_entities_file(
            exposed, excluded, explicit_exclusions, entity_config
        )
        _LOGGER.info(
            "Saved configuration: %d entities exposed, %d excluded, %d with custom config",
            len(exposed),
            len(excluded),
            len(entity_config),
        )

        # Update stored data
        await store.async_save(new_config)
        entry_data["data"] = new_config
        rule_engine.update_data(new_config)

        connection.send_result(msg["id"], {"success": True})

    except Exception as ex:
        _LOGGER.exception("Failed to save config")
        connection.send_error(msg["id"], "save_error", str(ex))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "google_home_exposure_manager/handle_migration",
        vol.Required("action"): vol.In(["import", "skip"]),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
@require_entry_data
async def websocket_handle_migration(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    entry_data: dict[str, Any],
) -> None:
    """Handle migration action (import or skip) via websocket."""
    store: Store[StoredData] = entry_data["store"]
    yaml_manager: YamlManager = entry_data["yaml_manager"]
    stored_data: StoredData = entry_data["data"]
    action: str = msg["action"]

    try:
        if action == "import":
            parent_file = await yaml_manager.find_google_assistant_config_file()
            if parent_file:
                # Create backup first
                await yaml_manager.create_backup(parent_file, mandatory=True)

                # Migrate
                await yaml_manager.migrate_entity_config(parent_file)

                # Load migrated entities as overrides
                entity_config = await yaml_manager.read_entity_config(parent_file)
                if entity_config:
                    entity_overrides: dict[str, dict[str, Any]] = {}
                    for entity_id, config in entity_config.items():
                        if isinstance(config, dict) and "expose" in config:
                            entity_overrides[entity_id] = {
                                "expose": config.get("expose")
                            }
                    stored_data[CONF_ENTITY_OVERRIDES] = entity_overrides

        # Mark import as completed (skip or import)
        stored_data["import_completed"] = True
        await store.async_save(stored_data)
        entry_data["data"] = stored_data

        connection.send_result(msg["id"], {"success": True})

    except Exception as ex:
        _LOGGER.exception("Migration failed")
        connection.send_error(msg["id"], "migration_error", str(ex))
