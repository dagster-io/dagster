from dagster_tableau import DagsterTableauTranslator, TableauCloudWorkspace
from dagster_tableau.translator import TableauContentData

from dagster import AssetSpec, EnvVar

workspace = TableauCloudWorkspace(
    connected_app_client_id=EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=EnvVar("TABLEAU_USERNAME"),
    site_name=EnvVar("TABLEAU_SITE_NAME"),
    pod_name=EnvVar("TABLEAU_POD_NAME"),
)


# A translator class lets us customize properties of the built
# Tableau assets, such as the owners or asset key
class MyCustomTableauTranslator(DagsterTableauTranslator):
    def get_sheet_spec(self, data: TableauContentData) -> AssetSpec:
        # We add a custom team owner tag to all sheets
        return super().get_sheet_spec(data)._replace(owners=["my_team"])


defs = workspace.build_defs(dagster_tableau_translator=MyCustomTableauTranslator)
