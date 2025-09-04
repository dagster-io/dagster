import time
from collections.abc import Mapping
from typing import Optional

from dagster_shared.dagster_model import DagsterModel
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
class DefsKeyStateInfo(DagsterModel):
    """Records information about the version of the state for a given defs key."""

    version: str
    create_timestamp: float


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
