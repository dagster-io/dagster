from typing import cast

from dagster import (
    _check as check,
    multi_asset,
)
from dagster._annotations import beta
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext

from dagster_powerbi.resource import PowerBIWorkspace
from dagster_powerbi.translator import PowerBIMetadataSet, PowerBITagSet


@beta
def build_semantic_model_refresh_asset_definition(
    resource_key: str, spec: AssetSpec
) -> AssetsDefinition:
    """Builds an asset definition for refreshing a PowerBI semantic model."""
    check.invariant(PowerBITagSet.extract(spec.tags).asset_type == "semantic_model")
    dataset_id = check.not_none(PowerBIMetadataSet.extract(spec.metadata).id)

    @multi_asset(
        specs=[spec],
        name="_".join(spec.key.path),
        required_resource_keys={resource_key},
    )
    def asset_fn(context: AssetExecutionContext) -> None:
        power_bi = cast(PowerBIWorkspace, getattr(context.resources, resource_key))
        power_bi.trigger_and_poll_refresh(dataset_id)

    return asset_fn
