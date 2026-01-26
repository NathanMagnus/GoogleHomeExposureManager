"""Tests for the config flow."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.google_home_exposure_manager.config_flow import (
    GoogleHomeExposureManagerConfigFlow,
    GoogleHomeExposureManagerOptionsFlow,
)
from custom_components.google_home_exposure_manager.const import (
    CONF_AUTO_ALIASES,
    CONF_BACKUPS,
    CONF_MANAGED_FILE,
    CONF_PARENT_FILE,
    CONF_SETTINGS,
    CONF_SHOW_PANEL,
    DOMAIN,
    GOOGLE_ASSISTANT_FILE,
    MANAGED_ENTITIES_FILE,
)


@pytest.fixture
def mock_setup_entry() -> AsyncMock:
    """Mock async_setup_entry."""
    with patch(
        "custom_components.google_home_exposure_manager.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


class TestConfigFlow:
    """Tests for GoogleHomeExposureManagerConfigFlow."""

    async def test_flow_init(self) -> None:
        """Test the config flow initializes correctly."""
        flow = GoogleHomeExposureManagerConfigFlow()
        assert flow._service_account_data is None
        assert flow._project_id is None
        assert flow._google_assistant_detected is False

    async def test_user_step_already_configured(self) -> None:
        """Test user step when already configured."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()

        # Mock that an entry already exists
        flow._async_current_entries = MagicMock(return_value=[MagicMock()])

        result = await flow.async_step_user(user_input={})

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"

    async def test_user_step_shows_form(self) -> None:
        """Test user step shows form when no input provided."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_user_step_google_assistant_detected(self) -> None:
        """Test user step when Google Assistant is already configured."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        # Mock detection of existing Google Assistant config
        with patch.object(
            flow, "_detect_google_assistant_config", new_callable=AsyncMock
        ) as mock_detect:
            async def set_detected():
                flow._google_assistant_detected = True

            mock_detect.side_effect = set_detected

            with patch(
                "custom_components.google_home_exposure_manager.config_flow.ir.async_create_issue"
            ):
                result = await flow.async_step_user(user_input={})

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Google Home Exposure Manager"
        assert result["data"][CONF_MANAGED_FILE] == MANAGED_ENTITIES_FILE
        assert result["data"][CONF_PARENT_FILE] == GOOGLE_ASSISTANT_FILE

    async def test_user_step_no_google_assistant(self) -> None:
        """Test user step redirects to credentials when GA not found."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        # Mock no existing Google Assistant config
        with patch.object(
            flow, "_detect_google_assistant_config", new_callable=AsyncMock
        ):
            with patch.object(
                flow, "async_step_credentials", new_callable=AsyncMock
            ) as mock_creds:
                mock_creds.return_value = {"type": FlowResultType.FORM}
                result = await flow.async_step_user(user_input={})

        assert result["type"] == FlowResultType.FORM


class TestCredentialsStep:
    """Tests for the credentials step."""

    async def test_credentials_step_shows_form(self) -> None:
        """Test credentials step shows form when no input."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_credentials(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "credentials"
        assert "errors" in result
        assert result["errors"] == {}

    async def test_credentials_step_no_input_error(self) -> None:
        """Test credentials step with empty input shows error."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_credentials(
            user_input={"manual_placement": False, "service_account_json": ""}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "no_credentials"

    async def test_credentials_step_invalid_json(self) -> None:
        """Test credentials step with invalid JSON shows error."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_credentials(
            user_input={"service_account_json": "not valid json"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_json"

    async def test_credentials_step_missing_project_id(self) -> None:
        """Test credentials step with JSON missing project_id."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_credentials(
            user_input={"service_account_json": '{"type": "service_account"}'}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "missing_project_id"

    async def test_credentials_step_manual_file_not_found(self) -> None:
        """Test credentials step when manual file doesn't exist."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config.path = lambda x: f"/config/{x}"

        async def mock_executor(func, *args):
            return func(*args) if not callable(func) else func()

        flow.hass.async_add_executor_job = mock_executor

        with patch("pathlib.Path.exists", return_value=False):
            result = await flow.async_step_credentials(
                user_input={"manual_placement": True}
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "file_not_found"

    async def test_credentials_step_valid_json(self) -> None:
        """Test credentials step with valid service account JSON."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config.path = lambda x: f"/config/{x}"

        async def mock_executor(func, *args):
            return func(*args)

        flow.hass.async_add_executor_job = mock_executor

        valid_json = json.dumps({
            "type": "service_account",
            "project_id": "my-project-123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        })

        with patch.object(flow, "_write_service_account"):
            with patch.object(
                flow, "async_step_project_id", new_callable=AsyncMock
            ) as mock_project:
                mock_project.return_value = {"type": FlowResultType.FORM}
                result = await flow.async_step_credentials(
                    user_input={"service_account_json": valid_json}
                )

        assert flow._project_id == "my-project-123"
        mock_project.assert_called_once()


class TestProjectIdStep:
    """Tests for the project_id step."""

    async def test_project_id_step_shows_form(self) -> None:
        """Test project_id step shows form when no input."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._project_id = "test-project"

        result = await flow.async_step_project_id(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "project_id"

    async def test_project_id_step_creates_entry(self) -> None:
        """Test project_id step creates config entry on success."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._project_id = "test-project"

        with patch.object(
            flow, "_setup_google_assistant_config", new_callable=AsyncMock
        ):
            with patch(
                "custom_components.google_home_exposure_manager.config_flow.ir.async_create_issue"
            ):
                result = await flow.async_step_project_id(
                    user_input={"project_id": "test-project"}
                )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Google Home Exposure Manager"

    async def test_project_id_step_handles_write_error(self) -> None:
        """Test project_id step handles configuration write errors."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow._project_id = "test-project"

        with patch.object(
            flow,
            "_setup_google_assistant_config",
            new_callable=AsyncMock,
            side_effect=Exception("Write failed"),
        ):
            result = await flow.async_step_project_id(
                user_input={"project_id": "test-project"}
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "write_error"


class TestOptionsFlow:
    """Tests for GoogleHomeExposureManagerOptionsFlow."""

    async def test_options_flow_shows_form(self) -> None:
        """Test options flow shows form with current settings."""
        flow = GoogleHomeExposureManagerOptionsFlow()
        flow.hass = MagicMock()
        
        # Mock the config_entry property to avoid HA's initialization check
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        with patch.object(
            type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_entry)
        ):
            flow.hass.data = {
                DOMAIN: {
                    "test_entry_id": {
                        "data": {
                            CONF_SETTINGS: {
                                CONF_BACKUPS: True,
                                CONF_AUTO_ALIASES: False,
                                CONF_SHOW_PANEL: True,
                            }
                        },
                        "rule_engine": None,
                    }
                }
            }

            result = await flow.async_step_init(user_input=None)

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "init"

    async def test_options_flow_saves_settings(self) -> None:
        """Test options flow saves settings correctly."""
        mock_store = MagicMock()
        mock_store.async_save = AsyncMock()

        flow = GoogleHomeExposureManagerOptionsFlow()
        flow.hass = MagicMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        with patch.object(
            type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_entry)
        ):
            flow.hass.data = {
                DOMAIN: {
                    "test_entry_id": {
                        "data": {
                            CONF_SETTINGS: {
                                CONF_BACKUPS: True,
                                CONF_AUTO_ALIASES: False,
                                CONF_SHOW_PANEL: True,
                            }
                        },
                        "rule_engine": None,
                        "store": mock_store,
                    }
                }
            }

            result = await flow.async_step_init(
                user_input={
                    "backups": False,
                    "auto_aliases": True,
                    "show_panel": True,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            mock_store.async_save.assert_called_once()

    async def test_options_flow_panel_change_creates_issue(self) -> None:
        """Test that changing panel visibility creates a restart issue."""
        mock_store = MagicMock()
        mock_store.async_save = AsyncMock()

        flow = GoogleHomeExposureManagerOptionsFlow()
        flow.hass = MagicMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        with patch.object(
            type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_entry)
        ):
            flow.hass.data = {
                DOMAIN: {
                    "test_entry_id": {
                        "data": {
                            CONF_SETTINGS: {
                                CONF_BACKUPS: True,
                                CONF_AUTO_ALIASES: False,
                                CONF_SHOW_PANEL: True,  # Currently enabled
                            }
                        },
                        "rule_engine": None,
                        "store": mock_store,
                    }
                }
            }

            with patch(
                "custom_components.google_home_exposure_manager.config_flow.ir.async_create_issue"
            ) as mock_issue:
                result = await flow.async_step_init(
                    user_input={
                        "backups": True,
                        "auto_aliases": False,
                        "show_panel": False,  # Changed to disabled
                    }
                )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            mock_issue.assert_called_once()

    async def test_options_flow_with_rule_engine_stats(self) -> None:
        """Test options flow displays stats from rule engine."""
        mock_rule_engine = MagicMock()
        mock_rule_engine.compute_entities = AsyncMock(
            return_value=(
                ["light.one", "light.two"],  # exposed
                ["sensor.excluded"],  # excluded
                set(),  # explicit_exclusions
                ["fan.unset"],  # unset
                {},  # exclusion_reasons
            )
        )

        flow = GoogleHomeExposureManagerOptionsFlow()
        flow.hass = MagicMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        with patch.object(
            type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_entry)
        ):
            flow.hass.data = {
                DOMAIN: {
                    "test_entry_id": {
                        "data": {CONF_SETTINGS: {}},
                        "rule_engine": mock_rule_engine,
                    }
                }
            }

            result = await flow.async_step_init(user_input=None)

            assert result["type"] == FlowResultType.FORM
            assert "stats_text" in result["description_placeholders"]
            # Stats should show: 2 exposed, 1 excluded, 1 unset
            stats = result["description_placeholders"]["stats_text"]
            assert "2" in stats  # exposed count


class TestDetectGoogleAssistant:
    """Tests for Google Assistant detection."""

    async def test_detect_ga_config_not_found(self) -> None:
        """Test detection when configuration.yaml doesn't exist."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config.path = lambda x: f"/config/{x}"

        async def mock_executor(func, *args):
            return func(*args)

        flow.hass.async_add_executor_job = mock_executor

        with patch("pathlib.Path.exists", return_value=False):
            await flow._detect_google_assistant_config()

        assert flow._google_assistant_detected is False

    async def test_detect_ga_config_found(self) -> None:
        """Test detection when google_assistant is in configuration."""
        flow = GoogleHomeExposureManagerConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config.path = lambda x: f"/config/{x}"

        async def mock_executor(func, *args):
            return func(*args)

        flow.hass.async_add_executor_job = mock_executor

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.read_text",
                return_value="google_assistant: !include google_assistant.yaml",
            ):
                await flow._detect_google_assistant_config()

        assert flow._google_assistant_detected is True


class TestWriteServiceAccount:
    """Tests for service account file writing."""

    def test_write_service_account_success(self, tmp_path: Path) -> None:
        """Test successful service account file write."""
        flow = GoogleHomeExposureManagerConfigFlow()
        target_path = tmp_path / "SERVICE_ACCOUNT.json"
        content = '{"project_id": "test"}'

        flow._write_service_account(target_path, content)

        assert target_path.exists()
        assert target_path.read_text() == content

    def test_write_service_account_atomic(self, tmp_path: Path) -> None:
        """Test that write is atomic (no partial files on failure)."""
        flow = GoogleHomeExposureManagerConfigFlow()
        target_path = tmp_path / "SERVICE_ACCOUNT.json"

        # First, write a file successfully
        flow._write_service_account(target_path, '{"first": true}')
        assert target_path.read_text() == '{"first": true}'

        # Now simulate the temp file existing but failing during write
        # The original should remain unchanged if atomic write fails properly
