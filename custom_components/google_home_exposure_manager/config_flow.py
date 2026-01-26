"""Config flow for Google Home Exposure Manager."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.selector import (
    BooleanSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_AUTO_ALIASES,
    CONF_BACKUPS,
    CONF_MANAGED_FILE,
    CONF_PARENT_FILE,
    CONF_SETTINGS,
    CONF_SHOW_PANEL,
    CONFIGURATION_FILE,
    DEFAULT_AUTO_ALIASES,
    DEFAULT_BACKUPS,
    DEFAULT_SHOW_PANEL,
    DOMAIN,
    GOOGLE_ASSISTANT_FILE,
    MANAGED_ENTITIES_FILE,
    SERVICE_ACCOUNT_FILE,
)

_LOGGER: Final = logging.getLogger(__name__)


class GoogleHomeExposureManagerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Home Exposure Manager."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._service_account_data: dict[str, Any] | None = None
        self._project_id: str | None = None
        self._google_assistant_detected: bool = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            # Detect Google Assistant configuration
            await self._detect_google_assistant_config()

            if self._google_assistant_detected:
                # Google Assistant already configured, proceed to create entry
                # Create issue to guide user to configure entities
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "setup_entities",
                    is_fixable=True,
                    is_persistent=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="setup_entities",
                )
                return self.async_create_entry(
                    title="Google Home Exposure Manager",
                    data={
                        CONF_MANAGED_FILE: MANAGED_ENTITIES_FILE,
                        CONF_PARENT_FILE: GOOGLE_ASSISTANT_FILE,
                    },
                )
            # Need to set up service account
            return await self.async_step_credentials()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle service account credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            manual_placement = user_input.get("manual_placement", False)
            service_account_json = user_input.get("service_account_json", "")

            if manual_placement:
                # Check if file exists
                service_account_path = Path(self.hass.config.path(SERVICE_ACCOUNT_FILE))
                file_exists = await self.hass.async_add_executor_job(
                    service_account_path.exists
                )
                if file_exists:
                    try:
                        content = await self.hass.async_add_executor_job(
                            service_account_path.read_text, "utf-8"
                        )
                        self._service_account_data = json.loads(content)
                        self._project_id = self._service_account_data.get("project_id")
                        if self._project_id:
                            return await self.async_step_project_id()
                        errors["base"] = "missing_project_id"
                    except json.JSONDecodeError:
                        errors["base"] = "invalid_json"
                else:
                    errors["base"] = "file_not_found"
            elif service_account_json:
                try:
                    self._service_account_data = json.loads(service_account_json)

                    # Validate it looks like a service account
                    if not isinstance(self._service_account_data, dict):
                        errors["base"] = "invalid_json"
                    elif (
                        "type" in self._service_account_data
                        and self._service_account_data["type"] != "service_account"
                    ):
                        errors["base"] = "invalid_json"
                    else:
                        self._project_id = self._service_account_data.get("project_id")
                        if self._project_id:
                            # Save service account file
                            svc_path = Path(self.hass.config.path(SERVICE_ACCOUNT_FILE))
                            await self.hass.async_add_executor_job(
                                self._write_service_account,
                                svc_path,
                                service_account_json,
                            )
                            return await self.async_step_project_id()
                        errors["base"] = "missing_project_id"
                except json.JSONDecodeError:
                    errors["base"] = "invalid_json"
            else:
                # Neither option selected - show error
                errors["base"] = "no_credentials"

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Optional("service_account_json"): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                            multiline=True,
                        )
                    ),
                    vol.Optional("manual_placement", default=False): BooleanSelector(),
                }
            ),
            errors=errors,
            description_placeholders={
                "setup_guide_url": "https://www.home-assistant.io/integrations/google_assistant/"
            },
        )

    def _write_service_account(self, path: Path, content: str) -> None:
        """Write service account file securely using atomic write."""
        temp_path = path.with_suffix(".tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            # Atomic rename
            temp_path.replace(path)
        except Exception:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise

    async def async_step_project_id(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle project ID confirmation step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._project_id = user_input.get("project_id", self._project_id)

            # Create Google Assistant configuration
            try:
                await self._setup_google_assistant_config()
                # Create issue - restart required for Google Assistant config
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "restart_required",
                    is_fixable=True,
                    is_persistent=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="restart_required",
                )
                return self.async_create_entry(
                    title="Google Home Exposure Manager",
                    data={
                        CONF_MANAGED_FILE: MANAGED_ENTITIES_FILE,
                        CONF_PARENT_FILE: GOOGLE_ASSISTANT_FILE,
                    },
                )
            except Exception:
                _LOGGER.exception("Failed to write configuration")
                errors["base"] = "write_error"

        return self.async_show_form(
            step_id="project_id",
            data_schema=vol.Schema(
                {
                    vol.Required("project_id", default=self._project_id): str,
                }
            ),
            errors=errors,
            description_placeholders={"project_id": self._project_id or ""},
        )

    async def _detect_google_assistant_config(self) -> None:
        """Detect existing Google Assistant configuration."""
        config_path = Path(self.hass.config.path(CONFIGURATION_FILE))

        def _check_config() -> bool:
            if not config_path.exists():
                return False
            try:
                content = config_path.read_text(encoding="utf-8")
                return "google_assistant:" in content
            except Exception:
                return False

        self._google_assistant_detected = await self.hass.async_add_executor_job(
            _check_config
        )

    async def _setup_google_assistant_config(self) -> None:
        """Set up Google Assistant configuration files."""
        from .yaml_manager import YamlManager

        yaml_manager = YamlManager(self.hass)
        await yaml_manager.setup_google_assistant_config(self._project_id)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return GoogleHomeExposureManagerOptionsFlow()


class GoogleHomeExposureManagerOptionsFlow(OptionsFlow):
    """Handle options flow for Google Home Exposure Manager.

    This simplified options flow only handles integration settings.
    Entity exposure rules are managed through the sidebar panel.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options flow."""
        # Load current settings from storage
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if entry_data is None:
            entry_data = {}

        stored_data = entry_data.get("data", {})
        settings = stored_data.get(CONF_SETTINGS, {})

        # Compute current stats for display
        rule_engine = entry_data.get("rule_engine")
        stats_text = ""
        if rule_engine:
            try:
                exposed, excluded, _, unset, _ = await rule_engine.compute_entities(
                    stored_data
                )
                stats_text = (
                    f"**{len(exposed)}** entities exposed · "
                    f"**{len(excluded)}** excluded · "
                    f"**{len(unset)}** unset"
                )
            except Exception:
                stats_text = "Unable to compute stats"

        if user_input is not None:
            # Get old value for comparison
            old_show_panel = settings.get(CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL)
            new_show_panel = user_input.get("show_panel", DEFAULT_SHOW_PANEL)

            # Save settings
            new_settings = {
                CONF_BACKUPS: user_input.get("backups", DEFAULT_BACKUPS),
                CONF_AUTO_ALIASES: user_input.get("auto_aliases", DEFAULT_AUTO_ALIASES),
                CONF_SHOW_PANEL: new_show_panel,
            }

            # Update stored data
            stored_data[CONF_SETTINGS] = new_settings
            store = entry_data.get("store")
            if store:
                await store.async_save(stored_data)

            # Update in-memory data
            if "data" in entry_data:
                entry_data["data"] = stored_data

            # If panel visibility changed, create restart issue
            if old_show_panel != new_show_panel:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "panel_restart_required",
                    is_fixable=True,
                    is_persistent=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="panel_restart_required",
                )
                _LOGGER.info(
                    "Panel visibility changed from %s to %s - restart required",
                    old_show_panel,
                    new_show_panel,
                )

            _LOGGER.info("Settings saved")
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "backups",
                        default=settings.get(CONF_BACKUPS, DEFAULT_BACKUPS),
                    ): BooleanSelector(),
                    vol.Optional(
                        "auto_aliases",
                        default=settings.get(CONF_AUTO_ALIASES, DEFAULT_AUTO_ALIASES),
                    ): BooleanSelector(),
                    vol.Optional(
                        "show_panel",
                        default=settings.get(CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL),
                    ): BooleanSelector(),
                }
            ),
            description_placeholders={"stats_text": stats_text},
        )
