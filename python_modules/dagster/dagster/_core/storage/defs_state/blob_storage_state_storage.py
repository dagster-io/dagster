from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from typing_extensions import Self

from dagster._config.config_type import ConfigType
from dagster._config.field import Field
from dagster._config.field_utils import Permissive, Shape
from dagster._core.storage.defs_state.base import DEFS_STATE_INFO_CURSOR_KEY, DefsStateStorage
from dagster._serdes.config_class import ConfigurableClass, ConfigurableClassData

if TYPE_CHECKING:
    from upath import UPath


class BlobStorageStateStorage(DefsStateStorage, ConfigurableClass):
    """Implements StateStorage using a UPath as the backing store."""

    def __init__(self, base_path: "UPath", inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        self._base_path = base_path

    @property
    def base_path(self) -> "UPath":
        return self._base_path

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> ConfigType:
        return Shape(
            {
                "base_path": Field(str, is_required=True),
                "storage_options": Field(Permissive(), is_required=False),
            }
        )

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        from upath import UPath

        return cls(
            inst_data=inst_data,
            base_path=UPath(
                check.not_none(
                    config_value.get("base_path"),
                ),
                **config_value.get("storage_options", {}),
            ),
        )

    def _get_state_path(self, key: str, version: str) -> "UPath":
        return self._base_path / key / version

    def download_state_to_path(self, key: str, version: str, path: Path) -> None:
        remote_path = self._get_state_path(key, version)
        if not remote_path.exists():
            if self.base_path.fs in ("file", None):
                raise ValueError(
                    f"No state found for key {key} and version {version}. "
                    "You are currently using local storage for your defs_state_storage, which is not supported "
                    "when executing in a remote environment. Please configure your defs_state_storage to have a "
                    "base_path that points to a remote blob storage location, such as s3://, gs://, azure://, or abfs://."
                )
            else:
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
