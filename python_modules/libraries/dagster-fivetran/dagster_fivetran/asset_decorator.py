from typing import Any, Callable, Optional, Type

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import experimental

from dagster_fivetran.resources import FivetranWorkspace, load_fivetran_asset_specs
from dagster_fivetran.translator import DagsterFivetranTranslator, FivetranMetadataSet


@experimental
def fivetran_assets(
    *,
    connector_id: str,
    workspace: FivetranWorkspace,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_fivetran_translator: Type[DagsterFivetranTranslator] = DagsterFivetranTranslator,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to sync the tables of a given Fivetran connector.

    Args:
        connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
            "Setup" tab of a given connector in the Fivetran UI.
        workspace (FivetranWorkspace): The Fivetran workspace to fetch assets from.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_fivetran_translator (Type[DagsterFivetranTranslator]): The translator to use
            to convert Fivetran content into AssetSpecs. Defaults to DagsterFivetranTranslator.

    Examples:
        Sync the tables of a Fivetran connector:

        .. code-block:: python
            from dagster_fivetran import FivetranWorkspace, fivetran_assets

            import dagster as dg

            fivetran_workspace = FivetranWorkspace(
                account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
            )

            @fivetran_assets(
                connector_id="fivetran_connector_id",
                name="fivetran_connector_id",
                group_name="fivetran_connector_id",
                workspace=fivetran_workspace,
            )
            def fivetran_connector_assets(context: dg.AssetExecutionContext, fivetran: FivetranWorkspace):
                yield from fivetran.sync_and_poll(context=context)

            defs = dg.Definitions(
                assets=[fivetran_connector_assets],
                resources={"fivetran": fivetran_workspace},
            )

        Sync the tables of a Fivetran connector with a custom translator:

        .. code-block:: python
            from dagster_fivetran import (
                DagsterFivetranTranslator,
                FivetranConnectorTableProps,
                FivetranWorkspace,
                fivetran_assets
            )

            import dagster as dg
            from dagster._core.definitions.asset_spec import replace_attributes

            class CustomDagsterFivetranTranslator(DagsterFivetranTranslator):
                def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
                    asset_spec = super().get_asset_spec(props)
                    return replace_attributes(
                        asset_spec,
                        key=asset_spec.key.with_prefix("my_prefix"),
                    )


            fivetran_workspace = FivetranWorkspace(
                account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
            )

            @fivetran_assets(
                connector_id="fivetran_connector_id",
                name="fivetran_connector_id",
                group_name="fivetran_connector_id",
                workspace=fivetran_workspace,
                dagster_fivetran_translator=CustomDagsterFivetranTranslator,
            )
            def fivetran_connector_assets(context: dg.AssetExecutionContext, fivetran: FivetranWorkspace):
                yield from fivetran.sync_and_poll(context=context)

            defs = dg.Definitions(
                assets=[fivetran_connector_assets],
                resources={"fivetran": fivetran_workspace},
            )

    """
    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=[
            spec
            for spec in load_fivetran_asset_specs(
                workspace=workspace, dagster_fivetran_translator=dagster_fivetran_translator
            )
            if FivetranMetadataSet.extract(spec.metadata).connector_id == connector_id
        ],
    )
