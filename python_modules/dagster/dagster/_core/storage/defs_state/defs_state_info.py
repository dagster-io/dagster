from collections.abc import Mapping
from typing import Any, Optional

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._time import get_current_timestamp


@whitelist_for_serdes
@record
class DefsKeyStateInfo:
    """Records information about the version of the state for a given defs key."""

    version: str
    create_timestamp: float


@whitelist_for_serdes
@record
class DefsStateInfo:
    """All of the information about the state version that will be used to load a given code location."""

    info_mapping: Mapping[str, Optional[DefsKeyStateInfo]]

    @staticmethod
    def from_yaml(val: Optional[dict[str, Any]]) -> Optional["DefsStateInfo"]:
        if val is None:
            return None

        return DefsStateInfo(
            info_mapping={
                key: DefsKeyStateInfo(
                    version=version_info["version"],
                    create_timestamp=version_info["create_timestamp"],
                )
                if version_info
                else None
                for key, version_info in val.items()
            }
        )

    def to_yaml(self) -> dict[str, Any]:
        return {
            key: {
                "version": version_info.version,
                "create_timestamp": version_info.create_timestamp,
            }
            if version_info
            else None
            for key, version_info in self.info_mapping.items()
        }

    def get_version(self, key: str) -> Optional[str]:
        info = self.info_mapping.get(key)
        return info.version if info else None

    def with_version(self, key: str, version: str) -> "DefsStateInfo":
        return DefsStateInfo(
            info_mapping={
                **self.info_mapping,
                key: DefsKeyStateInfo(version=version, create_timestamp=get_current_timestamp()),
            }
        )
