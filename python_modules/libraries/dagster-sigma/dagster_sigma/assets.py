from typing import cast

from dagster import AssetExecutionContext, AssetsDefinition, AssetSpec, multi_asset
from dagster._annotations import experimental


@experimental
def build_rebuild_workbook_assets_definition(
    resource_key: str,
    spec: AssetSpec,
) -> AssetsDefinition:
    """Returns the AssetsDefinition which rebuilds a Sigma workbook.

    Args:
        resource_key (str): The resource key to use for the Sigma resource.
        spec (AssetSpec): The asset spec of the Sigma workbook.

    Returns:
        AssetsDefinition: The AssetsDefinition which rebuilds a Sigma workbook.
    """
    from dagster_sigma import SigmaOrganization

    @multi_asset(
        name=f"sigma_materialize_{spec.key.to_python_identifier()}",
        specs=[spec],
        required_resource_keys={resource_key},
    )
    def asset_fn(context: AssetExecutionContext):
        sigma = cast(SigmaOrganization, getattr(context.resources, resource_key))
        yield from sigma.run_materializations_for_workbook(spec)

    return asset_fn
