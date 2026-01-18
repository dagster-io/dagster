from collections.abc import Callable
from typing import Any, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import beta, beta_param
from dagster._core.errors import DagsterInvariantViolationError

from dagster_tableau.asset_utils import parse_tableau_external_and_materializable_asset_specs
from dagster_tableau.resources import BaseTableauWorkspace, load_tableau_asset_specs
from dagster_tableau.translator import DagsterTableauTranslator, WorkbookSelectorFn


@beta
@beta_param(param="workbook_selector_fn")
def tableau_assets(
    *,
    workspace: BaseTableauWorkspace,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_tableau_translator: Optional[DagsterTableauTranslator] = None,
    workbook_selector_fn: Optional[WorkbookSelectorFn] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to refresh the extracted data sources and views of a given Tableau workspace.

    Args:
        workspace (Union[TableauCloudWorkspace, TableauServerWorkspace]): The Tableau workspace to fetch assets from.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_tableau_translator (Optional[DagsterTableauTranslator], optional): The translator to use
            to convert Tableau content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterTableauTranslator`.
        workbook_selector_fn (Optional[WorkbookSelectorFn]):
            A function that allows for filtering which Tableau workbook assets are created for,
            including data sources, sheets and dashboards.

    Examples:
        Refresh extracted data sources and views in Tableau:

        .. code-block:: python

            from dagster_tableau import TableauCloudWorkspace, tableau_assets

            import dagster as dg

            tableau_workspace = TableauCloudWorkspace(
                connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
                connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
                connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
                username=dg.EnvVar("TABLEAU_USERNAME"),
                site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
                pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
            )

            @tableau_assets(
                workspace=tableau_workspace,
                name="tableau_workspace_assets",
                group_name="tableau",
            )
            def tableau_workspace_assets(context: dg.AssetExecutionContext, tableau: TableauCloudWorkspace):
                yield from tableau.refresh_and_poll(context=context)

            defs = dg.Definitions(
                assets=[tableau_workspace_assets],
                resources={"tableau": tableau_workspace},
            )

        Refresh extracted data sources and views in Tableau with a custom translator:

        .. code-block:: python

            from dagster_tableau import (
                DagsterTableauTranslator,
                TableauTranslatorData,
                TableauCloudWorkspace,
                tableau_assets
            )

            import dagster as dg

            class CustomDagsterTableauTranslator(DagsterTableauTranslator):
                def get_asset_spec(self, data: TableauTranslatorData) -> dg.AssetSpec:
                    default_spec = super().get_asset_spec(data)
                    return default_spec.replace_attributes(
                        key=default_spec.key.with_prefix("my_prefix"),
                    )

            tableau_workspace = TableauCloudWorkspace(
                connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
                connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
                connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
                username=dg.EnvVar("TABLEAU_USERNAME"),
                site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
                pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
            )

            @tableau_assets(
                workspace=tableau_workspace,
                name="tableau_workspace_assets",
                group_name="tableau",
                dagster_tableau_translator=CustomDagsterTableauTranslator(),
            )
            def tableau_workspace_assets(context: dg.AssetExecutionContext, tableau: TableauCloudWorkspace):
                yield from tableau.refresh_and_poll(context=context)

            defs = dg.Definitions(
                assets=[tableau_workspace_assets],
                resources={"tableau": tableau_workspace},
            )

    """
    dagster_tableau_translator = dagster_tableau_translator or DagsterTableauTranslator()

    external_asset_specs, materializable_asset_specs = (
        parse_tableau_external_and_materializable_asset_specs(
            load_tableau_asset_specs(
                workspace=workspace,
                dagster_tableau_translator=dagster_tableau_translator,
                workbook_selector_fn=workbook_selector_fn,
            ),
            include_data_sources_with_extracts=True,
        )
    )

    if any([spec for spec in materializable_asset_specs if spec.group_name]) and group_name:
        raise DagsterInvariantViolationError(
            f"Cannot set group_name parameter on tableau_assets with site {workspace.site_name} - "
            f"one or more of the Tableau asset specs have a group_name defined."
        )

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=materializable_asset_specs,
    )
