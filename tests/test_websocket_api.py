"""Tests for the websocket_api module."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.google_home_exposure_manager.websocket_api import (
    _get_entry_data,
    require_entry_data,
)
from custom_components.google_home_exposure_manager.const import DOMAIN


class TestGetEntryData:
    """Tests for _get_entry_data function."""

    def test_returns_entry_data_when_found(self) -> None:
        """Test that entry data is returned when available."""
        mock_hass = MagicMock()
        entry_data = {"store": MagicMock(), "data": {}}
        mock_hass.data = {
            DOMAIN: {
                "entry_123": entry_data,
                "websocket_registered": True,
            }
        }

        result = _get_entry_data(mock_hass)

        assert result == entry_data

    def test_returns_none_when_domain_not_in_data(self) -> None:
        """Test that None is returned when domain is not present."""
        mock_hass = MagicMock()
        mock_hass.data = {}

        result = _get_entry_data(mock_hass)

        assert result is None

    def test_skips_websocket_registered_key(self) -> None:
        """Test that websocket_registered key is skipped."""
        mock_hass = MagicMock()
        mock_hass.data = {
            DOMAIN: {
                "websocket_registered": True,
            }
        }

        result = _get_entry_data(mock_hass)

        assert result is None

    def test_skips_non_dict_entries(self) -> None:
        """Test that non-dict entries are skipped."""
        mock_hass = MagicMock()
        mock_hass.data = {
            DOMAIN: {
                "some_string": "not a dict",
                "websocket_registered": True,
            }
        }

        result = _get_entry_data(mock_hass)

        assert result is None


class TestRequireEntryDataDecorator:
    """Tests for require_entry_data decorator."""

    @pytest.mark.asyncio
    async def test_sends_error_when_entry_data_missing(self) -> None:
        """Test that error is sent when entry_data is missing."""
        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_connection = MagicMock()
        msg = {"id": 1, "type": "test"}

        @require_entry_data
        async def test_handler(
            hass: Any,
            connection: Any,
            msg: dict[str, Any],
            entry_data: dict[str, Any],
        ) -> None:
            pass

        await test_handler(mock_hass, mock_connection, msg)

        mock_connection.send_error.assert_called_once_with(
            1, "not_found", "Integration not set up"
        )

    @pytest.mark.asyncio
    async def test_injects_entry_data_when_available(self) -> None:
        """Test that entry_data is injected when available."""
        mock_hass = MagicMock()
        entry_data = {"store": MagicMock(), "data": {"test": "value"}}
        mock_hass.data = {DOMAIN: {"entry_123": entry_data}}
        mock_connection = MagicMock()
        msg = {"id": 1, "type": "test"}
        received_entry_data = None

        @require_entry_data
        async def test_handler(
            hass: Any,
            connection: Any,
            msg: dict[str, Any],
            entry_data: dict[str, Any],
        ) -> None:
            nonlocal received_entry_data
            received_entry_data = entry_data

        await test_handler(mock_hass, mock_connection, msg)

        assert received_entry_data == entry_data
        mock_connection.send_error.assert_not_called()
