from collections.abc import Sequence
from typing import TYPE_CHECKING, AbstractSet, Annotated, Optional  # noqa: UP035

from dagster._check import checked
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_origin import RemoteJobOrigin
from dagster._core.remote_representation.external_data import RemoteJobSubsetResult
from dagster._grpc.types import JobSubsetSnapshotArgs
from dagster._record import ImportFrom
from dagster._serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


@checked
def sync_get_external_job_subset_grpc(
    api_client: Annotated["DagsterGrpcClient", ImportFrom("dagster._grpc.client")],
    job_origin: RemoteJobOrigin,
    include_parent_snapshot: bool,
    op_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
) -> RemoteJobSubsetResult:
    result = deserialize_value(
        api_client.external_pipeline_subset(
            pipeline_subset_snapshot_args=JobSubsetSnapshotArgs(
                job_origin=job_origin,
                op_selection=op_selection,
                asset_selection=asset_selection,
                asset_check_selection=asset_check_selection,
                include_parent_snapshot=include_parent_snapshot,
            ),
        ),
        RemoteJobSubsetResult,
    )

    if result.error:
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


@checked
async def gen_external_job_subset_grpc(
    api_client: Annotated["DagsterGrpcClient", ImportFrom("dagster._grpc.client")],
    job_origin: RemoteJobOrigin,
    include_parent_snapshot: bool,
    op_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
) -> RemoteJobSubsetResult:
    result = deserialize_value(
        await api_client.gen_external_pipeline_subset(
            pipeline_subset_snapshot_args=JobSubsetSnapshotArgs(
                job_origin=job_origin,
                op_selection=op_selection,
                asset_selection=asset_selection,
                asset_check_selection=asset_check_selection,
                include_parent_snapshot=include_parent_snapshot,
            ),
        ),
        RemoteJobSubsetResult,
    )

    if result.error:
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
