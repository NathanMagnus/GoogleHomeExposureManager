"""Rule engine for Google Home Exposure Manager."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)

from .const import (
    CONF_BULK_RULES,
    CONF_DEVICE_OVERRIDES,
    CONF_ENTITY_OVERRIDES,
    CONF_EXCLUDE_AREAS,
    CONF_EXCLUDE_PATTERNS,
    CONF_EXPOSE,
    CONF_EXPOSE_DOMAINS,
    SUPPORTED_DOMAINS,
)
from .helpers import (
    group_entities_by_domain,
    match_glob_pattern,
    validate_glob_pattern,
)

_LOGGER: Final = logging.getLogger(__name__)


class RuleEngine:
    """Engine to compute entity exposure based on rules.

    This class implements the rule evaluation logic for determining which
    entities should be exposed to Google Assistant. Rules are evaluated
    with the following priority (exclusions always win):

    1. Entity exclusions (absolute priority)
    2. Device exclusions (absolute priority)
    3. Entity inclusions
    4. Device inclusions
    5. Domain rules, area exclusions, pattern exclusions
    """

    def __init__(self, hass: HomeAssistant, stored_data: dict[str, Any]) -> None:
        """Initialize the rule engine.

        Args:
            hass: The Home Assistant instance.
            stored_data: The stored configuration data.
        """
        self.hass = hass
        self._stored_data = stored_data

    def update_data(self, stored_data: dict[str, Any]) -> None:
        """Update the stored data reference.

        Args:
            stored_data: The new configuration data.
        """
        self._stored_data = stored_data

    async def compute_entities(
        self, stored_data: dict[str, Any] | None = None
    ) -> tuple[list[str], list[str], set[str], list[str], dict[str, list[str]]]:
        """Compute entity exposure based on rules.

        Priority (exclusions always win over any inclusion):
        1. Entity exclusions (manual override - highest)
        2. Device exclusions (manual override)
        3. Pattern exclusions (bulk rule - applies to all)
        4. Area exclusions (bulk rule - applies to all)
        5. Entity inclusions (manual override)
        6. Device inclusions (manual override)
        7. Domain rules (bulk rule - lowest)

        Args:
            stored_data: Configuration data to use. Defaults to stored data.

        Returns:
            Tuple of (exposed, excluded, explicit_exclusions, unset, exclusion_reasons).
            exclusion_reasons maps reason type to list of entity IDs.
        """
        if stored_data is None:
            stored_data = self._stored_data

        bulk_rules = stored_data.get(CONF_BULK_RULES, {})
        entity_overrides = stored_data.get(CONF_ENTITY_OVERRIDES, {})
        device_overrides = stored_data.get(CONF_DEVICE_OVERRIDES, {})

        expose_domains = set(bulk_rules.get(CONF_EXPOSE_DOMAINS, []))
        exclude_areas = set(bulk_rules.get(CONF_EXCLUDE_AREAS, []))
        exclude_patterns: list[str] = bulk_rules.get(CONF_EXCLUDE_PATTERNS, [])

        # Get registries
        entity_reg = er.async_get(self.hass)
        device_reg = dr.async_get(self.hass)

        # Build lookup maps
        device_areas: dict[str, str | None] = {
            device.id: device.area_id for device in device_reg.devices.values()
        }

        # Helper to check if override is "selected" (explicit user choice)
        # "implied" overrides are computed from device state and should be ignored
        # Legacy data without "source" is treated as "selected" for backwards compat
        def is_selected_override(data: dict[str, Any]) -> bool:
            source = data.get("source", "selected")  # Legacy = selected
            return source != "implied"

        expose_devices = {
            did
            for did, data in device_overrides.items()
            if data.get(CONF_EXPOSE) is True and is_selected_override(data)
        }
        exclude_devices = {
            did
            for did, data in device_overrides.items()
            if data.get(CONF_EXPOSE) is False and is_selected_override(data)
        }
        exclude_entities_set = {
            eid
            for eid, data in entity_overrides.items()
            if data.get(CONF_EXPOSE) is False and is_selected_override(data)
        }
        expose_entities_set = {
            eid
            for eid, data in entity_overrides.items()
            if data.get(CONF_EXPOSE) is True and is_selected_override(data)
        }

        exposed_entities: list[str] = []
        excluded_entities: list[str] = []
        explicit_exclusions: set[str] = set()
        unset_entities: list[str] = []
        exclusion_reasons: dict[str, list[str]] = {
            "entity_override": [],
            "device_override": [],
            "area": [],
            "pattern": [],
        }

        # Process all entities
        for entity in entity_reg.entities.values():
            entity_id = entity.entity_id
            domain = entity_id.split(".")[0]

            # Skip unsupported/disabled/hidden entities
            if domain not in SUPPORTED_DOMAINS:
                continue
            if entity.disabled:
                continue
            if entity.entity_category is not None:
                continue
            if entity.hidden_by is not None:
                continue

            # 1. Check explicit entity exclusions (highest priority)
            if entity_id in exclude_entities_set:
                excluded_entities.append(entity_id)
                explicit_exclusions.add(entity_id)
                exclusion_reasons["entity_override"].append(entity_id)
                continue

            # 2. Check device exclusions
            if entity.device_id and entity.device_id in exclude_devices:
                excluded_entities.append(entity_id)
                explicit_exclusions.add(entity_id)
                exclusion_reasons["device_override"].append(entity_id)
                continue

            # 3. Check pattern exclusions (applies to ALL entities)
            if self._matches_any_pattern(entity_id, exclude_patterns):
                excluded_entities.append(entity_id)
                exclusion_reasons["pattern"].append(entity_id)
                continue

            # 4. Check area exclusions (applies to ALL entities)
            entity_area = self._get_entity_area(entity, device_areas)
            if entity_area and entity_area in exclude_areas:
                excluded_entities.append(entity_id)
                exclusion_reasons["area"].append(entity_id)
                continue

            # 5. Check explicit entity inclusions
            if entity_id in expose_entities_set:
                exposed_entities.append(entity_id)
                continue

            # 6. Check device inclusions
            if entity.device_id and entity.device_id in expose_devices:
                exposed_entities.append(entity_id)
                continue

            # 7. Apply domain rules (lowest priority)
            if domain not in expose_domains:
                unset_entities.append(entity_id)
                continue

            exposed_entities.append(entity_id)

        _LOGGER.debug(
            "Computed entities: %d exposed, %d excluded, %d explicit exclusions, %d unset",
            len(exposed_entities),
            len(excluded_entities),
            len(explicit_exclusions),
            len(unset_entities),
        )
        return (
            exposed_entities,
            excluded_entities,
            explicit_exclusions,
            unset_entities,
            exclusion_reasons,
        )

    def _get_entity_area(
        self,
        entity: er.RegistryEntry,
        device_areas: dict[str, str | None],
    ) -> str | None:
        """Get area ID for an entity (direct assignment or via device).

        Args:
            entity: The entity registry entry.
            device_areas: Mapping of device IDs to area IDs.

        Returns:
            The area ID or None if not assigned.
        """
        if entity.area_id:
            return entity.area_id
        if entity.device_id and entity.device_id in device_areas:
            return device_areas[entity.device_id]
        return None

    def _matches_any_pattern(self, entity_id: str, patterns: list[str]) -> bool:
        """Check if an entity ID matches any of the patterns.

        Args:
            entity_id: The entity ID to check.
            patterns: List of glob patterns.

        Returns:
            True if any pattern matches.
        """
        return any(match_glob_pattern(entity_id, p) for p in patterns)

    async def validate_rules(
        self, stored_data: dict[str, Any] | None = None
    ) -> list[str]:
        """Validate rules and return error messages (empty if valid).

        Args:
            stored_data: Configuration data to validate.

        Returns:
            List of error messages, empty if all rules are valid.
        """
        if stored_data is None:
            stored_data = self._stored_data

        errors: list[str] = []
        bulk_rules = stored_data.get(CONF_BULK_RULES, {})
        entity_overrides = stored_data.get(CONF_ENTITY_OVERRIDES, {})

        # Validate patterns
        patterns: list[str] = bulk_rules.get(CONF_EXCLUDE_PATTERNS, [])
        for pattern in patterns:
            if not validate_glob_pattern(pattern):
                errors.append(f"Invalid pattern: `{pattern}` — check syntax")

        # Validate areas (try by ID first, then by name)
        area_reg = ar.async_get(self.hass)
        exclude_areas: list[str] = bulk_rules.get(CONF_EXCLUDE_AREAS, [])
        for area_id in exclude_areas:
            if area_reg.async_get_area(area_id) is None:
                found = any(
                    area.name.lower() == area_id.lower()
                    for area in area_reg.async_list_areas()
                )
                if not found:
                    errors.append(f"Area not found: `{area_id}`")

        # Check for entity conflicts
        expose_overrides = {
            eid
            for eid, data in entity_overrides.items()
            if data.get(CONF_EXPOSE) is True
        }
        exclude_overrides = {
            eid
            for eid, data in entity_overrides.items()
            if data.get(CONF_EXPOSE) is False
        }
        conflicts = expose_overrides & exclude_overrides
        for conflict in conflicts:
            errors.append(f"Conflict: `{conflict}` is in both expose and exclude")

        # Check that at least one entity would be exposed
        exposed, _, _, _, _ = await self.compute_entities(stored_data)
        if not exposed:
            errors.append("No entities will be exposed — add domains or entities")

        if errors:
            _LOGGER.warning("Rule validation errors: %s", errors)

        return errors

    async def get_entity_summary(
        self, stored_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get exposure statistics and grouped entities for preview.

        Args:
            stored_data: Configuration data to use.

        Returns:
            Summary with totals, entities grouped by domain, and samples.
        """
        if stored_data is None:
            stored_data = self._stored_data

        exposed, excluded, _, _, exclusion_reasons = await self.compute_entities(
            stored_data
        )
        exposed_by_domain = group_entities_by_domain(exposed)
        excluded_by_domain = group_entities_by_domain(excluded)

        return {
            "total_exposed": len(exposed),
            "total_excluded": len(excluded),
            "exposed_entities": exposed,
            "excluded_entities": excluded,
            "exposed_by_domain": exposed_by_domain,
            "excluded_by_domain": excluded_by_domain,
            "exclusion_reasons": exclusion_reasons,
            "sample_exposed": exposed[:20],
            "sample_excluded": excluded[:10],
        }

    def get_entity_exposure_reason(
        self,
        entity_id: str,
        stored_data: dict[str, Any] | None = None,
    ) -> str:
        """Get the reason why an entity is exposed or excluded."""
        if stored_data is None:
            stored_data = self._stored_data

        bulk_rules = stored_data.get(CONF_BULK_RULES, {})
        entity_overrides = stored_data.get(CONF_ENTITY_OVERRIDES, {})
        device_overrides = stored_data.get(CONF_DEVICE_OVERRIDES, {})

        domain = entity_id.split(".")[0]

        # Helper to check if override is "selected" (explicit user choice)
        def is_selected(data: dict[str, Any]) -> bool:
            source = data.get("source", "selected")
            return source != "implied"

        # Check explicit entity exclusion first (absolute priority)
        if entity_id in entity_overrides:
            override = entity_overrides[entity_id]
            if override.get(CONF_EXPOSE) is False and is_selected(override):
                return "Explicitly excluded (entity exclusion - highest priority)"

        # Check device exclusion (absolute priority)
        entity_reg = er.async_get(self.hass)
        entity_entry = entity_reg.async_get(entity_id)
        if entity_entry and entity_entry.device_id:
            device_id = entity_entry.device_id
            if device_id in device_overrides:
                override = device_overrides[device_id]
                if override.get(CONF_EXPOSE) is False and is_selected(override):
                    return (
                        "Excluded via device rule (device exclusion - highest priority)"
                    )

        # Check explicit entity inclusion
        if entity_id in entity_overrides:
            override = entity_overrides[entity_id]
            if override.get(CONF_EXPOSE) is True and is_selected(override):
                return "Explicitly set to expose (individual entity rule)"

        # Check device inclusion
        if entity_entry and entity_entry.device_id:
            device_id = entity_entry.device_id
            if device_id in device_overrides:
                override = device_overrides[device_id]
                if override.get(CONF_EXPOSE) is True and is_selected(override):
                    return "Exposed via device rule (all entities from this device)"

        # Check domain
        expose_domains = set(bulk_rules.get(CONF_EXPOSE_DOMAINS, []))
        if domain not in expose_domains:
            return f"Domain '{domain}' is not in the expose list"

        # Check patterns
        patterns = bulk_rules.get(CONF_EXCLUDE_PATTERNS, [])
        for pattern in patterns:
            if match_glob_pattern(entity_id, pattern):
                return f"Matches exclude pattern: {pattern}"

        # Check area (would need entity registry lookup)
        return f"Exposed via domain '{domain}' bulk rule"
