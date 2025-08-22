from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes.serdes import deserialize_value, serialize_value

from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.defs_state_info import DefsStateInfo

if TYPE_CHECKING:
    from dagster._core.storage.runs.base import RunStorage


class RunStorageStateStorage(DefsStateStorage):
    """Implements StateStorage using a RunStorage as the backing store."""

    INFO_KEY = "__latest_defs_state_info__"

    def __init__(self, run_storage: "RunStorage"):
        self._run_storage = run_storage

    def get_latest_defs_state_info(self) -> Optional[DefsStateInfo]:
        raw_value = self._run_storage.get_cursor_values({self.INFO_KEY}).get(self.INFO_KEY)
        if raw_value is None:
            return None
        return deserialize_value(raw_value, DefsStateInfo)

    def download_state_to_path(self, key: str, version: str, path: Path) -> None:
        state_key = self._get_state_key(key, version)
        state_value = self._run_storage.get_cursor_values({state_key}).get(state_key)
        if state_value:
            path.write_bytes(state_value.encode("utf-8"))
            return
        raise ValueError(f"No state found for key {key} and version {version}")

    def set_latest_version(self, key: str, version: str) -> None:
        self._run_storage.set_cursor_values(
            {self.INFO_KEY: serialize_value(self.get_updated_defs_state_info(key, version))}
        )

    def upload_state_from_path(self, key: str, version: str, path: Path) -> None:
        state_key = self._get_state_key(key, version)
        self._run_storage.set_cursor_values({state_key: path.read_bytes().decode("utf-8")})
        self.set_latest_version(key, version)
