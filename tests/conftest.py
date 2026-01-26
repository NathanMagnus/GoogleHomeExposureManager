"""Pytest configuration and fixtures for Google Home Exposure Manager tests."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.config.config_dir = "/config"
    hass.config.path = lambda x: f"/config/{x}"
    hass.data = {}

    # Make async_add_executor_job run the function directly
    async def run_executor(func, *args):
        return func(*args)

    hass.async_add_executor_job = run_executor
    return hass


@pytest.fixture
def stored_data() -> dict[str, Any]:
    """Create sample stored data for testing."""
    return {
        "bulk_rules": {
            "expose_domains": ["light", "switch"],
            "exclude_areas": ["garage"],
            "exclude_patterns": ["*_test", "sensor.*_battery"],
        },
        "entity_overrides": {
            "light.living_room": {"expose": True},
            "switch.hidden": {"expose": False},
        },
        "device_overrides": {
            "device_123": {"expose": True},
            "device_456": {"expose": False},
        },
        "settings": {
            "auto_sync": True,
            "backups": True,
            "show_panel": True,
        },
    }


@pytest.fixture
def empty_stored_data() -> dict[str, Any]:
    """Create empty stored data for testing defaults."""
    return {}


@pytest.fixture
def mock_entity_registry() -> MagicMock:
    """Create a mock entity registry with sample entities."""
    registry = MagicMock()

    # Create mock entities
    entities = {}

    def create_entity(
        entity_id: str,
        device_id: str | None = None,
        area_id: str | None = None,
        disabled: bool = False,
        entity_category: str | None = None,
        hidden_by: str | None = None,
    ) -> MagicMock:
        entity = MagicMock()
        entity.entity_id = entity_id
        entity.device_id = device_id
        entity.area_id = area_id
        entity.disabled = disabled
        entity.entity_category = entity_category
        entity.hidden_by = hidden_by
        entity.name = entity_id.split(".")[-1].replace("_", " ").title()
        entity.original_name = entity.name
        return entity

    # Add various test entities
    entities["light.living_room"] = create_entity(
        "light.living_room", device_id="device_123", area_id="living_room"
    )
    entities["light.kitchen"] = create_entity(
        "light.kitchen", device_id="device_124", area_id="kitchen"
    )
    entities["light.garage"] = create_entity(
        "light.garage", device_id="device_125", area_id="garage"
    )
    entities["switch.office"] = create_entity(
        "switch.office", device_id="device_126", area_id="office"
    )
    entities["switch.hidden"] = create_entity(
        "switch.hidden", device_id="device_127"
    )
    entities["sensor.temperature"] = create_entity(
        "sensor.temperature", device_id="device_128", area_id="living_room"
    )
    entities["sensor.battery_test"] = create_entity(
        "sensor.battery_test", device_id="device_129"
    )
    entities["light.disabled"] = create_entity(
        "light.disabled", disabled=True
    )
    entities["switch.diagnostic"] = create_entity(
        "switch.diagnostic", entity_category="diagnostic"
    )
    entities["climate.thermostat"] = create_entity(
        "climate.thermostat", device_id="device_130", area_id="living_room"
    )
    # Entity on excluded device
    entities["light.excluded_device"] = create_entity(
        "light.excluded_device", device_id="device_456"
    )
    # Entity matching pattern
    entities["light.something_test"] = create_entity(
        "light.something_test"
    )

    registry.entities = entities
    registry.async_get = lambda eid: entities.get(eid)

    return registry


@pytest.fixture
def mock_device_registry() -> MagicMock:
    """Create a mock device registry."""
    registry = MagicMock()

    devices = {}

    def create_device(
        device_id: str,
        name: str,
        area_id: str | None = None,
    ) -> MagicMock:
        device = MagicMock()
        device.id = device_id
        device.name = name
        device.name_by_user = None
        device.area_id = area_id
        return device

    devices["device_123"] = create_device("device_123", "Living Room Light", "living_room")
    devices["device_124"] = create_device("device_124", "Kitchen Light", "kitchen")
    devices["device_125"] = create_device("device_125", "Garage Light", "garage")
    devices["device_126"] = create_device("device_126", "Office Switch", "office")
    devices["device_127"] = create_device("device_127", "Hidden Switch")
    devices["device_128"] = create_device("device_128", "Temperature Sensor", "living_room")
    devices["device_129"] = create_device("device_129", "Battery Sensor")
    devices["device_130"] = create_device("device_130", "Thermostat", "living_room")
    devices["device_456"] = create_device("device_456", "Excluded Device")

    registry.devices = devices
    registry.async_get = lambda did: devices.get(did)

    return registry


@pytest.fixture
def mock_area_registry() -> MagicMock:
    """Create a mock area registry."""
    registry = MagicMock()

    class Area:
        def __init__(self, area_id: str, name: str):
            self.id = area_id
            self.name = name

    areas = {
        "living_room": Area("living_room", "Living Room"),
        "kitchen": Area("kitchen", "Kitchen"),
        "garage": Area("garage", "Garage"),
        "office": Area("office", "Office"),
    }

    registry.async_get_area = lambda aid: areas.get(aid)
    registry.async_list_areas = lambda: list(areas.values())

    return registry


@pytest.fixture
def mock_registries(
    mock_hass: MagicMock,
    mock_entity_registry: MagicMock,
    mock_device_registry: MagicMock,
    mock_area_registry: MagicMock,
) -> Generator[None, None, None]:
    """Patch all registries to return mocks."""
    with (
        patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=mock_entity_registry,
        ),
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=mock_device_registry,
        ),
        patch(
            "homeassistant.helpers.area_registry.async_get",
            return_value=mock_area_registry,
        ),
    ):
        yield


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_hass_with_temp_dir(temp_config_dir: Path) -> MagicMock:
    """Create a mock Home Assistant with a real temp directory."""
    hass = MagicMock()
    hass.config.config_dir = str(temp_config_dir)
    hass.config.path = lambda x: str(temp_config_dir / x)
    hass.data = {}

    async def run_executor(func, *args):
        return func(*args)

    hass.async_add_executor_job = run_executor
    return hass
