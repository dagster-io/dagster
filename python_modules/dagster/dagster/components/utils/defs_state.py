from typing import Annotated, Optional

from dagster_shared.record import record
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType
from pydantic import Field

from dagster.components.resolved.model import Model, Resolver


class DefsStateConfigArgs(Model):
    key: Optional[str] = Field(
        default=None, description="The key for the state. This must be unique per deployment."
    )
    management_type: DefsStateManagementType = Field(
        description="The storage type for state required for loading this object's definitions."
        "  - `LOCAL_FILESYSTEM`: State is stored on the local filesystem. `dg utils refresh-defs-state` must be executed while building the deployed container image in order for state to be accessible."
        "  - `VERSIONED_STATE_STORAGE`: State is stored in your configured `defs_state_storage`. `dg utils refresh-defs-state` may be executed at any time to refresh the state."
        "  - `LEGACY_CODE_SERVER_SNAPSHOTS`: State is stored in memory in the code server. State is always automatically refreshed when the code server is loaded.",
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
    def local_filesystem(cls) -> "DefsStateConfigArgs":
        return cls(management_type=DefsStateManagementType.LOCAL_FILESYSTEM)

    @classmethod
    def versioned_state_storage(cls) -> "DefsStateConfigArgs":
        return cls(management_type=DefsStateManagementType.VERSIONED_STATE_STORAGE)

    @classmethod
    def legacy_code_server_snapshots(cls) -> "DefsStateConfigArgs":
        return cls(management_type=DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS)


@record
class DefsStateConfig:
    key: str
    management_type: DefsStateManagementType
    refresh_if_dev: bool

    @classmethod
    def from_args(cls, args: DefsStateConfigArgs, default_key: str) -> "DefsStateConfig":
        return cls(
            key=args.key or default_key,
            management_type=args.management_type,
            refresh_if_dev=args.refresh_if_dev,
        )


ResolvedDefsStateConfig = Annotated[
    DefsStateConfigArgs,
    Resolver.default(
        description="Configuration for determining how state is stored and persisted for this component."
    ),
]
