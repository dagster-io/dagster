from dagster_tableau import TableauCloudWorkspace

from dagster import Definitions, EnvVar

sales_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=EnvVar("SALES_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=EnvVar("TABLEAU_USERNAME"),
    site_name=EnvVar("SALES_TABLEAU_SITE_NAME"),
    pod_name=EnvVar("SALES_TABLEAU_POD_NAME"),
)

marketing_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=EnvVar("MARKETING_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=EnvVar("MARKETING_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=EnvVar("MARKETING_TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=EnvVar("TABLEAU_USERNAME"),
    site_name=EnvVar("MARKETING_TABLEAU_SITE_NAME"),
    pod_name=EnvVar("MARKETING_TABLEAU_POD_NAME"),
)

# We use Definitions.merge to combine the definitions from both workspaces
# into a single set of definitions to load
defs = Definitions.merge(
    sales_team_workspace.build_defs(),
    marketing_team_workspace.build_defs(),
)
