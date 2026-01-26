"""Shared helper functions for Google Home Exposure Manager.

This module contains utility functions used across multiple components
to avoid code duplication (DRY principle).
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Domain icons for UI display
DOMAIN_ICONS: Final[dict[str, str]] = {
    "light": "💡",
    "switch": "🔌",
    "cover": "🪟",
    "fan": "🌀",
    "climate": "🌡️",
    "lock": "🔒",
    "sensor": "📊",
    "binary_sensor": "⚡",
    "camera": "📷",
    "media_player": "🎵",
    "vacuum": "🧹",
    "humidifier": "💨",
    "scene": "🎬",
    "script": "📜",
    "input_boolean": "☑️",
    "input_select": "📋",
    "automation": "⚙️",
    "group": "👥",
    "alarm_control_panel": "🚨",
    "select": "📝",
}
DEFAULT_ICON: Final = "▪️"


def validate_glob_pattern(pattern: str) -> bool:
    """Validate a glob pattern for entity matching.

    Args:
        pattern: The glob pattern to validate.

    Returns:
        True if the pattern is syntactically valid.
    """
    try:
        # Test that fnmatch can compile the pattern
        fnmatch.translate(pattern)

        # Check for unbalanced brackets
        bracket_depth = 0
        for char in pattern:
            if char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1
            if bracket_depth < 0:
                return False

        return bracket_depth == 0
    except Exception:
        return False


def match_glob_pattern(value: str, pattern: str) -> bool:
    """Check if a value matches a glob pattern.

    Args:
        value: The value to match (e.g., entity_id).
        pattern: The glob pattern to match against.

    Returns:
        True if the pattern matches the value.
    """
    try:
        return fnmatch.fnmatch(value, pattern)
    except Exception:
        return False


def get_domain_icon(domain: str) -> str:
    """Get the icon emoji for a domain.

    Args:
        domain: The entity domain (e.g., 'light', 'switch').

    Returns:
        An emoji representing the domain.
    """
    return DOMAIN_ICONS.get(domain, DEFAULT_ICON)


def group_entities_by_domain(entity_ids: list[str]) -> dict[str, list[str]]:
    """Group entity IDs by their domain.

    Args:
        entity_ids: List of entity IDs to group.

    Returns:
        Dictionary mapping domain names to lists of entity IDs.
    """
    grouped: dict[str, list[str]] = {}
    for entity_id in entity_ids:
        domain = entity_id.split(".")[0]
        if domain not in grouped:
            grouped[domain] = []
        grouped[domain].append(entity_id)
    return grouped


async def check_google_assistant_configured(hass: HomeAssistant) -> bool:
    """Check if Google Assistant is configured in Home Assistant.

    Args:
        hass: The Home Assistant instance.

    Returns:
        True if google_assistant is found in configuration.yaml.
    """
    from .const import CONFIGURATION_FILE

    config_path = Path(hass.config.config_dir) / CONFIGURATION_FILE

    def _check() -> bool:
        if not config_path.exists():
            return False
        try:
            content = config_path.read_text(encoding="utf-8")
            return "google_assistant:" in content
        except Exception:
            return False

    return await hass.async_add_executor_job(_check)


def ensure_dict_keys(
    data: dict[str, Any] | None,
    required_keys: dict[str, Any],
) -> dict[str, Any]:
    """Ensure a dictionary has all required keys with defaults.

    This function is useful for data migration and ensuring stored data
    always has the expected structure.

    Args:
        data: The data dictionary to check. If None, an empty dict is used.
        required_keys: Dictionary of keys and their default values.

    Returns:
        The data dictionary with all required keys present.
    """
    if data is None:
        data = {}

    for key, default in required_keys.items():
        if key not in data:
            # Deep copy mutable defaults to avoid shared state
            if isinstance(default, (list, dict)):
                import copy

                data[key] = copy.deepcopy(default)
            else:
                data[key] = default

    return data
