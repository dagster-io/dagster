from dagster_tableau import (
    TableauCloudWorkspace,
    build_tableau_materializable_assets_definition,
    load_tableau_asset_specs,
    parse_tableau_external_and_materializable_asset_specs,
)

import dagster as dg

# Connect to Tableau Cloud using the connected app credentials
tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)


@dg.asset(
    # Define which Tableau data source this upstream asset corresponds to
    metadata={"dagster/tableau_data_source_id": "f5660c7-2b05-4ff0-90ce-3199226956c6"}
)
def upstream_asset(): ...


@dg.run_failure_sensor
def tableau_run_failure_sensor(
    context: dg.RunFailureSensorContext, tableau: TableauCloudWorkspace
):
    asset_keys = context.dagster_run.asset_selection or set()
    for asset_key in asset_keys:
        data_source_id = upstream_asset.metadata_by_key.get(asset_key, {}).get(
            "dagster/tableau_data_source_id"
        )
        if data_source_id:
            with tableau.get_client() as client:
                client.add_data_quality_warning_to_data_source(
                    data_source_id=data_source_id, message=context.failure_event.message
                )


tableau_specs = load_tableau_asset_specs(
    workspace=tableau_workspace,
)

external_asset_specs, materializable_asset_specs = (
    parse_tableau_external_and_materializable_asset_specs(tableau_specs)
)

# Pass the sensor, Tableau resource, upstream asset, Tableau assets specs and materializable assets definition at once
defs = dg.Definitions(
    assets=[
        upstream_asset,
        build_tableau_materializable_assets_definition(
            resource_key="tableau",
            specs=materializable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *external_asset_specs,
    ],
    sensors=[tableau_run_failure_sensor],
    resources={"tableau": tableau_workspace},
)
