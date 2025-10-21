import time
from collections.abc import Mapping
from enum import Enum
from typing import Any, Optional

from dagster_shared.dagster_model import DagsterModel
from dagster_shared.serdes import whitelist_for_serdes

LOCAL_STATE_VERSION = "__local__"
CODE_SERVER_STATE_VERSION = "__code_server__"


class DefsStateManagementType(Enum):
    VERSIONED_STATE_STORAGE = "VERSIONED_STATE_STORAGE"
    LOCAL_FILESYSTEM = "LOCAL_FILESYSTEM"
    LEGACY_CODE_SERVER_SNAPSHOTS = "LEGACY_CODE_SERVER_SNAPSHOTS"


@whitelist_for_serdes
class DefsKeyStateInfo(DagsterModel):
    """Records information about the version of the state for a given defs key."""

    version: str
    create_timestamp: float

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> "DefsKeyStateInfo":
        return cls(version=data["version"], create_timestamp=data["createTimestamp"])

    @property
    def management_type(self) -> DefsStateManagementType:
        if self.version == LOCAL_STATE_VERSION:
            return DefsStateManagementType.LOCAL_FILESYSTEM
        elif self.version == CODE_SERVER_STATE_VERSION:
            return DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS
        else:
            return DefsStateManagementType.VERSIONED_STATE_STORAGE


@whitelist_for_serdes
class DefsStateInfo(DagsterModel):
    """All of the information about the state version that will be used to load a given code location."""

    info_mapping: Mapping[str, Optional[DefsKeyStateInfo]]

    @staticmethod
    def empty() -> "DefsStateInfo":
        return DefsStateInfo(info_mapping={})

    @staticmethod
    def add_version(
        current_info: Optional["DefsStateInfo"],
        key: str,
        version: Optional[str],
        create_timestamp: Optional[float] = None,
    ) -> "DefsStateInfo":
        new_info = (
            DefsKeyStateInfo(version=version, create_timestamp=create_timestamp or time.time())
            if version
            else None
        )
        if current_info is None:
            return DefsStateInfo(info_mapping={key: new_info})
        else:
            return DefsStateInfo(info_mapping={**current_info.info_mapping, key: new_info})

    def get_version(self, key: str) -> Optional[str]:
        info = self.info_mapping.get(key)
        return info.version if info else None

    def for_keys(self, keys: set[str]) -> "DefsStateInfo":
        """Subsets the DefsStateInfo to only include the keys in the set."""
        return DefsStateInfo(info_mapping={k: v for k, v in self.info_mapping.items() if k in keys})

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> "DefsStateInfo":
        return cls(
            info_mapping={
                val["name"]: DefsKeyStateInfo.from_graphql(val["info"])
                for val in data["keyStateInfo"]
            }
        )
