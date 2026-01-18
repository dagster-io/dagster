from dagster_tableau import TableauCloudWorkspace, load_tableau_asset_specs

import dagster as dg

sales_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("SALES_TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("SALES_TABLEAU_POD_NAME"),
)

marketing_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("MARKETING_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("MARKETING_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar(
        "MARKETING_TABLEAU_CONNECTED_APP_SECRET_VALUE"
    ),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("MARKETING_TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("MARKETING_TABLEAU_POD_NAME"),
)


sales_team_specs = load_tableau_asset_specs(sales_team_workspace)
marketing_team_specs = load_tableau_asset_specs(marketing_team_workspace)

defs = dg.Definitions(
    assets=[*sales_team_specs, *marketing_team_specs],
    resources={
        "marketing_tableau": marketing_team_workspace,
        "sales_tableau": sales_team_workspace,
    },
)
