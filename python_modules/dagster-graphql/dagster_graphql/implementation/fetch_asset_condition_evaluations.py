from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.schema.asset_condition_evaluations import (
    GrapheneAssetConditionEvaluation,
    GrapheneAssetConditionEvaluationRecord,
    GrapheneAssetConditionEvaluationRecords,
    GrapheneAssetConditionEvaluationRecordsOrError,
)
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
)
from dagster_graphql.schema.inputs import GrapheneAssetCheckHandleInput, GrapheneAssetKeyInput

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


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
    return GrapheneAssetConditionEvaluationRecords(
        records=[
            GrapheneAssetConditionEvaluationRecord(evaluation) for evaluation in evaluation_records
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
    return GrapheneAssetConditionEvaluation(
        record.get_evaluation_with_run_ids().evaluation, partition_key
    )


def entity_key_from_graphql_input(
    graphene_input: Union[GrapheneAssetKeyInput, GrapheneAssetCheckHandleInput],
) -> EntityKey:
    if "path" in graphene_input:
        return AssetKey.from_graphql_input(graphene_input)
    else:
        return AssetCheckKey.from_graphql_input(graphene_input)


def fetch_true_partitions_for_evaluation_node(
    graphene_info: "ResolveInfo",
    graphene_entity_key: Union[GrapheneAssetKeyInput, GrapheneAssetCheckHandleInput],
    evaluation_id: int,
    node_unique_id: str,
) -> Sequence[str]:
    key = entity_key_from_graphql_input(graphene_entity_key)
    schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
    record = next(
        iter(
            schedule_storage.get_auto_materialize_asset_evaluations(
                # there is no method to get a specific evaluation by id, so instead get the first
                # evaluation before evaluation_id + 1
                key=key,
                cursor=evaluation_id + 1,
                limit=1,
            )
        )
    )
    check.invariant(
        record.evaluation_id == evaluation_id, f"Could not find evaluation with id {evaluation_id}"
    )

    # it's no longer necessary to pass in the partitions def in to get_evaluation_with_run_ids
    root_evaluation = record.get_evaluation_with_run_ids().evaluation
    for evaluation in root_evaluation.iter_nodes():
        if evaluation.condition_snapshot.unique_id == node_unique_id:
            return (
                list(evaluation.true_subset.subset_value.get_partition_keys())
                if evaluation.true_subset.is_partitioned
                else ["None"]
            )
    check.failed("No matching unique id found")


def fetch_asset_condition_evaluation_records_for_asset_key(
    graphene_info: "ResolveInfo",
    graphene_entity_key: Union[GrapheneAssetKeyInput, GrapheneAssetCheckHandleInput],
    limit: int,
    cursor: Optional[str],
) -> GrapheneAssetConditionEvaluationRecordsOrError:
    """Fetch asset policy evaluations from storage."""
    migration_error = _get_migration_error(graphene_info)
    if migration_error:
        return migration_error

    key = entity_key_from_graphql_input(graphene_entity_key)

    schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
    return _get_graphene_records_from_evaluations(
        graphene_info,
        schedule_storage.get_auto_materialize_asset_evaluations(
            key=key,
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
