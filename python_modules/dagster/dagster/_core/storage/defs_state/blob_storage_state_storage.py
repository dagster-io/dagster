from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

from dagster_shared import check
from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from typing_extensions import Self
from upath import UPath

from dagster._config.config_type import ConfigType
from dagster._config.field import Field
from dagster._config.field_utils import Shape
from dagster._core.storage.defs_state.base import DEFS_STATE_INFO_CURSOR_KEY, DefsStateStorage
from dagster._core.storage.defs_state.defs_state_info import DefsStateInfo
from dagster._serdes.config_class import ConfigurableClass, ConfigurableClassData


class BlobStorageStateStorage(DefsStateStorage, ConfigurableClass):
    """Implements StateStorage using a UPath as the backing store."""

    def __init__(self, base_dir: UPath, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> UPath:
        return self._base_dir

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> ConfigType:
        return Shape({"base_dir": Field(str, is_required=True)})

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(
            inst_data=inst_data,
            base_dir=UPath(check.not_none(config_value.get("base_dir"))),
        )

    def _get_state_path(self, key: str, version: str) -> UPath:
        return self._base_dir / key / version

    def download_state_to_path(self, key: str, version: str, path: Path) -> None:
        remote_path = self._get_state_path(key, version)
        if not remote_path.exists():
            raise ValueError(f"No state found for key {key} and version {version}")
        path.write_bytes(remote_path.read_bytes())

    def upload_state_from_path(self, key: str, version: str, path: Path) -> None:
        remote_path = self._get_state_path(key, version)
        # paths are structured as <base>/<key>/<version>, so make sure that the <key> directory exists
        # before attempting to write the file
        remote_path.parent.mkdir(parents=True, exist_ok=True)
        remote_path.write_bytes(path.read_bytes())
        self.set_latest_version(key, version)

    def set_latest_version(self, key: str, version: str) -> None:
        # use the run storage's kvs to store the latest version pointer
        current_info = self.get_latest_defs_state_info()
        new_info = DefsStateInfo.add_version(current_info, key, version)
        self._instance.run_storage.set_cursor_values(
            {DEFS_STATE_INFO_CURSOR_KEY: serialize_value(new_info)}
        )

    def get_latest_defs_state_info(self) -> Optional[DefsStateInfo]:
        raw_value = self._instance.run_storage.get_cursor_values({DEFS_STATE_INFO_CURSOR_KEY}).get(
            DEFS_STATE_INFO_CURSOR_KEY
        )
        if raw_value is None:
            return None
        return deserialize_value(raw_value, DefsStateInfo)
