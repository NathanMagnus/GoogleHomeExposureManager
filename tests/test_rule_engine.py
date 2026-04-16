"""Tests for the rule engine module."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.google_home_exposure_manager.rule_engine import RuleEngine


class TestRuleEngineCompute:
    """Tests for RuleEngine.compute_entities method."""

    @pytest.mark.asyncio
    async def test_basic_domain_exposure(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test basic domain-based exposure."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # All lights should be exposed (except disabled/diagnostic)
        assert "light.living_room" in result.exposed
        assert "light.kitchen" in result.exposed
        assert "light.garage" in result.exposed

        # Switches should be unset (not in expose_domains)
        assert "switch.office" in result.unset
        assert "switch.hidden" in result.unset

        # Disabled and diagnostic entities should not appear
        assert "light.disabled" not in result.exposed
        assert "light.disabled" not in result.excluded
        assert "light.disabled" not in result.unset

    @pytest.mark.asyncio
    async def test_area_exclusion(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test area-based exclusion."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": ["garage"],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Garage light should be excluded
        assert "light.garage" in result.excluded
        assert "light.garage" not in result.exposed
        assert "light.garage" in result.exclusion_reasons["area"]

        # Other lights should be exposed
        assert "light.living_room" in result.exposed
        assert "light.kitchen" in result.exposed

    @pytest.mark.asyncio
    async def test_pattern_exclusion(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test pattern-based exclusion."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light", "sensor"],
                "exclude_areas": [],
                "exclude_patterns": ["*_test", "sensor.*_battery*"],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Pattern matches should be excluded
        assert "light.something_test" in result.excluded
        assert "sensor.battery_test" in result.excluded
        assert "light.something_test" in result.exclusion_reasons["pattern"]
        assert "sensor.battery_test" in result.exclusion_reasons["pattern"]

        # Non-matching entities should be exposed
        assert "light.living_room" in result.exposed
        assert "sensor.temperature" in result.exposed

    @pytest.mark.asyncio
    async def test_entity_override_inclusion(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test result.explicit_exclusions entity inclusion overrides domain rules."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": [],  # No domains result.exposed by default
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {
                "light.kitchen": {"expose": True},
            },
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Explicitly included entity should be exposed
        assert "light.kitchen" in result.exposed

        # Other lights should be unset (no domain rule)
        assert "light.living_room" in result.unset

    @pytest.mark.asyncio
    async def test_entity_override_exclusion_priority(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test entity exclusion has highest priority."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {
                "light.kitchen": {"expose": False},  # Explicit exclusion
            },
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Explicitly excluded should not be exposed
        assert "light.kitchen" in result.excluded
        assert "light.kitchen" in result.explicit_exclusions
        assert "light.kitchen" not in result.exposed
        assert "light.kitchen" in result.exclusion_reasons["entity_override"]

        # Other lights should be exposed
        assert "light.living_room" in result.exposed

    @pytest.mark.asyncio
    async def test_device_override_inclusion(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test device-level inclusion."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": [],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {
                "device_123": {"expose": True},  # Living room light device
            },
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Entity on included device should be exposed
        assert "light.living_room" in result.exposed

    @pytest.mark.asyncio
    async def test_device_override_exclusion_priority(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test device exclusion has high priority."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {
                "device_456": {"expose": False},  # Excluded device
            },
        }

        engine = RuleEngine(mock_hass, stored_data)
        result = await engine.compute_entities()

        # Entity on excluded device should be excluded
        assert "light.excluded_device" in result.excluded
        assert "light.excluded_device" in result.explicit_exclusions
        assert "light.excluded_device" not in result.exposed
        assert "light.excluded_device" in result.exclusion_reasons["device_override"]


class TestRuleEngineValidation:
    """Tests for RuleEngine.validate_rules method."""

    @pytest.mark.asyncio
    async def test_valid_rules(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test validation passes for valid rules."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": ["living_room"],
                "exclude_patterns": ["*_test"],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        errors = await engine.validate_rules()

        # Should have at least one error about no entities exposed
        # (because we excluded all areas and patterns might match)
        # But patterns and areas should be valid
        assert not any("Invalid pattern" in e for e in errors)

    @pytest.mark.asyncio
    async def test_invalid_pattern_detected(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test invalid patterns are detected."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": ["[invalid"],  # Unbalanced bracket
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        errors = await engine.validate_rules()

        assert any("Invalid pattern" in e for e in errors)

    @pytest.mark.asyncio
    async def test_invalid_area_detected(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test invalid areas are detected."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": ["nonexistent_area"],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        errors = await engine.validate_rules()

        assert any("Area not found" in e for e in errors)


class TestRuleEngineExposureReason:
    """Tests for RuleEngine.get_entity_exposure_reason method."""

    def test_entity_exclusion_reason(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test reason for result.explicit_exclusions entity exclusion."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {
                "light.kitchen": {"expose": False},
            },
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        reason = engine.get_entity_exposure_reason("light.kitchen")

        assert "Explicitly excluded" in reason
        assert "highest priority" in reason

    def test_domain_exposure_reason(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test reason for domain-based exposure."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        reason = engine.get_entity_exposure_reason("light.kitchen")

        assert "domain" in reason.lower()
        assert "light" in reason

    def test_domain_not_in_list_reason(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test reason when domain is not result.exposed."""
        stored_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],  # switch not included
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, stored_data)
        reason = engine.get_entity_exposure_reason("switch.office")

        assert "switch" in reason
        assert "not in the expose list" in reason


class TestRuleEngineUpdateData:
    """Tests for RuleEngine.update_data method."""

    @pytest.mark.asyncio
    async def test_update_data_affects_computation(
        self,
        mock_hass: MagicMock,
        mock_registries: None,
    ) -> None:
        """Test that update_data changes rule computation."""
        initial_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": [],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }

        engine = RuleEngine(mock_hass, initial_data)
        result1 = await engine.compute_entities()
        assert len(result1.exposed) == 0  # Nothing exposed

        # Update data
        new_data: dict[str, Any] = {
            "bulk_rules": {
                "expose_domains": ["light"],
                "exclude_areas": [],
                "exclude_patterns": [],
            },
            "entity_overrides": {},
            "device_overrides": {},
        }
        engine.update_data(new_data)

        result2 = await engine.compute_entities()
        assert len(result2.exposed) > 0  # Now lights are exposed
