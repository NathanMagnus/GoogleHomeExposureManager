"""Google Home Exposure Manager integration.

This integration provides a UI to manage which entities are exposed to the
manual Google Assistant integration in Home Assistant.

Safety: Only modifies files it creates, uses atomic writes, creates backups.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_AUTO_ALIASES,
    CONF_AUTO_SYNC,
    CONF_BACKUPS,
    CONF_BULK_RULES,
    CONF_DEVICE_OVERRIDES,
    CONF_ENTITY_CONFIG,
    CONF_ENTITY_OVERRIDES,
    CONF_EXCLUDE_AREAS,
    CONF_EXCLUDE_PATTERNS,
    CONF_EXPOSE_DOMAINS,
    CONF_FILTERED_DEVICES,
    CONF_FILTERED_ENTITIES,
    CONF_SETTINGS,
    CONF_SHOW_PANEL,
    DEFAULT_AUTO_ALIASES,
    DEFAULT_AUTO_SYNC,
    DEFAULT_BACKUPS,
    DEFAULT_EXPOSE_DOMAINS,
    DEFAULT_SHOW_PANEL,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .helpers import ensure_dict_keys
from .rule_engine import RuleEngine
from .websocket_api import async_register_websocket_commands
from .yaml_manager import YamlManager

if TYPE_CHECKING:
    pass

_LOGGER: Final = logging.getLogger(__name__)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]

# Type alias for stored data structure
type StoredData = dict[str, Any]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Google Home Exposure Manager component."""
    return True


def _ensure_valid_stored_data(stored_data: StoredData | None) -> StoredData:
    """Ensure stored data has all required keys with valid defaults.

    This function performs data migration and ensures all required fields exist.
    It handles cases where stored data is None, empty, or missing required keys.

    Args:
        stored_data: The loaded stored data, may be None or incomplete.

    Returns:
        A complete stored data dictionary with all required keys.
    """
    # Top-level keys
    stored_data = ensure_dict_keys(
        stored_data,
        {
            CONF_BULK_RULES: {},
            CONF_ENTITY_OVERRIDES: {},
            CONF_DEVICE_OVERRIDES: {},
            CONF_ENTITY_CONFIG: {},
            CONF_SETTINGS: {},
            CONF_FILTERED_ENTITIES: [],
            CONF_FILTERED_DEVICES: [],
        },
    )

    # Nested bulk_rules keys
    stored_data[CONF_BULK_RULES] = ensure_dict_keys(
        stored_data[CONF_BULK_RULES],
        {
            CONF_EXPOSE_DOMAINS: list(DEFAULT_EXPOSE_DOMAINS),
            CONF_EXCLUDE_AREAS: [],
            CONF_EXCLUDE_PATTERNS: [],
        },
    )

    # Nested settings keys
    stored_data[CONF_SETTINGS] = ensure_dict_keys(
        stored_data[CONF_SETTINGS],
        {
            CONF_AUTO_SYNC: DEFAULT_AUTO_SYNC,
            CONF_BACKUPS: DEFAULT_BACKUPS,
            CONF_AUTO_ALIASES: DEFAULT_AUTO_ALIASES,
            CONF_SHOW_PANEL: DEFAULT_SHOW_PANEL,
        },
    )

    return stored_data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Home Exposure Manager from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being set up.

    Returns:
        True if setup was successful.

    Raises:
        ConfigEntryNotReady: If setup fails and should be retried.
    """
    hass.data.setdefault(DOMAIN, {})

    try:
        store: Store[StoredData] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        stored_data = await store.async_load()
        stored_data = _ensure_valid_stored_data(stored_data)
        await store.async_save(stored_data)

        yaml_manager = YamlManager(hass)
        rule_engine = RuleEngine(hass, stored_data)

        hass.data[DOMAIN][entry.entry_id] = {
            "store": store,
            "data": stored_data,
            "yaml_manager": yaml_manager,
            "rule_engine": rule_engine,
        }

        # Register websocket commands (only once per integration)
        async_register_websocket_commands(hass)

        # Register sidebar panel if enabled
        show_panel = stored_data.get(CONF_SETTINGS, {}).get(
            CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL
        )
        if show_panel:
            await _register_panel(hass)

        # Set up platforms (sensors for stats display)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.async_on_unload(entry.add_update_listener(async_update_options))

        _LOGGER.info("Google Home Exposure Manager loaded successfully")
        return True

    except Exception as ex:
        _LOGGER.exception("Failed to set up Google Home Exposure Manager")
        raise ConfigEntryNotReady(
            f"Failed to initialize Google Home Exposure Manager: {ex}"
        ) from ex


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being unloaded.

    Returns:
        True if unload was successful.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("Google Home Exposure Manager unloaded")

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of a config entry.

    Note: Preserves config files and backups by design for safety.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being removed.
    """
    _LOGGER.info(
        "Google Home Exposure Manager removed. Your entity configuration "
        "files and backups have been preserved. Remove them manually if needed."
    )


async def _register_panel(hass: HomeAssistant) -> None:
    """Register the sidebar panel for the integration.

    Args:
        hass: The Home Assistant instance.
    """
    frontend_path = Path(__file__).parent / "frontend"

    # Register static paths for all frontend JS files (ES modules need all files)
    static_paths = [
        StaticPathConfig(
            "/google_exposure_panel.js",
            str(frontend_path / "google-exposure-panel.js"),
            False,
        ),
        StaticPathConfig(
            "/google_exposure_panel/panel-styles.js",
            str(frontend_path / "panel-styles.js"),
            False,
        ),
        StaticPathConfig(
            "/google_exposure_panel/panel-tabs.js",
            str(frontend_path / "panel-tabs.js"),
            False,
        ),
        StaticPathConfig(
            "/google_exposure_panel/panel-dialogs.js",
            str(frontend_path / "panel-dialogs.js"),
            False,
        ),
        StaticPathConfig(
            "/google_exposure_panel/alias-suggestions.js",
            str(frontend_path / "alias-suggestions.js"),
            False,
        ),
    ]
    await hass.http.async_register_static_paths(static_paths)

    # Register the custom panel
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="google-exposure-panel",
        frontend_url_path="google-exposure",
        sidebar_title="Google Exposure",
        sidebar_icon="mdi:home-export-outline",
        module_url="/google_exposure_panel.js",
        require_admin=True,
    )
