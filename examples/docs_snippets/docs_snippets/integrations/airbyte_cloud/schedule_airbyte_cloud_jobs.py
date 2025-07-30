from dagster_airbyte import AirbyteCloudWorkspace, airbyte_assets

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)


@airbyte_assets(
    connection_id="airbyte_connection_id",  # Replace with your connection ID
    workspace=airbyte_workspace,
    name="airbyte_connection_name",  # Replace with your connection name
)
def airbyte_connection_assets(
    context: dg.AssetExecutionContext, airbyte: AirbyteCloudWorkspace
):
    yield from airbyte.sync_and_poll(context=context)


airbyte_connection_assets_job = dg.define_asset_job(
    name="airbyte_connection_assets_job",
    selection=[airbyte_connection_assets],
)

# start_airbyte_cloud_schedule
airbyte_connection_assets_schedule = dg.ScheduleDefinition(
    job=airbyte_connection_assets_job,
    cron_schedule="0 0 * * *",  # Runs at midnight daily
)


defs = dg.Definitions(
    assets=[airbyte_connection_assets],
    jobs=[airbyte_connection_assets_job],
    schedules=[airbyte_connection_assets_schedule],
    resources={"airbyte": airbyte_workspace},
)
# end_airbyte_cloud_schedule
