from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.events import ASSET_CHECK_EVENTS, DagsterEventType
from dagster._core.loader import LoadingContext
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.dagster_run import RunRecord

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution
    from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle
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
) -> list["GrapheneAssetCheckExecution"]:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution

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


def get_asset_checks_for_run_id(
    graphene_info: "ResolveInfo", run_id: str
) -> Sequence["GrapheneAssetCheckHandle"]:
    from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle

    check.str_param(run_id, "run_id")

    records = graphene_info.context.instance.all_logs(run_id, of_type=ASSET_CHECK_EVENTS)

    asset_check_keys = set(
        [
            record.get_dagster_event().asset_check_evaluation_data.asset_check_key
            for record in records
            if record.is_dagster_event
            and record.get_dagster_event().event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        + [
            record.get_dagster_event().asset_check_planned_data.asset_check_key
            for record in records
            if record.is_dagster_event
            and record.get_dagster_event().event_type
            == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
        ]
    )
    return [
        GrapheneAssetCheckHandle(handle=asset_check_key)
        for asset_check_key in sorted(
            asset_check_keys, key=lambda key: key.name + "".join(key.asset_key.path)
        )
    ]
