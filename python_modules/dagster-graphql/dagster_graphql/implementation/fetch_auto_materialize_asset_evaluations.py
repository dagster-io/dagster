from typing import TYPE_CHECKING, Optional

from dagster import AssetKey
from dagster._daemon.asset_daemon import get_current_evaluation_id

from dagster_graphql.implementation.fetch_assets import get_asset_nodes_by_asset_key
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
    GrapheneAutoMaterializeAssetEvaluationRecord,
    GrapheneAutoMaterializeAssetEvaluationRecords,
)
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def fetch_auto_materialize_asset_evaluations(
    graphene_info: "ResolveInfo",
    graphene_asset_key: GrapheneAssetKeyInput,
    limit: int,
    cursor: Optional[str],
):
    """Fetch asset policy evaluations from storage."""
    if graphene_info.context.instance.schedule_storage is None:
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message="Instance does not have schedule storage configured, cannot fetch evaluations."
        )
    if (
        not graphene_info.context.instance.schedule_storage.supports_auto_materialize_asset_evaluations
    ):
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message=(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )
        )

    asset_key = AssetKey.from_graphql_input(graphene_asset_key)
    asset_node = get_asset_nodes_by_asset_key(graphene_info).get(asset_key)
    partitions_def = (
        asset_node.external_asset_node.partitions_def_data.get_partitions_definition()
        if asset_node and asset_node.external_asset_node.partitions_def_data
        else None
    )

    current_evaluation_id = get_current_evaluation_id(graphene_info.context.instance)

    return GrapheneAutoMaterializeAssetEvaluationRecords(
        records=[
            GrapheneAutoMaterializeAssetEvaluationRecord(record, partitions_def=partitions_def)
            for record in graphene_info.context.instance.schedule_storage.get_auto_materialize_asset_evaluations(
                asset_key=asset_key,
                limit=limit,
                cursor=int(cursor) if cursor else None,
            )
        ],
        currentEvaluationId=current_evaluation_id,
    )
