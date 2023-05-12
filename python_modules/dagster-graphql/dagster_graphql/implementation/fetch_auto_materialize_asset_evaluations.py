from typing import Optional, Sequence

from dagster import AssetKey, DagsterInstance

from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationRecord,
)
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput


def fetch_auto_materialize_asset_evaluations(
    instance: DagsterInstance,
    asset_key: GrapheneAssetKeyInput,
    limit: int,
    cursor: Optional[int],
) -> Sequence[GrapheneAutoMaterializeAssetEvaluationRecord]:
    """Fetch asset policy evaluations from storage."""
    return [
        GrapheneAutoMaterializeAssetEvaluationRecord(record)
        for record in instance.schedule_storage.get_auto_materialize_asset_evaluations(
            AssetKey.from_graphql_input(asset_key), limit, cursor
        )
    ]
