from dagster_airbyte import AirbyteCloudWorkspace, airbyte_assets

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)


@airbyte_assets(
    # Replace with your connection_id
    connection_id="airbyte_connection_id",
    workspace=airbyte_workspace,
    # Replace with your connection_name
    name="airbyte_connection_name",
    group_name="airbyte_connection_name",
)
def airbyte_connection_assets(
    context: dg.AssetExecutionContext, airbyte: AirbyteCloudWorkspace
):
    # Do something before the materialization...
    yield from airbyte.sync_and_poll(context=context)
    # Do something after the materialization...


defs = dg.Definitions(
    assets=[airbyte_connection_assets],
    resources={"airbyte": airbyte_workspace},
)
