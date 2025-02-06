from collections.abc import Sequence
from typing import Optional, cast

from dagster import AssetExecutionContext, AssetsDefinition, AssetSpec, multi_asset
from dagster._annotations import beta

from dagster_tableau.resources import BaseTableauWorkspace


@beta
def build_tableau_materializable_assets_definition(
    resource_key: str,
    specs: Sequence[AssetSpec],
    refreshable_workbook_ids: Optional[Sequence[str]] = None,
) -> AssetsDefinition:
    """Returns the AssetsDefinition of the materializable assets in the Tableau workspace.

    Args:
        resource_key (str): The resource key to use for the Tableau resource.
        specs (Sequence[AssetSpec]): The asset specs of the executable assets in the Tableau workspace.
        refreshable_workbook_ids (Optional[Sequence[str]]): A list of workbook IDs. The workbooks provided must
            have extracts as data sources and be refreshable in Tableau.

            When materializing your Tableau assets, the workbooks provided are refreshed,
            refreshing their sheets and dashboards before pulling their data in Dagster.

            This feature is equivalent to selecting Refreshing Extracts for a workbook in Tableau UI
            and only works for workbooks for which the data sources are extracts.
            See https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#update_workbook_now
            for documentation.

    Returns:
        AssetsDefinition: The AssetsDefinition of the executable assets in the Tableau workspace.
    """

    @multi_asset(
        name=f"tableau_sync_site_{resource_key}",
        compute_kind="tableau",
        can_subset=False,
        specs=specs,
        required_resource_keys={resource_key},
    )
    def asset_fn(context: AssetExecutionContext):
        tableau = cast(BaseTableauWorkspace, getattr(context.resources, resource_key))
        with tableau.get_client() as client:
            yield from client.refresh_and_materialize_workbooks(
                specs=specs, refreshable_workbook_ids=refreshable_workbook_ids
            )

    return asset_fn
