"""Tests for the constants module."""
from __future__ import annotations

import pytest

from custom_components.google_home_exposure_manager.const import (
    CONF_AUTO_SYNC,
    CONF_BACKUPS,
    CONF_BULK_RULES,
    CONF_DEVICE_OVERRIDES,
    CONF_ENTITY_OVERRIDES,
    CONF_EXCLUDE_AREAS,
    CONF_EXCLUDE_PATTERNS,
    CONF_EXPOSE,
    CONF_EXPOSE_DOMAINS,
    CONF_MANAGED_FILE,
    CONF_PARENT_FILE,
    CONF_SETTINGS,
    CONF_SHOW_PANEL,
    CONFIGURATION_FILE,
    DEFAULT_AUTO_SYNC,
    DEFAULT_BACKUPS,
    DEFAULT_EXPOSE_DOMAINS,
    DEFAULT_SHOW_PANEL,
    DOMAIN,
    GOOGLE_ASSISTANT_FILE,
    MANAGED_ENTITIES_FILE,
    MANAGED_FILE_HEADER,
    SERVICE_ACCOUNT_FILE,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUPPORTED_DOMAINS,
    ConfigurationError,
    GoogleHomeExposureManagerError,
    MigrationError,
    YamlWriteError,
)


class TestConstants:
    """Test that constants have expected values."""

    def test_domain(self) -> None:
        """Test DOMAIN constant."""
        assert DOMAIN == "google_home_exposure_manager"
        assert isinstance(DOMAIN, str)

    def test_storage_version(self) -> None:
        """Test storage version is positive integer."""
        assert STORAGE_VERSION >= 1
        assert isinstance(STORAGE_VERSION, int)

    def test_storage_key_matches_domain(self) -> None:
        """Test storage key matches domain."""
        assert STORAGE_KEY == DOMAIN

    def test_file_names(self) -> None:
        """Test file name constants."""
        assert MANAGED_ENTITIES_FILE.endswith(".yaml")
        assert GOOGLE_ASSISTANT_FILE.endswith(".yaml")
        assert SERVICE_ACCOUNT_FILE.endswith(".json")
        assert CONFIGURATION_FILE.endswith(".yaml")

    def test_default_domains_list(self) -> None:
        """Test default expose domains is a list of valid domains."""
        assert isinstance(DEFAULT_EXPOSE_DOMAINS, list)
        assert len(DEFAULT_EXPOSE_DOMAINS) > 0

        # All defaults should be in supported domains
        for domain in DEFAULT_EXPOSE_DOMAINS:
            assert domain in SUPPORTED_DOMAINS

    def test_supported_domains(self) -> None:
        """Test supported domains list."""
        assert isinstance(SUPPORTED_DOMAINS, list)
        assert len(SUPPORTED_DOMAINS) > 0

        # Common domains should be included
        expected = ["light", "switch", "cover", "climate", "lock", "fan"]
        for domain in expected:
            assert domain in SUPPORTED_DOMAINS

    def test_default_booleans(self) -> None:
        """Test boolean defaults."""
        assert isinstance(DEFAULT_AUTO_SYNC, bool)
        assert isinstance(DEFAULT_BACKUPS, bool)
        assert isinstance(DEFAULT_SHOW_PANEL, bool)

    def test_managed_file_header(self) -> None:
        """Test managed file header has expected content."""
        assert MANAGED_FILE_HEADER.startswith("#")
        assert "Managed" in MANAGED_FILE_HEADER
        assert "DO NOT EDIT" in MANAGED_FILE_HEADER


class TestConfigKeys:
    """Test configuration key constants."""

    def test_config_keys_are_strings(self) -> None:
        """Test all config keys are strings."""
        config_keys = [
            CONF_MANAGED_FILE,
            CONF_PARENT_FILE,
            CONF_BULK_RULES,
            CONF_EXPOSE_DOMAINS,
            CONF_EXCLUDE_AREAS,
            CONF_EXCLUDE_PATTERNS,
            CONF_ENTITY_OVERRIDES,
            CONF_DEVICE_OVERRIDES,
            CONF_EXPOSE,
            CONF_SETTINGS,
            CONF_AUTO_SYNC,
            CONF_BACKUPS,
            CONF_SHOW_PANEL,
        ]

        for key in config_keys:
            assert isinstance(key, str)
            assert len(key) > 0

    def test_config_keys_are_unique(self) -> None:
        """Test config keys don't have collisions."""
        config_keys = [
            CONF_MANAGED_FILE,
            CONF_PARENT_FILE,
            CONF_BULK_RULES,
            CONF_EXPOSE_DOMAINS,
            CONF_EXCLUDE_AREAS,
            CONF_EXCLUDE_PATTERNS,
            CONF_ENTITY_OVERRIDES,
            CONF_DEVICE_OVERRIDES,
            CONF_EXPOSE,
            CONF_SETTINGS,
            CONF_AUTO_SYNC,
            CONF_BACKUPS,
            CONF_SHOW_PANEL,
        ]

        assert len(config_keys) == len(set(config_keys))


class TestExceptions:
    """Test custom exception classes."""

    def test_base_exception_inherits_from_ha_error(self) -> None:
        """Test GoogleHomeExposureManagerError inherits correctly."""
        from homeassistant.exceptions import HomeAssistantError

        assert issubclass(GoogleHomeExposureManagerError, HomeAssistantError)

    def test_configuration_error(self) -> None:
        """Test ConfigurationError can be raised with message."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Test error message")

        assert "Test error message" in str(exc_info.value)
        assert isinstance(exc_info.value, GoogleHomeExposureManagerError)

    def test_migration_error(self) -> None:
        """Test MigrationError can be raised with message."""
        with pytest.raises(MigrationError) as exc_info:
            raise MigrationError("Migration failed")

        assert "Migration failed" in str(exc_info.value)
        assert isinstance(exc_info.value, GoogleHomeExposureManagerError)

    def test_yaml_write_error(self) -> None:
        """Test YamlWriteError can be raised with message."""
        with pytest.raises(YamlWriteError) as exc_info:
            raise YamlWriteError("Could not write file")

        assert "Could not write file" in str(exc_info.value)
        assert isinstance(exc_info.value, GoogleHomeExposureManagerError)

    def test_exception_hierarchy(self) -> None:
        """Test exception class hierarchy."""
        # All custom exceptions should inherit from base
        assert issubclass(ConfigurationError, GoogleHomeExposureManagerError)
        assert issubclass(MigrationError, GoogleHomeExposureManagerError)
        assert issubclass(YamlWriteError, GoogleHomeExposureManagerError)

        # Can catch all with base class
        try:
            raise YamlWriteError("test")
        except GoogleHomeExposureManagerError:
            pass  # Should be caught
