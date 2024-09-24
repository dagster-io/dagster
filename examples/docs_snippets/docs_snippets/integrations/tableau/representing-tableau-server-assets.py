from dagster_tableau import TableauServerWorkspace

from dagster import EnvVar

# Connect to Tableau Server using the connected app credentials
workspace = TableauServerWorkspace(
    connected_app_client_id=EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=EnvVar("TABLEAU_USERNAME"),
    site_name=EnvVar("TABLEAU_SITE_NAME"),
    server_name=EnvVar("TABLEAU_SERVER_NAME"),
)

defs = workspace.build_defs()
