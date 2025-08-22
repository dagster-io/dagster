import time
from collections.abc import Mapping
from typing import Any, Optional

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class DefsKeyStateInfo:
    """Records information about the version of the state for a given defs key."""

    version: str
    create_timestamp: float

    @staticmethod
    def from_dict(val: dict[str, Any]) -> "DefsKeyStateInfo":
        return DefsKeyStateInfo(version=val["version"], create_timestamp=val["create_timestamp"])

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "create_timestamp": self.create_timestamp}


@whitelist_for_serdes
@record
class DefsStateInfo:
    """All of the information about the state version that will be used to load a given code location."""

    info_mapping: Mapping[str, DefsKeyStateInfo]

    @staticmethod
    def add_version(
        current_info: Optional["DefsStateInfo"], key: str, version: str
    ) -> "DefsStateInfo":
        new_info = DefsKeyStateInfo(version=version, create_timestamp=time.time())
        if current_info is None:
            return DefsStateInfo(info_mapping={key: new_info})
        else:
            return DefsStateInfo(info_mapping={**current_info.info_mapping, key: new_info})

    @staticmethod
    def from_dict(val: dict[str, Any]) -> "DefsStateInfo":
        """Used for converting from the user-facing dict representation."""
        return DefsStateInfo(
            info_mapping={key: DefsKeyStateInfo.from_dict(info) for key, info in val.items()}
        )

    def to_dict(self) -> dict[str, Any]:
        """Used for converting to the user-facing dict representation."""
        return {key: info.to_dict() for key, info in self.info_mapping.items()}

    def get_version(self, key: str) -> Optional[str]:
        info = self.info_mapping.get(key)
        return info.version if info else None
