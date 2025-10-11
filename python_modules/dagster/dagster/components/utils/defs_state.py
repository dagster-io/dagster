from typing import Annotated

from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType
from pydantic import Field

from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model, Resolver


class DefsStateConfig(Resolvable, Model):
    type: DefsStateManagementType = Field(
        description="The storage type for state required for loading this object's definitions.",
        examples=[
            DefsStateManagementType.LOCAL_FILESYSTEM.value,
            DefsStateManagementType.VERSIONED_STATE_STORAGE.value,
            DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS.value,
        ],
    )
    refresh_if_dev: bool = Field(
        default=True,
        description="Whether to automatically refresh defs state when using `dagster dev` or the `dg` cli.",
    )

    @classmethod
    def local_filesystem(cls) -> "DefsStateConfig":
        return cls(type=DefsStateManagementType.LOCAL_FILESYSTEM)

    @classmethod
    def versioned_state_storage(cls) -> "DefsStateConfig":
        return cls(type=DefsStateManagementType.VERSIONED_STATE_STORAGE)

    @classmethod
    def legacy_code_server_snapshots(cls) -> "DefsStateConfig":
        return cls(type=DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS)


ResolvedDefsStateConfig = Annotated[
    DefsStateConfig,
    Resolver.default(
        description="Configuration for determining how state is stored and persisted for this component."
        "  - `VERSIONED_STATE_STORAGE`: State is stored in your configured `defs_state_storage`. `dg utils refresh-defs-state` may be executed at any time to refresh the state."
        "  - `LOCAL_FILESYSTEM`: State is stored on the local filesystem. `dg utils refresh-defs-state` must be executed while building the deployed container image in order for state to be accessible."
        "  - `LEGACY_CODE_SERVER_SNAPSHOTS`: State is stored in memory in the code server. State is always automatically refreshed when the code server is loaded."
    ),
]
