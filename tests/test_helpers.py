"""Tests for the helpers module."""
from __future__ import annotations

import pytest

from custom_components.google_home_exposure_manager.helpers import (
    ensure_dict_keys,
    get_domain_icon,
    group_entities_by_domain,
    match_glob_pattern,
    validate_glob_pattern,
)


class TestValidateGlobPattern:
    """Tests for validate_glob_pattern function."""

    def test_simple_wildcard(self) -> None:
        """Test simple * wildcard patterns."""
        assert validate_glob_pattern("*") is True
        assert validate_glob_pattern("light.*") is True
        assert validate_glob_pattern("*.test") is True
        assert validate_glob_pattern("*_battery") is True

    def test_question_mark_wildcard(self) -> None:
        """Test ? wildcard patterns."""
        assert validate_glob_pattern("light.?") is True
        assert validate_glob_pattern("switch.room?") is True

    def test_character_class(self) -> None:
        """Test [seq] character class patterns."""
        assert validate_glob_pattern("[abc]") is True
        assert validate_glob_pattern("light.[abc]_room") is True
        assert validate_glob_pattern("[a-z]") is True

    def test_unbalanced_brackets_invalid(self) -> None:
        """Test that unbalanced brackets are invalid."""
        assert validate_glob_pattern("[abc") is False
        assert validate_glob_pattern("abc]") is False
        assert validate_glob_pattern("[[") is False
        assert validate_glob_pattern("]]") is False

    def test_complex_valid_patterns(self) -> None:
        """Test complex but valid patterns."""
        assert validate_glob_pattern("sensor.*_battery") is True
        assert validate_glob_pattern("light.living_room_*") is True
        assert validate_glob_pattern("*.*") is True

    def test_empty_pattern(self) -> None:
        """Test empty pattern is valid."""
        assert validate_glob_pattern("") is True


class TestMatchGlobPattern:
    """Tests for match_glob_pattern function."""

    def test_exact_match(self) -> None:
        """Test exact string matching."""
        assert match_glob_pattern("light.kitchen", "light.kitchen") is True
        assert match_glob_pattern("light.kitchen", "light.bedroom") is False

    def test_star_wildcard(self) -> None:
        """Test * wildcard matching."""
        assert match_glob_pattern("light.kitchen", "light.*") is True
        assert match_glob_pattern("switch.kitchen", "light.*") is False
        assert match_glob_pattern("sensor.battery_level", "*_level") is True
        assert match_glob_pattern("sensor.temperature", "*_level") is False

    def test_question_mark(self) -> None:
        """Test ? single character matching."""
        assert match_glob_pattern("light.a", "light.?") is True
        assert match_glob_pattern("light.ab", "light.?") is False
        assert match_glob_pattern("light.room1", "light.room?") is True

    def test_character_class(self) -> None:
        """Test [seq] character class matching."""
        assert match_glob_pattern("a", "[abc]") is True
        assert match_glob_pattern("d", "[abc]") is False

    def test_real_world_patterns(self) -> None:
        """Test patterns that would be used in real configs."""
        # Exclude all test entities - fnmatch matches full string
        assert match_glob_pattern("light.test_entity", "light.*test*") is True
        assert match_glob_pattern("light.test", "*test*") is True
        assert match_glob_pattern("sensor.battery_test", "*_test") is True
        assert match_glob_pattern("light.something_test", "*_test") is True

        # Exclude battery sensors
        assert match_glob_pattern("sensor.phone_battery", "sensor.*_battery") is True
        assert match_glob_pattern("sensor.temperature", "sensor.*_battery") is False


class TestGetDomainIcon:
    """Tests for get_domain_icon function."""

    def test_known_domains(self) -> None:
        """Test icons for known domains."""
        assert get_domain_icon("light") == "💡"
        assert get_domain_icon("switch") == "🔌"
        assert get_domain_icon("climate") == "🌡️"
        assert get_domain_icon("lock") == "🔒"

    def test_unknown_domain(self) -> None:
        """Test default icon for unknown domains."""
        assert get_domain_icon("unknown_domain") == "▪️"
        assert get_domain_icon("custom") == "▪️"


class TestGroupEntitiesByDomain:
    """Tests for group_entities_by_domain function."""

    def test_basic_grouping(self) -> None:
        """Test basic entity grouping."""
        entities = [
            "light.kitchen",
            "light.bedroom",
            "switch.office",
            "sensor.temperature",
        ]
        result = group_entities_by_domain(entities)

        assert result == {
            "light": ["light.kitchen", "light.bedroom"],
            "switch": ["switch.office"],
            "sensor": ["sensor.temperature"],
        }

    def test_empty_list(self) -> None:
        """Test grouping empty list."""
        result = group_entities_by_domain([])
        assert result == {}

    def test_single_domain(self) -> None:
        """Test when all entities are same domain."""
        entities = ["light.a", "light.b", "light.c"]
        result = group_entities_by_domain(entities)
        assert result == {"light": ["light.a", "light.b", "light.c"]}


class TestEnsureDictKeys:
    """Tests for ensure_dict_keys function."""

    def test_none_input(self) -> None:
        """Test with None input."""
        result = ensure_dict_keys(None, {"key": "default"})
        assert result == {"key": "default"}

    def test_empty_dict(self) -> None:
        """Test with empty dict."""
        result = ensure_dict_keys({}, {"key": "default", "other": 42})
        assert result == {"key": "default", "other": 42}

    def test_partial_data(self) -> None:
        """Test with some keys present."""
        data = {"key": "existing"}
        result = ensure_dict_keys(data, {"key": "default", "other": 42})
        assert result == {"key": "existing", "other": 42}

    def test_mutable_defaults_not_shared(self) -> None:
        """Test that mutable defaults are deep copied."""
        result1 = ensure_dict_keys(None, {"list": [1, 2, 3]})
        result2 = ensure_dict_keys(None, {"list": [1, 2, 3]})

        # Modify one result
        result1["list"].append(4)

        # Other result should not be affected
        assert result2["list"] == [1, 2, 3]

    def test_nested_dict_default(self) -> None:
        """Test with nested dict default."""
        result = ensure_dict_keys(None, {"nested": {"a": 1, "b": 2}})
        assert result == {"nested": {"a": 1, "b": 2}}

        # Verify it's a copy
        result["nested"]["c"] = 3
        result2 = ensure_dict_keys(None, {"nested": {"a": 1, "b": 2}})
        assert "c" not in result2["nested"]
