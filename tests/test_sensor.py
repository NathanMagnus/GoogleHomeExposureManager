"""Tests for the sensor platform."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.google_home_exposure_manager.const import DOMAIN
from custom_components.google_home_exposure_manager.sensor import (
    ExcludedEntitiesSensor,
    ExposedEntitiesSensor,
    LastSyncSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.async_on_unload = MagicMock()
    entry.add_update_listener = MagicMock()
    return entry


@pytest.fixture
def mock_rule_engine() -> MagicMock:
    """Create a mock rule engine."""
    engine = MagicMock()
    engine.compute_entities = AsyncMock(
        return_value=(
            ["light.living_room", "switch.kitchen"],  # exposed
            ["sensor.temperature"],  # excluded
            [],  # explicit_exclusions
            ["fan.bedroom"],  # unset
        )
    )
    return engine


@pytest.fixture
def mock_entry_data(mock_rule_engine: MagicMock) -> dict[str, Any]:
    """Create mock entry data."""
    return {
        "rule_engine": mock_rule_engine,
        "data": {
            "last_sync": "2024-01-15T10:30:00+00:00",
        },
    }


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_creates_sensors(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test that setup creates the expected sensors."""
        mock_hass.data[DOMAIN][mock_entry.entry_id] = mock_entry_data
        entities_added: list[Any] = []

        def capture_entities(
            entities: list[Any], update_before_add: bool = False
        ) -> None:
            entities_added.extend(entities)

        await async_setup_entry(mock_hass, mock_entry, capture_entities)

        assert len(entities_added) == 3
        assert any(isinstance(e, ExposedEntitiesSensor) for e in entities_added)
        assert any(isinstance(e, ExcludedEntitiesSensor) for e in entities_added)
        assert any(isinstance(e, LastSyncSensor) for e in entities_added)

    async def test_setup_with_no_entry_data(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test that setup handles missing entry data gracefully."""
        # Don't add entry data to mock_hass.data[DOMAIN]
        entities_added: list[Any] = []

        def capture_entities(
            entities: list[Any], update_before_add: bool = False
        ) -> None:
            entities_added.extend(entities)

        await async_setup_entry(mock_hass, mock_entry, capture_entities)

        # Should not add any entities
        assert len(entities_added) == 0


class TestExposedEntitiesSensor:
    """Tests for ExposedEntitiesSensor."""

    async def test_sensor_attributes(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor has correct attributes."""
        sensor = ExposedEntitiesSensor(mock_hass, mock_entry, mock_entry_data)

        assert sensor.name == "Exposed Entities"
        assert sensor.icon == "mdi:check-circle-outline"
        assert sensor.native_unit_of_measurement == "entities"
        assert "test_entry_id_exposed_count" in sensor.unique_id

    async def test_sensor_update(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor updates correctly."""
        sensor = ExposedEntitiesSensor(mock_hass, mock_entry, mock_entry_data)
        await sensor.async_update()

        assert sensor.native_value == 2  # Two exposed entities
        assert "domains" in sensor.extra_state_attributes
        assert sensor.extra_state_attributes["domains"] == {"light": 1, "switch": 1}
        assert sensor.extra_state_attributes["total_excluded"] == 1
        assert sensor.extra_state_attributes["total_unset"] == 1

    async def test_sensor_update_no_rule_engine(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor handles missing rule engine."""
        entry_data: dict[str, Any] = {"data": {}}
        sensor = ExposedEntitiesSensor(mock_hass, mock_entry, entry_data)
        await sensor.async_update()

        assert sensor.native_value == 0
        assert sensor.extra_state_attributes == {}


class TestExcludedEntitiesSensor:
    """Tests for ExcludedEntitiesSensor."""

    async def test_sensor_attributes(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor has correct attributes."""
        sensor = ExcludedEntitiesSensor(mock_hass, mock_entry, mock_entry_data)

        assert sensor.name == "Excluded Entities"
        assert sensor.icon == "mdi:cancel"
        assert sensor.native_unit_of_measurement == "entities"
        assert "test_entry_id_excluded_count" in sensor.unique_id

    async def test_sensor_update(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor updates correctly."""
        sensor = ExcludedEntitiesSensor(mock_hass, mock_entry, mock_entry_data)
        await sensor.async_update()

        assert sensor.native_value == 1  # One excluded entity
        assert "domains" in sensor.extra_state_attributes
        assert sensor.extra_state_attributes["domains"] == {"sensor": 1}
        assert sensor.extra_state_attributes["total_exposed"] == 2
        assert sensor.extra_state_attributes["total_unset"] == 1


class TestLastSyncSensor:
    """Tests for LastSyncSensor."""

    async def test_sensor_attributes(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor has correct attributes."""
        sensor = LastSyncSensor(mock_hass, mock_entry, mock_entry_data)

        assert sensor.name == "Last Sync"
        assert sensor.icon == "mdi:sync"
        assert sensor.device_class == "timestamp"
        assert "test_entry_id_last_sync" in sensor.unique_id

    async def test_sensor_update_with_timestamp(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test sensor updates with valid timestamp."""
        sensor = LastSyncSensor(mock_hass, mock_entry, mock_entry_data)
        await sensor.async_update()

        assert sensor.native_value is not None
        assert isinstance(sensor.native_value, datetime)
        assert sensor.native_value.year == 2024
        assert sensor.native_value.month == 1
        assert sensor.native_value.day == 15

    async def test_sensor_update_no_timestamp(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor handles missing timestamp."""
        entry_data: dict[str, Any] = {"data": {}}
        sensor = LastSyncSensor(mock_hass, mock_entry, entry_data)
        await sensor.async_update()

        assert sensor.native_value is None

    async def test_sensor_update_invalid_timestamp(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor handles invalid timestamp."""
        entry_data: dict[str, Any] = {"data": {"last_sync": "not-a-valid-date"}}
        sensor = LastSyncSensor(mock_hass, mock_entry, entry_data)
        await sensor.async_update()

        assert sensor.native_value is None


class TestSensorDeviceInfo:
    """Tests for sensor device info."""

    async def test_device_info_structure(
        self,
        mock_hass: MagicMock,
        mock_entry: MagicMock,
        mock_entry_data: dict[str, Any],
    ) -> None:
        """Test device info is correctly structured."""
        sensor = ExposedEntitiesSensor(mock_hass, mock_entry, mock_entry_data)

        device_info = sensor.device_info
        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, mock_entry.entry_id) in device_info["identifiers"]
        assert device_info["name"] == "Google Home Exposure Manager"
        assert device_info["manufacturer"] == "Home Assistant Community"
