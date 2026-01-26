"""Sensor platform for Google Home Exposure Manager.

Provides statistics about exposed entities for display on the integration page.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import group_entities_by_domain

if TYPE_CHECKING:
    from .rule_engine import RuleEngine

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.
    """
    entry_data = hass.data[DOMAIN].get(entry.entry_id)
    if not entry_data:
        _LOGGER.warning("No entry data found for sensor setup")
        return

    sensors = [
        ExposedEntitiesSensor(hass, entry, entry_data),
        ExcludedEntitiesSensor(hass, entry, entry_data),
        LastSyncSensor(hass, entry, entry_data),
    ]

    async_add_entities(sensors, update_before_add=True)


class ExposureBaseSensor(SensorEntity):
    """Base class for exposure statistics sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entry_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor.

        Args:
            hass: The Home Assistant instance.
            entry: The config entry.
            entry_data: The integration's stored data.
        """
        self._hass = hass
        self._entry = entry
        self._entry_data = entry_data
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Google Home Exposure Manager",
            "manufacturer": "Home Assistant Community",
            "model": "Exposure Manager",
            "entry_type": "service",
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        # Update when integration data changes
        self._entry.async_on_unload(
            self._entry.add_update_listener(self._async_update_listener)
        )

    async def _async_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options updates."""
        self.async_schedule_update_ha_state(force_refresh=True)


class ExposedEntitiesSensor(ExposureBaseSensor):
    """Sensor showing the count of exposed entities."""

    _attr_name = "Exposed Entities"
    _attr_icon = "mdi:check-circle-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "entities"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entry_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, entry_data)
        self._attr_unique_id = f"{entry.entry_id}_exposed_count"

    async def async_update(self) -> None:
        """Update the sensor state."""
        rule_engine: RuleEngine | None = self._entry_data.get("rule_engine")
        if not rule_engine:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {}
            return

        stored_data = self._entry_data.get("data", {})
        try:
            exposed, excluded, _, unset = await rule_engine.compute_entities(
                stored_data
            )
            self._attr_native_value = len(exposed)

            # Group by domain for attributes using shared helper
            domains = {
                domain: len(entities)
                for domain, entities in group_entities_by_domain(exposed).items()
            }

            self._attr_extra_state_attributes = {
                "domains": domains,
                "total_excluded": len(excluded),
                "total_unset": len(unset),
            }
        except Exception as ex:
            _LOGGER.error("Failed to compute exposed entities: %s", ex)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {"error": str(ex)}


class ExcludedEntitiesSensor(ExposureBaseSensor):
    """Sensor showing the count of excluded entities."""

    _attr_name = "Excluded Entities"
    _attr_icon = "mdi:cancel"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "entities"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entry_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, entry_data)
        self._attr_unique_id = f"{entry.entry_id}_excluded_count"

    async def async_update(self) -> None:
        """Update the sensor state."""
        rule_engine: RuleEngine | None = self._entry_data.get("rule_engine")
        if not rule_engine:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {}
            return

        stored_data = self._entry_data.get("data", {})
        try:
            exposed, excluded, _, unset = await rule_engine.compute_entities(
                stored_data
            )
            self._attr_native_value = len(excluded)

            # Group by domain for attributes using shared helper
            domains = {
                domain: len(entities)
                for domain, entities in group_entities_by_domain(excluded).items()
            }

            self._attr_extra_state_attributes = {
                "domains": domains,
                "total_exposed": len(exposed),
                "total_unset": len(unset),
            }
        except Exception as ex:
            _LOGGER.error("Failed to compute excluded entities: %s", ex)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {"error": str(ex)}


class LastSyncSensor(ExposureBaseSensor):
    """Sensor showing when the configuration was last synced."""

    _attr_name = "Last Sync"
    _attr_icon = "mdi:sync"
    _attr_device_class = "timestamp"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entry_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, entry_data)
        self._attr_unique_id = f"{entry.entry_id}_last_sync"

    async def async_update(self) -> None:
        """Update the sensor state."""
        stored_data = self._entry_data.get("data", {})
        last_sync = stored_data.get("last_sync")

        if last_sync:
            try:
                # Parse ISO format timestamp
                self._attr_native_value = datetime.fromisoformat(last_sync)
            except (ValueError, TypeError):
                self._attr_native_value = None
        else:
            self._attr_native_value = None
