from typing import Optional

from dagster import AssetKey, DagsterInstance

from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
    GrapheneAutoMaterializeAssetEvaluationRecord,
    GrapheneAutoMaterializeAssetEvaluationRecords,
)
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput


def fetch_auto_materialize_asset_evaluations(
    instance: DagsterInstance,
    asset_key: GrapheneAssetKeyInput,
    limit: int,
    cursor: Optional[str],
):
    """Fetch asset policy evaluations from storage."""
    if instance.schedule_storage is None:
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message="Instance does not have schedule storage configured, cannot fetch evaluations."
        )
    if not instance.schedule_storage.supports_auto_materialize_asset_evaluations:
        return GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(
            message=(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )
        )

    return GrapheneAutoMaterializeAssetEvaluationRecords(
        records=[
            GrapheneAutoMaterializeAssetEvaluationRecord(record)
            for record in instance.schedule_storage.get_auto_materialize_asset_evaluations(
                asset_key=AssetKey.from_graphql_input(asset_key),
                limit=limit,
                cursor=int(cursor) if cursor else None,
            )
        ]
    )
