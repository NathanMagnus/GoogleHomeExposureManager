"""Constants for Google Home Exposure Manager."""

from __future__ import annotations

from typing import Final

from homeassistant.exceptions import HomeAssistantError

DOMAIN: Final = "google_home_exposure_manager"


class GoogleHomeExposureManagerError(HomeAssistantError):
    """Base exception for Google Home Exposure Manager."""


class ConfigurationError(GoogleHomeExposureManagerError):
    """Error in configuration."""


class MigrationError(GoogleHomeExposureManagerError):
    """Error during migration."""


class YamlWriteError(GoogleHomeExposureManagerError):
    """Error writing YAML file."""


# Storage
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = DOMAIN

# Default values
DEFAULT_EXPOSE_DOMAINS: Final[list[str]] = [
    "light",
    "switch",
    "cover",
    "fan",
    "climate",
    "lock",
    "scene",
    "script",
]
DEFAULT_AUTO_SYNC: Final = True
DEFAULT_BACKUPS: Final = True
DEFAULT_SHOW_PANEL: Final = True
DEFAULT_AUTO_ALIASES: Final = True

# File names
MANAGED_ENTITIES_FILE: Final = "google_assistant_entities.yaml"
GOOGLE_ASSISTANT_FILE: Final = "google_assistant.yaml"
SERVICE_ACCOUNT_FILE: Final = "SERVICE_ACCOUNT.json"
CONFIGURATION_FILE: Final = "configuration.yaml"

# Config keys
CONF_MANAGED_FILE: Final = "managed_file"
CONF_PARENT_FILE: Final = "parent_file"
CONF_BULK_RULES: Final = "bulk_rules"
CONF_EXPOSE_DOMAINS: Final = "expose_domains"
CONF_EXCLUDE_AREAS: Final = "exclude_areas"
CONF_EXCLUDE_PATTERNS: Final = "exclude_patterns"
CONF_ENTITY_OVERRIDES: Final = "entity_overrides"
CONF_DEVICE_OVERRIDES: Final = "device_overrides"
CONF_ENTITY_CONFIG: Final = "entity_config"
CONF_EXPOSE: Final = "expose"
CONF_SETTINGS: Final = "settings"
CONF_AUTO_SYNC: Final = "auto_sync"
CONF_BACKUPS: Final = "backups"
CONF_SHOW_PANEL: Final = "show_panel"
CONF_AUTO_ALIASES: Final = "auto_aliases"
CONF_LAST_SYNC: Final = "last_sync"
CONF_FILTERED_ENTITIES: Final = "filtered_entities"
CONF_FILTERED_DEVICES: Final = "filtered_devices"

# Supported domains for exposure
SUPPORTED_DOMAINS: Final[list[str]] = [
    "alarm_control_panel",
    "binary_sensor",
    "camera",
    "climate",
    "cover",
    "fan",
    "humidifier",
    "input_boolean",
    "input_select",
    "light",
    "lock",
    "media_player",
    "scene",
    "script",
    "select",
    "sensor",
    "switch",
    "vacuum",
]

# Header for managed YAML file
MANAGED_FILE_HEADER: Final = "# Managed by Google Home Exposure Manager - DO NOT EDIT\n"
