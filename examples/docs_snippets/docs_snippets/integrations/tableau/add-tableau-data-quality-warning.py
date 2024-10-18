from dagster_tableau import TableauCloudWorkspace

import dagster as dg

# Connect to Tableau Cloud using the connected app credentials
workspace = TableauCloudWorkspace(
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


# We use Definitions.merge to combine the definitions from the Tableau workspace
# and the Dagster definitions into a single set of definitions to load
tableau_defs = workspace.build_defs()
upstream_defs = dg.Definitions(
    assets=[upstream_asset],
    sensors=[tableau_run_failure_sensor],
    resources={"tableau": workspace},
)

defs = dg.Definitions.merge(tableau_defs, upstream_defs)
