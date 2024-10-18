from dagster_tableau import TableauCloudWorkspace

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

# We use Definitions.merge to combine the definitions from both workspaces
# into a single set of definitions to load
defs = dg.Definitions.merge(
    sales_team_workspace.build_defs(),
    marketing_team_workspace.build_defs(),
)
