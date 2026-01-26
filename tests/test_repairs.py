"""Tests for the repairs module."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.google_home_exposure_manager.repairs import (
    AcknowledgeRepairFlow,
    async_create_fix_flow,
)


class TestAcknowledgeRepairFlow:
    """Tests for the AcknowledgeRepairFlow class."""

    @pytest.mark.asyncio
    async def test_init_step_redirects_to_confirm(self) -> None:
        """Test that init step redirects to confirm."""
        flow = AcknowledgeRepairFlow()
        flow.hass = MagicMock()
        flow.issue_id = "test_issue"

        # Mock the confirm step
        flow.async_step_confirm = AsyncMock(return_value={"type": "form"})

        result = await flow.async_step_init()

        flow.async_step_confirm.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_confirm_step_shows_form(self) -> None:
        """Test that confirm step shows a form when no input."""
        flow = AcknowledgeRepairFlow()
        flow.hass = MagicMock()
        flow.issue_id = "test_issue"

        result = await flow.async_step_confirm(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

    @pytest.mark.asyncio
    async def test_confirm_step_deletes_issue_on_submit(self) -> None:
        """Test that submitting confirm deletes the issue."""
        flow = AcknowledgeRepairFlow()
        flow.hass = MagicMock()
        flow.issue_id = "test_issue"

        with patch(
            "custom_components.google_home_exposure_manager.repairs.ir.async_delete_issue"
        ) as mock_delete:
            result = await flow.async_step_confirm(user_input={})

            mock_delete.assert_called_once_with(
                flow.hass,
                "google_home_exposure_manager",
                "test_issue",
            )

        assert result["type"] == "create_entry"


class TestAsyncCreateFixFlow:
    """Tests for async_create_fix_flow function."""

    @pytest.mark.asyncio
    async def test_restart_required_returns_acknowledge_flow(self) -> None:
        """Test restart_required issue returns AcknowledgeRepairFlow."""
        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "restart_required", None)

        assert isinstance(flow, AcknowledgeRepairFlow)

    @pytest.mark.asyncio
    async def test_setup_entities_returns_acknowledge_flow(self) -> None:
        """Test setup_entities issue returns AcknowledgeRepairFlow."""
        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "setup_entities", None)

        assert isinstance(flow, AcknowledgeRepairFlow)

    @pytest.mark.asyncio
    async def test_restart_after_update_returns_acknowledge_flow(self) -> None:
        """Test restart_after_update issue returns AcknowledgeRepairFlow."""
        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "restart_after_update", None)

        assert isinstance(flow, AcknowledgeRepairFlow)

    @pytest.mark.asyncio
    async def test_panel_restart_required_returns_acknowledge_flow(self) -> None:
        """Test panel_restart_required issue returns AcknowledgeRepairFlow."""
        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "panel_restart_required", None)

        assert isinstance(flow, AcknowledgeRepairFlow)

    @pytest.mark.asyncio
    async def test_unknown_issue_returns_confirm_flow(self) -> None:
        """Test unknown issue returns ConfirmRepairFlow."""
        from homeassistant.components.repairs import ConfirmRepairFlow

        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "unknown_issue", None)

        assert isinstance(flow, ConfirmRepairFlow)

    @pytest.mark.asyncio
    async def test_data_parameter_accepted(self) -> None:
        """Test that data parameter is accepted even if unused."""
        hass = MagicMock()
        data: dict[str, Any] = {"key": "value", "number": 42}

        # Should not raise
        flow = await async_create_fix_flow(hass, "restart_required", data)

        assert isinstance(flow, AcknowledgeRepairFlow)
