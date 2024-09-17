from typing import TYPE_CHECKING, List, Optional

from dagster import AssetKey
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.loader import LoadingContext
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.dagster_run import RunRecord

from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    return any(
        external_check.asset_key == asset_key
        for external_check in graphene_info.context.asset_graph.asset_checks
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
