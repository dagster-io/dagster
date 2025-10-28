from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, cast

from dagster import AssetExecutionContext, AssetsDefinition, AssetSpec, multi_asset
from dagster._annotations import beta, deprecated_param, superseded
from dagster_shared import check

if TYPE_CHECKING:
    from dagster_tableau.resources import BaseTableauWorkspace


@superseded(additional_warn_text="Use `tableau_assets` decorator instead.")
@deprecated_param(
    param="refreshable_workbook_ids",
    breaking_version="0.27",
    additional_warn_text="Use `refreshable_data_source_ids` instead.",
)
@beta
def build_tableau_materializable_assets_definition(
    resource_key: str,
    specs: Sequence[AssetSpec],
    refreshable_workbook_ids: Optional[Sequence[str]] = None,
    refreshable_data_source_ids: Optional[Sequence[str]] = None,
) -> AssetsDefinition:
    """Returns the AssetsDefinition of the materializable assets in the Tableau workspace.

    Args:
        resource_key (str): The resource key to use for the Tableau resource.
        specs (Sequence[AssetSpec]): The asset specs of the executable assets in the Tableau workspace.
        refreshable_workbook_ids (Optional[Sequence[str]]): A list of workbook IDs. The provided workbooks must
            have extracts as data sources and be refreshable in Tableau.

            When materializing your Tableau assets, the workbooks provided are refreshed,
            refreshing their sheets and dashboards before pulling their data in Dagster.

            This feature is equivalent to selecting Refreshing Extracts for a workbook in Tableau UI
            and only works for workbooks for which the data sources are extracts.
            See https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#update_workbook_now
            for documentation.
        refreshable_data_source_ids (Optional[Sequence[str]]): A list of data source IDs. The provided data sources must
            have extracts and be refreshable in Tableau.

            When materializing your Tableau assets, the provided data source are refreshed,
            refreshing upstream sheets and dashboards before pulling their data in Dagster.

            This feature is equivalent to selecting Refreshing Extracts for a data source in Tableau UI
            and only works for data sources that have extracts.
            See https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_data_sources.htm#update_data_source_now
            for documentation.

    Returns:
        AssetsDefinition: The AssetsDefinition of the executable assets in the Tableau workspace.
    """
    check.param_invariant(
        not (refreshable_workbook_ids and refreshable_data_source_ids),
        "refreshable_data_source_ids",
        "Cannot provide both refreshable workbook IDs and refreshable data source IDs.",
    )

    @multi_asset(
        name=f"tableau_sync_site_{resource_key}",
        can_subset=False,
        specs=specs,
        required_resource_keys={resource_key},
    )
    def asset_fn(context: AssetExecutionContext):
        tableau = cast("BaseTableauWorkspace", getattr(context.resources, resource_key))
        with tableau.get_client() as client:
            if refreshable_workbook_ids:
                yield from client.refresh_and_materialize_workbooks(
                    specs=specs, refreshable_workbook_ids=refreshable_workbook_ids
                )
            else:
                yield from client.refresh_and_materialize(
                    specs=specs, refreshable_data_source_ids=refreshable_data_source_ids
                )

    return asset_fn
