"""Tests for the integration setup and lifecycle."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.google_home_exposure_manager import (
    PLATFORMS,
    async_remove_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
    _ensure_valid_stored_data,
    _register_panel,
)
from custom_components.google_home_exposure_manager.const import (
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


class TestAsyncSetup:
    """Tests for async_setup."""

    async def test_async_setup_returns_true(self) -> None:
        """Test that async_setup returns True."""
        hass = MagicMock()
        config = {}

        result = await async_setup(hass, config)

        assert result is True


class TestEnsureValidStoredData:
    """Tests for _ensure_valid_stored_data."""

    def test_none_input(self) -> None:
        """Test handling of None input."""
        result = _ensure_valid_stored_data(None)

        assert isinstance(result, dict)
        assert CONF_BULK_RULES in result
        assert CONF_ENTITY_OVERRIDES in result
        assert CONF_DEVICE_OVERRIDES in result
        assert CONF_ENTITY_CONFIG in result
        assert CONF_SETTINGS in result
        assert CONF_FILTERED_ENTITIES in result
        assert CONF_FILTERED_DEVICES in result

    def test_empty_input(self) -> None:
        """Test handling of empty dict input."""
        result = _ensure_valid_stored_data({})

        assert CONF_BULK_RULES in result
        assert isinstance(result[CONF_BULK_RULES], dict)
        assert CONF_SETTINGS in result
        assert isinstance(result[CONF_SETTINGS], dict)

    def test_partial_input(self) -> None:
        """Test handling of partial data."""
        partial_data = {
            CONF_BULK_RULES: {
                CONF_EXPOSE_DOMAINS: ["light"],
            },
        }

        result = _ensure_valid_stored_data(partial_data)

        # Should preserve existing data
        assert result[CONF_BULK_RULES][CONF_EXPOSE_DOMAINS] == ["light"]
        # Should add missing keys
        assert CONF_EXCLUDE_AREAS in result[CONF_BULK_RULES]
        assert CONF_EXCLUDE_PATTERNS in result[CONF_BULK_RULES]

    def test_nested_settings_defaults(self) -> None:
        """Test that nested settings get proper defaults."""
        result = _ensure_valid_stored_data({})

        settings = result[CONF_SETTINGS]
        assert settings[CONF_AUTO_SYNC] == DEFAULT_AUTO_SYNC
        assert settings[CONF_BACKUPS] == DEFAULT_BACKUPS
        assert settings[CONF_AUTO_ALIASES] == DEFAULT_AUTO_ALIASES
        assert settings[CONF_SHOW_PANEL] == DEFAULT_SHOW_PANEL

    def test_bulk_rules_defaults(self) -> None:
        """Test that bulk rules get proper defaults."""
        result = _ensure_valid_stored_data({})

        bulk_rules = result[CONF_BULK_RULES]
        assert bulk_rules[CONF_EXPOSE_DOMAINS] == list(DEFAULT_EXPOSE_DOMAINS)
        assert bulk_rules[CONF_EXCLUDE_AREAS] == []
        assert bulk_rules[CONF_EXCLUDE_PATTERNS] == []

    def test_preserves_existing_values(self) -> None:
        """Test that existing values are not overwritten."""
        existing_data = {
            CONF_BULK_RULES: {
                CONF_EXPOSE_DOMAINS: ["switch", "cover"],
                CONF_EXCLUDE_AREAS: ["garage"],
            },
            CONF_SETTINGS: {
                CONF_BACKUPS: False,
            },
        }

        result = _ensure_valid_stored_data(existing_data)

        # Existing values should be preserved
        assert result[CONF_BULK_RULES][CONF_EXPOSE_DOMAINS] == ["switch", "cover"]
        assert result[CONF_BULK_RULES][CONF_EXCLUDE_AREAS] == ["garage"]
        assert result[CONF_SETTINGS][CONF_BACKUPS] is False
        # Missing values should be added
        assert result[CONF_BULK_RULES][CONF_EXCLUDE_PATTERNS] == []
        assert result[CONF_SETTINGS][CONF_AUTO_SYNC] == DEFAULT_AUTO_SYNC


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {}
        hass.config.config_dir = "/config"

        async def mock_forward_entry_setups(entry, platforms):
            pass

        hass.config_entries.async_forward_entry_setups = mock_forward_entry_setups
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.async_on_unload = MagicMock()
        entry.add_update_listener = MagicMock(return_value=lambda: None)
        return entry

    async def test_setup_entry_success(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test successful setup entry."""
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value=None)
        mock_store.async_save = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with patch(
                "custom_components.google_home_exposure_manager.YamlManager"
            ):
                with patch(
                    "custom_components.google_home_exposure_manager.RuleEngine"
                ):
                    with patch(
                        "custom_components.google_home_exposure_manager.async_register_websocket_commands"
                    ):
                        with patch(
                            "custom_components.google_home_exposure_manager._register_panel",
                            new_callable=AsyncMock,
                        ):
                            result = await async_setup_entry(mock_hass, mock_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]

    async def test_setup_entry_initializes_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that setup entry initializes data correctly."""
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value=None)
        mock_store.async_save = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with patch(
                "custom_components.google_home_exposure_manager.YamlManager"
            ) as mock_yaml:
                with patch(
                    "custom_components.google_home_exposure_manager.RuleEngine"
                ) as mock_rule:
                    with patch(
                        "custom_components.google_home_exposure_manager.async_register_websocket_commands"
                    ):
                        with patch(
                            "custom_components.google_home_exposure_manager._register_panel",
                            new_callable=AsyncMock,
                        ):
                            await async_setup_entry(mock_hass, mock_entry)

        entry_data = mock_hass.data[DOMAIN][mock_entry.entry_id]
        assert "store" in entry_data
        assert "data" in entry_data
        assert "yaml_manager" in entry_data
        assert "rule_engine" in entry_data

    async def test_setup_entry_with_existing_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test setup entry with existing stored data."""
        existing_data = {
            CONF_BULK_RULES: {
                CONF_EXPOSE_DOMAINS: ["light"],
            },
        }

        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value=existing_data)
        mock_store.async_save = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with patch(
                "custom_components.google_home_exposure_manager.YamlManager"
            ):
                with patch(
                    "custom_components.google_home_exposure_manager.RuleEngine"
                ):
                    with patch(
                        "custom_components.google_home_exposure_manager.async_register_websocket_commands"
                    ):
                        with patch(
                            "custom_components.google_home_exposure_manager._register_panel",
                            new_callable=AsyncMock,
                        ):
                            await async_setup_entry(mock_hass, mock_entry)

        entry_data = mock_hass.data[DOMAIN][mock_entry.entry_id]
        # Data should be migrated and saved
        mock_store.async_save.assert_called_once()
        saved_data = mock_store.async_save.call_args[0][0]
        assert CONF_BULK_RULES in saved_data
        assert saved_data[CONF_BULK_RULES][CONF_EXPOSE_DOMAINS] == ["light"]

    async def test_setup_entry_registers_panel_when_enabled(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that setup entry registers panel when show_panel is True."""
        stored_data = {
            CONF_SETTINGS: {CONF_SHOW_PANEL: True},
        }

        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value=stored_data)
        mock_store.async_save = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with patch(
                "custom_components.google_home_exposure_manager.YamlManager"
            ):
                with patch(
                    "custom_components.google_home_exposure_manager.RuleEngine"
                ):
                    with patch(
                        "custom_components.google_home_exposure_manager.async_register_websocket_commands"
                    ):
                        with patch(
                            "custom_components.google_home_exposure_manager._register_panel",
                            new_callable=AsyncMock,
                        ) as mock_panel:
                            await async_setup_entry(mock_hass, mock_entry)

        mock_panel.assert_called_once_with(mock_hass)

    async def test_setup_entry_skips_panel_when_disabled(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that setup entry skips panel when show_panel is False."""
        stored_data = {
            CONF_SETTINGS: {CONF_SHOW_PANEL: False},
        }

        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value=stored_data)
        mock_store.async_save = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with patch(
                "custom_components.google_home_exposure_manager.YamlManager"
            ):
                with patch(
                    "custom_components.google_home_exposure_manager.RuleEngine"
                ):
                    with patch(
                        "custom_components.google_home_exposure_manager.async_register_websocket_commands"
                    ):
                        with patch(
                            "custom_components.google_home_exposure_manager._register_panel",
                            new_callable=AsyncMock,
                        ) as mock_panel:
                            await async_setup_entry(mock_hass, mock_entry)

        mock_panel.assert_not_called()

    async def test_setup_entry_raises_on_failure(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that setup entry raises ConfigEntryNotReady on failure."""
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(side_effect=Exception("Load failed"))

        with patch(
            "custom_components.google_home_exposure_manager.Store",
            return_value=mock_store,
        ):
            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(mock_hass, mock_entry)


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {DOMAIN: {"test_entry_id": {"data": {}}}}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        return entry

    async def test_unload_entry_success(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test successful unload entry."""
        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry, PLATFORMS
        )

    async def test_unload_entry_removes_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload entry removes data from hass.data."""
        await async_unload_entry(mock_hass, mock_entry)

        assert mock_entry.entry_id not in mock_hass.data[DOMAIN]

    async def test_unload_entry_failure(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test unload entry when platform unload fails."""
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is False
        # Data should NOT be removed on failure
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]


class TestAsyncRemoveEntry:
    """Tests for async_remove_entry."""

    async def test_remove_entry_logs_message(self) -> None:
        """Test that remove entry logs preservation message."""
        hass = MagicMock()
        entry = MagicMock()

        # Should complete without error
        await async_remove_entry(hass, entry)


class TestAsyncUpdateOptions:
    """Tests for async_update_options."""

    async def test_update_options_reloads_entry(self) -> None:
        """Test that update options triggers reload."""
        hass = MagicMock()
        hass.config_entries.async_reload = AsyncMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"

        await async_update_options(hass, entry)

        hass.config_entries.async_reload.assert_called_once_with("test_entry")


class TestRegisterPanel:
    """Tests for _register_panel."""

    async def test_register_panel_calls_http_and_panel_custom(self) -> None:
        """Test that register panel sets up static paths and panel."""
        hass = MagicMock()
        hass.http.async_register_static_paths = AsyncMock()

        with patch(
            "custom_components.google_home_exposure_manager.panel_custom.async_register_panel",
            new_callable=AsyncMock,
        ) as mock_panel:
            await _register_panel(hass)

        # Should register static paths
        hass.http.async_register_static_paths.assert_called_once()
        static_paths = hass.http.async_register_static_paths.call_args[0][0]
        # Should have 5 static paths (main panel + 4 modules)
        assert len(static_paths) == 5

        # Should register panel
        mock_panel.assert_called_once()
        call_kwargs = mock_panel.call_args[1]
        assert call_kwargs["webcomponent_name"] == "google-exposure-panel"
        assert call_kwargs["frontend_url_path"] == "google-exposure"
        assert call_kwargs["require_admin"] is True


class TestPlatforms:
    """Tests for platform constants."""

    def test_platforms_includes_sensor(self) -> None:
        """Test that PLATFORMS includes sensor."""
        from homeassistant.const import Platform

        assert Platform.SENSOR in PLATFORMS

    def test_platforms_count(self) -> None:
        """Test expected number of platforms."""
        assert len(PLATFORMS) == 1
