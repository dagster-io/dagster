from dagster_tableau import (
    DagsterTableauTranslator,
    TableauCloudWorkspace,
    load_tableau_asset_specs,
)
from dagster_tableau.translator import TableauContentType, TableauTranslatorData

import dagster as dg

tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)


# A translator class lets us customize properties of the built
# Tableau assets, such as the owners or asset key
class MyCustomTableauTranslator(DagsterTableauTranslator):
    def get_asset_spec(self, data: TableauTranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize the metadata and asset key prefix for all assets, including sheets,
        # and we customize the team owner tag only for sheets.
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
            owners=(
                ["team:my_team"]
                if data.content_type == TableauContentType.SHEET
                else ...
            ),
        )


tableau_specs = load_tableau_asset_specs(
    tableau_workspace,
    dagster_tableau_translator=MyCustomTableauTranslator(),
)
defs = dg.Definitions(assets=[*tableau_specs], resources={"tableau": tableau_workspace})
