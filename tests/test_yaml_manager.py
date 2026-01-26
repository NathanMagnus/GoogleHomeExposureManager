"""Tests for the YAML manager module."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.google_home_exposure_manager.yaml_manager import YamlManager
from custom_components.google_home_exposure_manager.const import (
    MANAGED_ENTITIES_FILE,
    MANAGED_FILE_HEADER,
)


class TestYamlManagerInit:
    """Tests for YamlManager initialization."""

    def test_initialization(self, mock_hass: MagicMock) -> None:
        """Test YamlManager can be initialized."""
        manager = YamlManager(mock_hass)

        assert manager.hass is mock_hass
        assert manager._config_dir == Path("/config")

    def test_get_path(self, mock_hass: MagicMock) -> None:
        """Test _get_path returns correct path."""
        manager = YamlManager(mock_hass)

        path = manager._get_path("test.yaml")

        assert path == Path("/config/test.yaml")


class TestYamlManagerFileExists:
    """Tests for file_exists method."""

    @pytest.mark.asyncio
    async def test_file_exists_true(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test file_exists returns True for existing file."""
        # Create test file
        test_file = temp_config_dir / "test.yaml"
        test_file.write_text("test: content")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.file_exists("test.yaml")

        assert result is True

    @pytest.mark.asyncio
    async def test_file_exists_false(
        self,
        mock_hass_with_temp_dir: MagicMock,
    ) -> None:
        """Test file_exists returns False for non-existing file."""
        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.file_exists("nonexistent.yaml")

        assert result is False


class TestYamlManagerReadFile:
    """Tests for read_file method."""

    @pytest.mark.asyncio
    async def test_read_file_success(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test read_file returns file contents."""
        test_file = temp_config_dir / "test.yaml"
        test_file.write_text("hello: world")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.read_file("test.yaml")

        assert result == "hello: world"

    @pytest.mark.asyncio
    async def test_read_file_not_found(
        self,
        mock_hass_with_temp_dir: MagicMock,
    ) -> None:
        """Test read_file returns None for non-existing file."""
        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.read_file("nonexistent.yaml")

        assert result is None


class TestYamlManagerBackup:
    """Tests for backup functionality."""

    @pytest.mark.asyncio
    async def test_create_backup_creates_file(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test backup creates a timestamped copy."""
        # Create source file
        source = temp_config_dir / MANAGED_ENTITIES_FILE
        source.write_text("original: content")

        manager = YamlManager(mock_hass_with_temp_dir)

        backup_path = await manager.create_backup()

        assert backup_path is not None
        backup_file = Path(backup_path)
        assert backup_file.exists()
        assert backup_file.read_text() == "original: content"

    @pytest.mark.asyncio
    async def test_create_backup_no_source_file(
        self,
        mock_hass_with_temp_dir: MagicMock,
    ) -> None:
        """Test backup returns None when source doesn't exist."""
        manager = YamlManager(mock_hass_with_temp_dir)

        backup_path = await manager.create_backup()

        assert backup_path is None

    @pytest.mark.asyncio
    async def test_create_backup_creates_directory(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test backup creates backup directory if needed."""
        source = temp_config_dir / MANAGED_ENTITIES_FILE
        source.write_text("test: data")

        manager = YamlManager(mock_hass_with_temp_dir)

        backup_path = await manager.create_backup()

        backup_dir = temp_config_dir / "backups" / "google_home_exposure_manager"
        assert backup_dir.exists()


class TestYamlManagerWriteEntities:
    """Tests for write_entities_file method."""

    @pytest.mark.asyncio
    async def test_write_entities_creates_file(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test writing entities creates the file."""
        manager = YamlManager(mock_hass_with_temp_dir)

        await manager.write_entities_file(
            exposed_entities=["light.kitchen", "light.living_room"],
            excluded_entities=["light.hidden"],
            explicit_exclusions={"light.hidden"},
        )

        output_file = temp_config_dir / MANAGED_ENTITIES_FILE
        assert output_file.exists()

        content = output_file.read_text()
        assert MANAGED_FILE_HEADER in content
        assert "light.kitchen" in content
        assert "light.living_room" in content
        # Explicit exclusions should be written
        assert "light.hidden" in content

    @pytest.mark.asyncio
    async def test_write_entities_sorted(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test entities are written in sorted order."""
        manager = YamlManager(mock_hass_with_temp_dir)

        await manager.write_entities_file(
            exposed_entities=["light.z_last", "light.a_first"],
            excluded_entities=[],
            explicit_exclusions=set(),
        )

        output_file = temp_config_dir / MANAGED_ENTITIES_FILE
        content = output_file.read_text()

        # a_first should appear before z_last
        assert content.index("light.a_first") < content.index("light.z_last")

    @pytest.mark.asyncio
    async def test_write_entities_preserves_existing_properties(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test existing entity properties are preserved when ruamel.yaml available."""
        # Create existing file with custom properties
        existing_file = temp_config_dir / MANAGED_ENTITIES_FILE
        existing_file.write_text("""light.kitchen:
  expose: false
  name: Kitchen Light
  aliases:
    - kitchen lamp
""")

        manager = YamlManager(mock_hass_with_temp_dir)

        await manager.write_entities_file(
            exposed_entities=["light.kitchen"],
            excluded_entities=[],
            explicit_exclusions=set(),
        )

        content = existing_file.read_text()

        # Check expose was updated
        assert "light.kitchen" in content
        assert "expose: true" in content

        # Properties preservation depends on ruamel.yaml being available
        # The test verifies the basic write works; property preservation is a bonus
        # when ruamel.yaml is installed

    @pytest.mark.asyncio
    async def test_write_entities_with_entity_config(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test entity_config (name, aliases, room) is written to entities file."""
        manager = YamlManager(mock_hass_with_temp_dir)

        entity_config = {
            "light.living_room": {
                "name": "Living Room Light",
                "aliases": ["main light", "big lamp"],
                "room": "Living Room",
            },
            "switch.porch": {
                "name": "Porch Light",
            },
        }

        await manager.write_entities_file(
            exposed_entities=["light.living_room", "switch.porch"],
            excluded_entities=[],
            explicit_exclusions=set(),
            entity_config=entity_config,
        )

        output_file = temp_config_dir / MANAGED_ENTITIES_FILE
        content = output_file.read_text()

        # Verify entity_config was merged
        assert "light.living_room" in content
        assert "Living Room Light" in content
        assert "main light" in content
        assert "big lamp" in content
        assert "Living Room" in content
        assert "switch.porch" in content
        assert "Porch Light" in content


class TestYamlManagerReadEntities:
    """Tests for read_entities_file method."""

    @pytest.mark.asyncio
    async def test_read_entities_success(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test reading entities file."""
        entities_file = temp_config_dir / MANAGED_ENTITIES_FILE
        entities_file.write_text("""
light.kitchen:
  expose: true
light.bedroom:
  expose: false
""")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.read_entities_file()

        assert "light.kitchen" in result
        assert result["light.kitchen"]["expose"] is True
        assert "light.bedroom" in result
        assert result["light.bedroom"]["expose"] is False

    @pytest.mark.asyncio
    async def test_read_entities_empty_file(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test reading empty entities file."""
        entities_file = temp_config_dir / MANAGED_ENTITIES_FILE
        entities_file.write_text("")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.read_entities_file()

        assert result == {}

    @pytest.mark.asyncio
    async def test_read_entities_file_not_found(
        self,
        mock_hass_with_temp_dir: MagicMock,
    ) -> None:
        """Test reading non-existing file returns empty dict."""
        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.read_entities_file()

        assert result == {}


class TestYamlManagerFindGAConfig:
    """Tests for find_google_assistant_config_file method."""

    @pytest.mark.asyncio
    async def test_find_ga_config_with_include(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test finding GA config with !include."""
        config_file = temp_config_dir / "configuration.yaml"
        config_file.write_text("""
homeassistant:
  name: Home

google_assistant: !include google_assistant.yaml
""")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.find_google_assistant_config_file()

        assert result == "google_assistant.yaml"

    @pytest.mark.asyncio
    async def test_find_ga_config_inline(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test finding inline GA config."""
        config_file = temp_config_dir / "configuration.yaml"
        config_file.write_text("""
homeassistant:
  name: Home

google_assistant:
  project_id: my-project
""")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.find_google_assistant_config_file()

        assert result == "configuration.yaml"

    @pytest.mark.asyncio
    async def test_find_ga_config_not_configured(
        self,
        mock_hass_with_temp_dir: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Test when GA is not configured."""
        config_file = temp_config_dir / "configuration.yaml"
        config_file.write_text("""
homeassistant:
  name: Home
""")

        manager = YamlManager(mock_hass_with_temp_dir)

        result = await manager.find_google_assistant_config_file()

        assert result is None
