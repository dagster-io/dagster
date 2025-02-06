from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import beta

from dagster_airbyte.resources import AirbyteCloudWorkspace
from dagster_airbyte.translator import AirbyteMetadataSet, DagsterAirbyteTranslator


@beta
def airbyte_assets(
    *,
    connection_id: str,
    workspace: AirbyteCloudWorkspace,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to sync the tables of a given Airbyte connection.

    Args:
        connection_id (str): The Airbyte Connection ID.
        workspace (AirbyteCloudWorkspace): The Airbyte workspace to fetch assets from.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
            to convert Airbyte content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterAirbyteTranslator`.

    Examples:
        Sync the tables of an Airbyte connection:

        .. code-block:: python

            from dagster_airbyte import AirbyteCloudWorkspace, airbyte_assets

            import dagster as dg

            airbyte_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )


            @airbyte_assets(
                connection_id="airbyte_connection_id",
                workspace=airbyte_workspace,
            )
            def airbyte_connection_assets(context: dg.AssetExecutionContext, airbyte: AirbyteCloudWorkspace):
                yield from airbyte.sync_and_poll(context=context)


            defs = dg.Definitions(
                assets=[airbyte_connection_assets],
                resources={"airbyte": airbyte_workspace},
            )

        Sync the tables of an Airbyte connection with a custom translator:

        .. code-block:: python

            from dagster_airbyte import (
                DagsterAirbyteTranslator,
                AirbyteConnectionTableProps,
                AirbyteCloudWorkspace,
                airbyte_assets
            )

            import dagster as dg

            class CustomDagsterAirbyteTranslator(DagsterAirbyteTranslator):
                def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
                    default_spec = super().get_asset_spec(props)
                    return default_spec.merge_attributes(
                        metadata={"custom": "metadata"},
                    )

            airbyte_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )


            @airbyte_assets(
                connection_id="airbyte_connection_id",
                workspace=airbyte_workspace,
                dagster_airbyte_translator=CustomDagsterAirbyteTranslator()
            )
            def airbyte_connection_assets(context: dg.AssetExecutionContext, airbyte: AirbyteCloudWorkspace):
                yield from airbyte.sync_and_poll(context=context)


            defs = dg.Definitions(
                assets=[airbyte_connection_assets],
                resources={"airbyte": airbyte_workspace},
            )
    """
    dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=[
            spec
            for spec in workspace.load_asset_specs(
                dagster_airbyte_translator=dagster_airbyte_translator
            )
            if AirbyteMetadataSet.extract(spec.metadata).connection_id == connection_id
        ],
    )
