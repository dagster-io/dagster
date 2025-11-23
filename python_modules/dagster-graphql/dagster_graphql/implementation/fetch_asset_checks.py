from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

from dagster import _check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.events import ASSET_CHECK_EVENTS, DagsterEventType
from dagster._core.loader import LoadingContext
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckInstanceSupport,
)
from dagster._core.storage.dagster_run import RunRecord
from packaging import version

from dagster_graphql.schema.asset_checks import (
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
)

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution
    from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle
    from dagster_graphql.schema.util import ResolveInfo


def check_asset_checks_support(
    graphene_info: "ResolveInfo", repository_handle: RepositoryHandle
) -> Union[
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    None,
]:
    asset_check_support = graphene_info.context.instance.get_asset_check_support()
    if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
        return GrapheneAssetCheckNeedsMigrationError(
            message="Asset checks require an instance migration. Run `dagster instance migrate`."
        )
    elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
        return GrapheneAssetCheckNeedsAgentUpgradeError(
            "Asset checks require an agent upgrade to 1.5.0 or greater."
        )
    else:
        check.invariant(
            asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
            f"Unexpected asset check support status {asset_check_support}",
        )

    library_versions = graphene_info.context.get_dagster_library_versions(
        repository_handle.location_name
    )
    code_location_version = (library_versions or {}).get("dagster")
    if code_location_version and version.parse(code_location_version) < version.parse("1.5"):
        return GrapheneAssetCheckNeedsUserCodeUpgrade(
            message=(
                "Asset checks require dagster>=1.5. Upgrade your dagster"
                " version for this code location."
            )
        )


def fetch_asset_check_executions(
    loading_context: LoadingContext,
    asset_check_key: AssetCheckKey,
    partition: Optional[str],
    limit: int,
    cursor: Optional[str],
) -> list["GrapheneAssetCheckExecution"]:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution

    check_records = loading_context.instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check_key,
        limit=limit,
        cursor=int(cursor) if cursor else None,
        partition=partition,
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
