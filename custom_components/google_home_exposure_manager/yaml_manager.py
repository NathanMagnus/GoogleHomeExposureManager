"""YAML file management for Google Home Exposure Manager."""

from __future__ import annotations

import logging
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from homeassistant.core import HomeAssistant

from .const import (
    CONFIGURATION_FILE,
    GOOGLE_ASSISTANT_FILE,
    MANAGED_ENTITIES_FILE,
    MANAGED_FILE_HEADER,
    SERVICE_ACCOUNT_FILE,
    YamlWriteError,
)

if TYPE_CHECKING:
    pass

_LOGGER: Final = logging.getLogger(__name__)

# Safety: Files this integration is allowed to create/modify
SAFE_TO_CREATE: Final[set[str]] = {
    MANAGED_ENTITIES_FILE,
    GOOGLE_ASSISTANT_FILE,
}

# Files that require mandatory backup before modification
CRITICAL_FILES: Final[set[str]] = {
    CONFIGURATION_FILE,
    GOOGLE_ASSISTANT_FILE,
}


class YamlManager:
    """Manage YAML configuration files.

    This class handles reading and writing YAML configuration files for
    the Google Home Exposure Manager integration. It ensures safe file
    operations with atomic writes and automatic backups.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the YAML manager.

        Args:
            hass: The Home Assistant instance.
        """
        self.hass = hass
        self._config_dir = Path(hass.config.config_dir)

    def _get_path(self, filename: str) -> Path:
        """Get full path for a config file.

        Args:
            filename: The filename to resolve.

        Returns:
            The full Path to the file.
        """
        return self._config_dir / filename

    async def create_backup(
        self,
        filename: str | None = None,
        mandatory: bool = False,
    ) -> str | None:
        """Create a timestamped backup of a file.

        Args:
            filename: The file to backup. Defaults to MANAGED_ENTITIES_FILE.
            mandatory: If True, raises YamlWriteError on failure.

        Returns:
            The backup file path, or None if the source file doesn't exist.

        Raises:
            YamlWriteError: If mandatory=True and backup fails.
        """
        if filename is None:
            filename = MANAGED_ENTITIES_FILE

        filepath = self._get_path(filename)

        def _backup() -> str | None:
            if not filepath.exists():
                _LOGGER.debug("No backup needed - file does not exist: %s", filename)
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self._config_dir / "backups" / "google_home_exposure_manager"

            try:
                backup_dir.mkdir(parents=True, exist_ok=True)
            except OSError as ex:
                _LOGGER.error("Failed to create backup directory: %s", ex)
                if mandatory:
                    raise YamlWriteError(
                        f"Failed to create backup directory: {ex}"
                    ) from ex
                return None

            # Use original extension
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = backup_dir / backup_name

            try:
                shutil.copy2(filepath, backup_path)
                _LOGGER.info("Created backup: %s", backup_path)
                return str(backup_path)
            except OSError as ex:
                _LOGGER.error("Failed to create backup: %s", ex)
                if mandatory:
                    raise YamlWriteError(f"Failed to create backup: {ex}") from ex
                return None

        return await self.hass.async_add_executor_job(_backup)

    async def write_entities_file(
        self,
        exposed_entities: list[str],
        excluded_entities: list[str],
        explicit_exclusions: set[str] | None = None,
        entity_config: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Write managed entities YAML file using atomic write.

        Exposed entities get expose: true, explicit exclusions get expose: false.
        Preserves existing entity properties (name, aliases, etc.) and merges
        with any entity_config provided (which takes precedence).

        Args:
            exposed_entities: List of entity IDs to expose.
            excluded_entities: List of entity IDs to exclude.
            explicit_exclusions: Set of entity IDs that were explicitly excluded.
            entity_config: Optional dict of entity configs (name, aliases, room).
        """
        filepath = self._get_path(MANAGED_ENTITIES_FILE)

        # Default to empty if not provided
        if explicit_exclusions is None:
            explicit_exclusions = set()
        if entity_config is None:
            entity_config = {}

        def _write() -> None:
            # Preserve existing entity properties
            existing_data: dict[str, Any] = {}
            if filepath.exists():
                try:
                    from ruamel.yaml import YAML

                    yaml_reader = YAML()
                    with filepath.open("r", encoding="utf-8") as f:
                        existing_data = yaml_reader.load(f) or {}
                except Exception as ex:
                    _LOGGER.warning("Could not read existing entities file: %s", ex)

            temp_fd = None
            temp_path: Path | None = None

            try:
                temp_fd, temp_path_str = tempfile.mkstemp(
                    suffix=".yaml.tmp",
                    prefix="ghem_",
                    dir=str(filepath.parent),
                )
                temp_path = Path(temp_path_str)

                try:
                    from ruamel.yaml import YAML
                    from ruamel.yaml.comments import CommentedMap

                    yaml = YAML()
                    yaml.default_flow_style = False
                    yaml.preserve_quotes = True
                    use_ruamel = True
                except ImportError:
                    _LOGGER.debug("ruamel.yaml not available, using standard yaml")
                    use_ruamel = False

                import os as os_module

                with os_module.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    temp_fd = None
                    f.write(MANAGED_FILE_HEADER)

                    if use_ruamel:
                        data = CommentedMap()

                        for entity_id in sorted(exposed_entities):
                            if entity_id in existing_data and isinstance(
                                existing_data[entity_id], dict
                            ):
                                entity_data = CommentedMap(existing_data[entity_id])
                                entity_data["expose"] = True
                            else:
                                entity_data = CommentedMap()
                                entity_data["expose"] = True
                            # Merge entity_config (name, aliases, room)
                            if entity_id in entity_config:
                                for key, value in entity_config[entity_id].items():
                                    entity_data[key] = value
                            data[entity_id] = entity_data

                        for entity_id in sorted(explicit_exclusions):
                            if entity_id in data:
                                continue
                            if entity_id in existing_data and isinstance(
                                existing_data[entity_id], dict
                            ):
                                entity_data = CommentedMap(existing_data[entity_id])
                                entity_data["expose"] = False
                            else:
                                entity_data = CommentedMap()
                                entity_data["expose"] = False
                            # Merge entity_config for excluded entities too
                            if entity_id in entity_config:
                                for key, value in entity_config[entity_id].items():
                                    entity_data[key] = value
                            data[entity_id] = entity_data

                        yaml.dump(data, f)
                    else:
                        import yaml as standard_yaml

                        data = {}

                        for entity_id in sorted(exposed_entities):
                            if entity_id in existing_data and isinstance(
                                existing_data[entity_id], dict
                            ):
                                entity_data = dict(existing_data[entity_id])
                                entity_data["expose"] = True
                            else:
                                entity_data = {"expose": True}
                            # Merge entity_config (name, aliases, room)
                            if entity_id in entity_config:
                                entity_data.update(entity_config[entity_id])
                            data[entity_id] = entity_data

                        for entity_id in sorted(explicit_exclusions):
                            if entity_id in data:
                                continue
                            if entity_id in existing_data and isinstance(
                                existing_data[entity_id], dict
                            ):
                                entity_data = dict(existing_data[entity_id])
                                entity_data["expose"] = False
                            else:
                                entity_data = {"expose": False}
                            # Merge entity_config for excluded entities too
                            if entity_id in entity_config:
                                entity_data.update(entity_config[entity_id])
                            data[entity_id] = entity_data

                        standard_yaml.dump(
                            data, f, default_flow_style=False, sort_keys=False
                        )

                # Atomic rename
                temp_path.replace(filepath)
                temp_path = None

            finally:
                # Clean up on failure
                if temp_fd is not None:
                    try:
                        import os as os_module

                        os_module.close(temp_fd)
                    except OSError:
                        pass
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

        await self.hass.async_add_executor_job(_write)
        _LOGGER.info("Wrote entities file: %s", filepath)

    async def setup_google_assistant_config(self, project_id: str | None) -> None:
        """Set up Google Assistant configuration files.

        Args:
            project_id: The Google Cloud project ID.
        """

        def _setup() -> None:
            # Check if google_assistant.yaml exists
            ga_file = self._get_path(GOOGLE_ASSISTANT_FILE)
            config_file = self._get_path(CONFIGURATION_FILE)
            entities_file = self._get_path(MANAGED_ENTITIES_FILE)

            try:
                from ruamel.yaml import YAML

                yaml = YAML()
                yaml.preserve_quotes = True
                yaml.default_flow_style = False
            except ImportError:
                yaml = None

            # Create google_assistant.yaml if it doesn't exist
            if not ga_file.exists():
                with ga_file.open("w", encoding="utf-8") as f:
                    f.write("# Google Assistant Configuration\n")
                    f.write(
                        "# Managed entities are in google_assistant_entities.yaml\n\n"
                    )
                    f.write(f"project_id: {project_id}\n")
                    f.write(f"service_account: !include {SERVICE_ACCOUNT_FILE}\n")
                    f.write("report_state: true\n")
                    f.write("expose_by_default: false\n")
                    f.write(f"entity_config: !include {MANAGED_ENTITIES_FILE}\n")

                _LOGGER.info("Created %s", ga_file)

            # Create empty entities file if it doesn't exist
            if not entities_file.exists():
                with entities_file.open("w", encoding="utf-8") as f:
                    f.write(MANAGED_FILE_HEADER)
                    f.write("# Entity exposure will be configured after setup\n")
                _LOGGER.info("Created %s", entities_file)

            # Update configuration.yaml to include google_assistant
            self._update_configuration_yaml(config_file, ga_file)

        await self.hass.async_add_executor_job(_setup)

    def _update_configuration_yaml(self, config_file: Path, ga_file: Path) -> None:
        """Update configuration.yaml to include google_assistant.

        Creates mandatory backup before modification.

        Args:
            config_file: Path to configuration.yaml.
            ga_file: Path to google_assistant.yaml.
        """
        if not config_file.exists():
            _LOGGER.warning("configuration.yaml not found - skipping modification")
            return

        content = config_file.read_text(encoding="utf-8")

        # Check if google_assistant is already configured
        if "google_assistant:" in content:
            _LOGGER.info(
                "google_assistant already in configuration.yaml - no changes needed"
            )
            return

        # SAFETY: Create backup before modifying configuration.yaml
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self._config_dir / "backups" / "google_home_exposure_manager"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"configuration_{timestamp}.yaml"

        try:
            shutil.copy2(config_file, backup_path)
            _LOGGER.info("Created backup of configuration.yaml: %s", backup_path)
        except OSError as ex:
            _LOGGER.error("Cannot backup configuration.yaml, aborting: %s", ex)
            raise YamlWriteError(
                f"Cannot modify configuration.yaml without backup: {ex}"
            ) from ex

        # Add google_assistant include
        include_line = f"\ngoogle_assistant: !include {GOOGLE_ASSISTANT_FILE}\n"

        try:
            with config_file.open("a", encoding="utf-8") as f:
                f.write(include_line)
            _LOGGER.info("Added google_assistant include to configuration.yaml")
        except OSError as ex:
            _LOGGER.error("Failed to update configuration.yaml: %s", ex)
            _LOGGER.info("Backup available at: %s", backup_path)
            raise

    async def read_entities_file(self) -> dict[str, dict[str, Any]]:
        """Read the current entities file.

        Returns:
            Dictionary mapping entity IDs to their configuration.
        """
        filepath = self._get_path(MANAGED_ENTITIES_FILE)

        def _read() -> dict[str, dict[str, Any]]:
            if not filepath.exists():
                return {}

            try:
                from ruamel.yaml import YAML

                yaml = YAML()
                with filepath.open("r", encoding="utf-8") as f:
                    data = yaml.load(f)
                return data if data else {}
            except ImportError:
                import yaml as standard_yaml

                with filepath.open("r", encoding="utf-8") as f:
                    data = standard_yaml.safe_load(f)
                return data if data else {}
            except Exception as ex:
                _LOGGER.error("Failed to read entities file: %s", ex)
                return {}

        return await self.hass.async_add_executor_job(_read)

    async def read_entity_config(self, parent_file: str) -> dict[str, dict[str, Any]]:
        """Read entity config from a parent file (alias for read_google_assistant_entity_config).

        Args:
            parent_file: The parent config file to read from.

        Returns:
            Dictionary mapping entity IDs to their configuration.
        """
        return await self.read_google_assistant_entity_config(parent_file)

    async def migrate_entity_config(self, parent_file: str) -> bool:
        """Migrate entity config from parent file to managed file.

        Args:
            parent_file: The parent config file containing entity_config.

        Returns:
            True if migration succeeded, False otherwise.
        """
        success, _, _ = await self.migrate_entity_config_to_include(parent_file)
        return success

    async def inject_entity_config_include(self, parent_file: str) -> bool:
        """Inject entity_config !include into existing GA config file.

        Args:
            parent_file: The parent config file to modify.

        Returns:
            True if injection succeeded or migration was triggered.
        """
        filepath = self._get_path(parent_file)

        def _inject() -> bool:
            if not filepath.exists():
                return False

            content = filepath.read_text(encoding="utf-8")

            # Check if entity_config already exists
            if "entity_config:" in content:
                # Need to migrate existing entity_config
                _LOGGER.info("entity_config already exists, migration needed")
                return self._migrate_entity_config(filepath, content)

            # Add entity_config include
            include_line = f"\nentity_config: !include {MANAGED_ENTITIES_FILE}\n"

            with filepath.open("a", encoding="utf-8") as f:
                f.write(include_line)

            _LOGGER.info("Added entity_config include to %s", parent_file)
            return True

        return await self.hass.async_add_executor_job(_inject)

    def _migrate_entity_config(self, filepath: Path, content: str) -> bool:
        """Migrate existing entity_config to managed file.

        Creates backup first for safety.

        Args:
            filepath: Path to the config file.
            content: The file content.

        Returns:
            True if migration succeeded.
        """
        backup_path: str | None = None
        entities_file = self._get_path(MANAGED_ENTITIES_FILE)
        entities_backup: str | None = None

        try:
            from ruamel.yaml import YAML

            yaml = YAML()
            yaml.preserve_quotes = True

            # Parse the file
            with filepath.open("r", encoding="utf-8") as f:
                data = yaml.load(f)

            if data is None or "entity_config" not in data:
                _LOGGER.info("No entity_config found to migrate")
                return False

            entity_config = data.get("entity_config", {})

            if not entity_config:
                _LOGGER.info("entity_config is empty, nothing to migrate")
                return False

            # SAFETY: Create backup of parent file first
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self._config_dir / "backups" / "google_home_exposure_manager"
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_path = str(
                backup_dir
                / f"{filepath.stem}_premigration_{timestamp}{filepath.suffix}"
            )
            shutil.copy2(filepath, backup_path)
            _LOGGER.info("Created pre-migration backup: %s", backup_path)

            # SAFETY: Backup existing entities file if it exists
            if entities_file.exists():
                entities_backup = str(
                    backup_dir
                    / f"google_assistant_entities_premigration_{timestamp}.yaml"
                )
                shutil.copy2(entities_file, entities_backup)
                _LOGGER.info("Created entities backup: %s", entities_backup)

            # Write entity config to managed file (use temp file for safety)
            temp_entities = entities_file.with_suffix(".tmp")
            try:
                with temp_entities.open("w", encoding="utf-8") as f:
                    f.write(MANAGED_FILE_HEADER)
                    f.write("# Migrated from existing entity_config\n")
                    yaml.dump(entity_config, f)
            except Exception:
                if temp_entities.exists():
                    temp_entities.unlink()
                raise

            # Build new parent file content
            lines = content.split("\n")
            new_lines: list[str] = []
            skip_until_outdent = False
            indent_level = 0

            for line in lines:
                if skip_until_outdent:
                    stripped = line.lstrip()
                    current_indent = len(line) - len(stripped)
                    if stripped and current_indent <= indent_level:
                        skip_until_outdent = False
                        new_lines.append(line)
                    continue

                if line.strip().startswith("entity_config:"):
                    indent_level = len(line) - len(line.lstrip())
                    indent_str = " " * indent_level
                    include_str = f"!include {MANAGED_ENTITIES_FILE}"
                    new_lines.append(f"{indent_str}entity_config: {include_str}")
                    if line.strip().endswith(":"):
                        skip_until_outdent = True
                else:
                    new_lines.append(line)

            # Write parent file (use temp file for safety)
            temp_parent = filepath.with_suffix(".tmp")
            try:
                temp_parent.write_text("\n".join(new_lines), encoding="utf-8")
            except Exception:
                if temp_parent.exists():
                    temp_parent.unlink()
                if temp_entities.exists():
                    temp_entities.unlink()
                raise

            # SAFETY: Atomic swap - only if both temp files were written successfully
            temp_entities.replace(entities_file)
            temp_parent.replace(filepath)

            _LOGGER.info(
                "Successfully migrated entity_config to %s", MANAGED_ENTITIES_FILE
            )
            _LOGGER.info("Original files backed up to: %s", backup_dir)
            return True

        except Exception as ex:
            _LOGGER.exception("Failed to migrate entity_config: %s", ex)
            if backup_path:
                _LOGGER.info("Original file backup available at: %s", backup_path)
            if entities_backup:
                _LOGGER.info(
                    "Original entities backup available at: %s", entities_backup
                )
            return False

    async def file_exists(self, filename: str) -> bool:
        """Check if a file exists in the config directory.

        Args:
            filename: The filename to check.

        Returns:
            True if the file exists.
        """
        filepath = self._get_path(filename)

        def _exists() -> bool:
            return filepath.exists()

        return await self.hass.async_add_executor_job(_exists)

    async def read_file(self, filename: str) -> str | None:
        """Read a file's contents.

        Args:
            filename: The filename to read.

        Returns:
            The file contents, or None if the file doesn't exist.
        """
        filepath = self._get_path(filename)

        def _read() -> str | None:
            if not filepath.exists():
                return None
            return filepath.read_text(encoding="utf-8")

        return await self.hass.async_add_executor_job(_read)

    async def find_google_assistant_config_file(self) -> str | None:
        """Find the Google Assistant config file.

        Searches configuration.yaml for a google_assistant reference.

        Returns:
            The filename or None if not found.
        """
        config_file = self._get_path(CONFIGURATION_FILE)

        def _find() -> str | None:
            if not config_file.exists():
                return None

            content = config_file.read_text(encoding="utf-8")

            # Check for google_assistant with !include
            # Match: google_assistant: !include filename.yaml
            match = re.search(r"google_assistant:\s*!include\s+([^\s\n]+)", content)
            if match:
                return match.group(1).strip()

            # Check for inline google_assistant: (no include)
            if re.search(r"^google_assistant:\s*$", content, re.MULTILINE):
                # Inline config in configuration.yaml itself
                return CONFIGURATION_FILE

            # Check for google_assistant with inline content on same line
            ga_parts = content.split("google_assistant:")
            if len(ga_parts) > 1 and "!include" not in ga_parts[1].split("\n")[0]:
                # Could be inline in configuration.yaml
                return CONFIGURATION_FILE

            return None

        return await self.hass.async_add_executor_job(_find)

    async def read_google_assistant_entity_config(
        self, config_file: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Read inline entity_config from GA config file.

        Args:
            config_file: The config file to read from. Auto-detected if None.

        Returns:
            Dictionary mapping entity IDs to their config, empty if none found.
        """
        if config_file is None:
            config_file = await self.find_google_assistant_config_file()
            if config_file is None:
                return {}

        filepath = self._get_path(config_file)
        is_main_config = config_file == CONFIGURATION_FILE

        def _read() -> dict[str, dict[str, Any]]:
            if not filepath.exists():
                return {}

            # First check if entity_config is an include (don't parse those)
            content = filepath.read_text(encoding="utf-8")

            # If entity_config uses !include, it's already migrated
            if (
                "entity_config: !include" in content
                or "entity_config:!include" in content
            ):
                _LOGGER.debug(
                    "entity_config already uses !include, no migration needed"
                )
                return {}

            # Check if entity_config exists at all
            if "entity_config:" not in content:
                return {}

            try:
                from ruamel.yaml import YAML

                yaml = YAML()
                yaml.preserve_quotes = True

                with filepath.open("r", encoding="utf-8") as f:
                    data = yaml.load(f)

                if data is None:
                    return {}

                # If reading from configuration.yaml, look inside google_assistant
                if is_main_config:
                    ga_config = data.get("google_assistant", {})
                    if not isinstance(ga_config, dict):
                        return {}
                    entity_config = ga_config.get("entity_config", {})
                else:
                    entity_config = data.get("entity_config", {})

                # If it's a string (like an include path), return empty
                if isinstance(entity_config, str):
                    return {}

                return dict(entity_config) if entity_config else {}

            except ImportError:
                import yaml as standard_yaml

                with filepath.open("r", encoding="utf-8") as f:
                    data = standard_yaml.safe_load(f)

                if data is None:
                    return {}

                if is_main_config:
                    ga_config = data.get("google_assistant", {})
                    if not isinstance(ga_config, dict):
                        return {}
                    entity_config = ga_config.get("entity_config", {})
                else:
                    entity_config = data.get("entity_config", {})

                if isinstance(entity_config, str):
                    return {}

                return dict(entity_config) if entity_config else {}

            except Exception as ex:
                _LOGGER.error("Failed to read %s: %s", config_file, ex)
                return {}

        return await self.hass.async_add_executor_job(_read)

    async def migrate_entity_config_to_include(
        self, config_file: str | None = None
    ) -> tuple[bool, int, str]:
        """Migrate inline entity_config to entities file.

        Args:
            config_file: The config file to migrate from. Auto-detected if None.

        Returns:
            Tuple of (success, entity_count, config_file).
        """
        if config_file is None:
            config_file = await self.find_google_assistant_config_file()
            if config_file is None:
                return (False, 0, "")

        filepath = self._get_path(config_file)

        def _migrate() -> tuple[bool, int, str]:
            if not filepath.exists():
                return (False, 0, config_file)

            content = filepath.read_text(encoding="utf-8")

            # Check if already using include
            if (
                "entity_config: !include" in content
                or "entity_config:!include" in content
            ):
                _LOGGER.info("entity_config already uses !include")
                return (True, 0, config_file)

            result = self._migrate_entity_config(filepath, content)
            if result:
                # Count entities that were migrated
                entities_file = self._get_path(MANAGED_ENTITIES_FILE)
                try:
                    from ruamel.yaml import YAML

                    yaml = YAML()
                    with entities_file.open("r", encoding="utf-8") as f:
                        data = yaml.load(f)
                    count = len(data) if data else 0
                except Exception:
                    count = 0
                return (True, count, config_file)
            return (False, 0, config_file)

        return await self.hass.async_add_executor_job(_migrate)
