import time
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from platformdirs import user_data_dir

from dagster_shared.dagster_model import DagsterModel
from dagster_shared.serdes import whitelist_for_serdes

LOCAL_STATE_VERSION = "__local__"


def _global_state_dir() -> Path:
    return Path(user_data_dir("dagster", appauthor=False)).resolve()


def get_local_state_dir(key: str) -> Path:
    state_dir = _global_state_dir() / key
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_local_state_path(key: str) -> Path:
    return get_local_state_dir(key) / "state"


class DefsStateStorageLocation(Enum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


@whitelist_for_serdes
class DefsKeyStateInfo(DagsterModel):
    """Records information about the version of the state for a given defs key."""

    version: str
    create_timestamp: float

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> "DefsKeyStateInfo":
        return cls(version=data["version"], create_timestamp=data["createTimestamp"])

    @property
    def storage_location(self) -> DefsStateStorageLocation:
        if self.version == LOCAL_STATE_VERSION:
            return DefsStateStorageLocation.LOCAL
        else:
            return DefsStateStorageLocation.REMOTE


@whitelist_for_serdes
class DefsStateInfo(DagsterModel):
    """All of the information about the state version that will be used to load a given code location."""

    info_mapping: Mapping[str, Optional[DefsKeyStateInfo]]

    @staticmethod
    def empty() -> "DefsStateInfo":
        return DefsStateInfo(info_mapping={})

    @staticmethod
    def add_version(
        current_info: Optional["DefsStateInfo"], key: str, version: Optional[str]
    ) -> "DefsStateInfo":
        new_info = (
            DefsKeyStateInfo(version=version, create_timestamp=time.time()) if version else None
        )
        if current_info is None:
            return DefsStateInfo(info_mapping={key: new_info})
        else:
            return DefsStateInfo(info_mapping={**current_info.info_mapping, key: new_info})

    def get_version(self, key: str) -> Optional[str]:
        info = self.info_mapping.get(key)
        return info.version if info else None

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> "DefsStateInfo":
        return cls(
            info_mapping={
                val["name"]: DefsKeyStateInfo.from_graphql(val["info"])
                for val in data["keyStateInfo"]
            }
        )
