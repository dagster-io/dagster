from collections.abc import Mapping
from typing import Optional

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

    info_mapping: Mapping[str, DefsKeyStateInfo]

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
