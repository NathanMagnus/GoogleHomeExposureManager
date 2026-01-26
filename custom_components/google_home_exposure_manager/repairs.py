"""Repairs for Google Home Exposure Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

# Issue IDs that use the acknowledgement flow
_ACKNOWLEDGEMENT_ISSUES = frozenset(
    {
        "restart_required",
        "setup_entities",
        "restart_after_update",
        "panel_restart_required",
    }
)


class AcknowledgeRepairFlow(RepairsFlow):
    """Generic repair flow that just requires user acknowledgement.

    Used for issues that inform the user about something but don't require
    any specific action beyond acknowledging the message.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step - redirect to confirm."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle user acknowledgement.

        When the user submits the form, the issue is deleted and the flow completes.
        """
        if user_input is not None:
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create repair flow for an issue.

    Args:
        hass: The Home Assistant instance.
        issue_id: The issue identifier.
        data: Optional data associated with the issue.

    Returns:
        The appropriate RepairsFlow for the issue.
    """
    if issue_id in _ACKNOWLEDGEMENT_ISSUES:
        return AcknowledgeRepairFlow()
    return ConfirmRepairFlow()
