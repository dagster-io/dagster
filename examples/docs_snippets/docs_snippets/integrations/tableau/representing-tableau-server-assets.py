from dagster_tableau import TableauServerWorkspace

import dagster as dg

# Connect to Tableau Server using the connected app credentials
workspace = TableauServerWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    server_name=dg.EnvVar("TABLEAU_SERVER_NAME"),
)

defs = workspace.build_defs()
