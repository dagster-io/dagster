from typing import TYPE_CHECKING, Optional, Sequence

import dagster._check as check
from dagster import AssetKey
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.implementation.fetch_assets import get_asset_nodes_by_asset_key
from dagster_graphql.schema.asset_condition_evaluations import (
    GrapheneAssetConditionEvaluation,
    GrapheneAssetConditionEvaluationRecord,
    GrapheneAssetConditionEvaluationRecords,
    GrapheneAssetConditionEvaluationRecordsOrError,
)
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
)
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def _get_migration_error(
    graphene_info: "ResolveInfo",
) -> Optional[GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError]:
    if graphene_info.context.instance.schedule_storage is None:
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message="Instance does not have schedule storage configured, cannot fetch evaluations."
        )
    if not graphene_info.context.instance.schedule_storage.supports_auto_materialize_asset_evaluations:
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message=(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )
        )
    return None


def _get_graphene_records_from_evaluations(
    graphene_info: "ResolveInfo",
    evaluation_records: Sequence[AutoMaterializeAssetEvaluationRecord],
) -> GrapheneAssetConditionEvaluationRecords:
    asset_keys = {record.asset_key for record in evaluation_records}

    partitions_defs = {}

    nodes = get_asset_nodes_by_asset_key(graphene_info)
    for asset_key in asset_keys:
        asset_node = nodes.get(asset_key)
        partitions_defs[asset_key] = (
            asset_node.external_asset_node.partitions_def_data.get_partitions_definition()
            if asset_node and asset_node.external_asset_node.partitions_def_data
            else None
        )

    return GrapheneAssetConditionEvaluationRecords(
        records=[
            GrapheneAssetConditionEvaluationRecord(
                evaluation, partitions_defs[evaluation.asset_key]
            )
            for evaluation in evaluation_records
        ]
    )


def fetch_asset_condition_evaluation_record_for_partition(
    graphene_info: "ResolveInfo",
    graphene_asset_key: GrapheneAssetKeyInput,
    evaluation_id: int,
    partition_key: str,
) -> GrapheneAssetConditionEvaluation:
    asset_key = AssetKey.from_graphql_input(graphene_asset_key)
    schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
    record = next(
        iter(
            schedule_storage.get_auto_materialize_asset_evaluations(
                asset_key, cursor=evaluation_id + 1, limit=1
            )
        )
    )
    asset_node = get_asset_nodes_by_asset_key(graphene_info).get(asset_key)
    partitions_def = (
        asset_node.external_asset_node.partitions_def_data.get_partitions_definition()
        if asset_node and asset_node.external_asset_node.partitions_def_data
        else None
    )
    return GrapheneAssetConditionEvaluation(
        record.get_evaluation_with_run_ids(partitions_def).evaluation,
        partitions_def,
        partition_key,
    )


def fetch_asset_condition_evaluation_records_for_asset_key(
    graphene_info: "ResolveInfo",
    graphene_asset_key: GrapheneAssetKeyInput,
    limit: int,
    cursor: Optional[str],
) -> GrapheneAssetConditionEvaluationRecordsOrError:
    """Fetch asset policy evaluations from storage."""
    migration_error = _get_migration_error(graphene_info)
    if migration_error:
        return migration_error

    asset_key = AssetKey.from_graphql_input(graphene_asset_key)

    schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
    return _get_graphene_records_from_evaluations(
        graphene_info,
        schedule_storage.get_auto_materialize_asset_evaluations(
            asset_key=asset_key,
            limit=limit,
            cursor=int(cursor) if cursor else None,
        ),
    )


def fetch_asset_condition_evaluation_records_for_evaluation_id(
    graphene_info: "ResolveInfo",
    evaluation_id: int,
) -> GrapheneAssetConditionEvaluationRecordsOrError:
    migration_error = _get_migration_error(graphene_info)
    if migration_error:
        return migration_error

    schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
    return _get_graphene_records_from_evaluations(
        graphene_info,
        schedule_storage.get_auto_materialize_evaluations_for_evaluation_id(
            evaluation_id=evaluation_id
        ),
    )
