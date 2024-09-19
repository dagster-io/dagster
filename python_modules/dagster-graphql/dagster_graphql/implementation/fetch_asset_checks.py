from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

from dagster import AssetKey
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.loader import LoadingContext
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import ExternalRepository
from dagster._core.remote_representation.external_data import ExternalAssetCheck
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.dagster_run import RunRecord
from dagster._core.workspace.context import WorkspaceRequestContext

from dagster_graphql.implementation.fetch_assets import repository_iter
from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


def asset_checks_iter(
    context: WorkspaceRequestContext,
) -> Iterator[Tuple[CodeLocation, ExternalRepository, ExternalAssetCheck]]:
    for location, repository in repository_iter(context):
        for external_check in repository.external_repository_data.external_asset_checks or []:
            yield (location, repository, external_check)


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    return any(
        external_check.asset_key == asset_key
        for _, _, external_check in asset_checks_iter(graphene_info.context)
    )


def fetch_asset_check_executions(
    loading_context: LoadingContext,
    asset_check_key: AssetCheckKey,
    limit: int,
    cursor: Optional[str],
) -> List[GrapheneAssetCheckExecution]:
    check_records = loading_context.instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check_key,
        limit=limit,
        cursor=int(cursor) if cursor else None,
    )

    RunRecord.prepare(
        loading_context,
        [r.run_id for r in check_records if r.status == AssetCheckExecutionRecordStatus.PLANNED],
    )

    return [GrapheneAssetCheckExecution(check_record) for check_record in check_records]
