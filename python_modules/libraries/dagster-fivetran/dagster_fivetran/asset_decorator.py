from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import beta

from dagster_fivetran.resources import FivetranWorkspace
from dagster_fivetran.translator import (
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
    FivetranMetadataSet,
)


@beta
def fivetran_assets(
    *,
    connector_id: str,
    workspace: FivetranWorkspace,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_fivetran_translator: Optional[DagsterFivetranTranslator] = None,
    connector_selector_fn: Optional[ConnectorSelectorFn] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to sync the tables of a given Fivetran connector.

    Args:
        connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
            "Setup" tab of a given connector in the Fivetran UI.
        workspace (FivetranWorkspace): The Fivetran workspace to fetch assets from.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_fivetran_translator (Optional[DagsterFivetranTranslator], optional): The translator to use
            to convert Fivetran content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterFivetranTranslator`.
        connector_selector_fn (Optional[ConnectorSelectorFn]):
                A function that allows for filtering which Fivetran connector assets are created for.

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

            class CustomDagsterFivetranTranslator(DagsterFivetranTranslator):
                def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
                    default_spec = super().get_asset_spec(props)
                    return default_spec.replace_attributes(
                        key=default_spec.key.with_prefix("my_prefix"),
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
                dagster_fivetran_translator=CustomDagsterFivetranTranslator(),
            )
            def fivetran_connector_assets(context: dg.AssetExecutionContext, fivetran: FivetranWorkspace):
                yield from fivetran.sync_and_poll(context=context)

            defs = dg.Definitions(
                assets=[fivetran_connector_assets],
                resources={"fivetran": fivetran_workspace},
            )

    """
    dagster_fivetran_translator = dagster_fivetran_translator or DagsterFivetranTranslator()
    connector_selector_fn = connector_selector_fn or (
        lambda connector: connector.id == connector_id
    )

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=[
            spec
            for spec in workspace.load_asset_specs(
                dagster_fivetran_translator=dagster_fivetran_translator,
                connector_selector_fn=connector_selector_fn,
            )
            if FivetranMetadataSet.extract(spec.metadata).connector_id == connector_id
        ],
    )
