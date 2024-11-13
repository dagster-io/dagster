from dagster_tableau import (
    TableauCloudWorkspace,
    build_tableau_materializable_assets_definition,
    load_tableau_asset_specs,
    parse_tableau_external_and_materializable_asset_specs,
)

import dagster as dg

tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)

# Load Tableau asset specs
tableau_specs = load_tableau_asset_specs(
    workspace=tableau_workspace,
)

external_asset_specs, materializable_asset_specs = (
    parse_tableau_external_and_materializable_asset_specs(tableau_specs)
)

# Use the asset definition builder to construct the definition for tableau materializable assets
defs = dg.Definitions(
    assets=[
        build_tableau_materializable_assets_definition(
            resource_key="tableau",
            specs=materializable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *external_asset_specs,
    ],
    resources={"tableau": tableau_workspace},
)
