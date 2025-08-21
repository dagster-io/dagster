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
def tableau_workspace_assets(
    context: dg.AssetExecutionContext, tableau: TableauCloudWorkspace
):
    yield from tableau.refresh_and_poll(context=context)


defs = dg.Definitions(
    assets=[tableau_workspace_assets],
    resources={"tableau": tableau_workspace},
)
