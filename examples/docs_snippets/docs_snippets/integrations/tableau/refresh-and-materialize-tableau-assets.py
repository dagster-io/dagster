from dagster_tableau import StartWorkbookRefreshRequest, TableauCloudWorkspace

from dagster import EnvVar

workspace = TableauCloudWorkspace(
    connected_app_client_id=EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=EnvVar("TABLEAU_USERNAME"),
    site_name=EnvVar("TABLEAU_SITE_NAME"),
    pod_name=EnvVar("TABLEAU_POD_NAME"),
)

defs = workspace.build_defs(
    start_workbook_refresh_requests=[
        StartWorkbookRefreshRequest(workbook_id="b75fc023-a7ca-4115-857b-4342028640d0")
    ]
)
