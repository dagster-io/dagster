from dagster_airbyte import AirbyteCloudWorkspace, airbyte_assets

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)


# start_downstream_asset
@airbyte_assets(
    connection_id="airbyte_connection_id",  # Replace with your connection ID
    workspace=airbyte_workspace,
)
def airbyte_connection_assets(
    context: dg.AssetExecutionContext, airbyte: AirbyteCloudWorkspace
): ...


my_airbyte_cloud_table_asset_key = next(
    iter(
        [
            spec.key
            for spec in airbyte_connection_assets.specs
            if spec.metadata.get("dagster/table_name")
            == "my_database.my_schema.my_airbyte_cloud_table"
        ]
    )
)


@dg.asset(deps=[my_airbyte_cloud_table_asset_key])
def my_downstream_asset(): ...


# end_downstream_asset
