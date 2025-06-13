from dagster_tableau import (
    DagsterTableauTranslator,
    TableauCloudWorkspace,
    TableauContentType,
    TableauTranslatorData,
    load_tableau_asset_specs,
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


# start_upstream_asset
class MyCustomTableauTranslator(DagsterTableauTranslator):
    def get_asset_spec(self, data: TableauTranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize upstream dependencies for the Tableau sheet named `my_tableau_sheet`
        return default_spec.replace_attributes(
            deps=["my_upstream_asset"]
            if data.content_type == TableauContentType.SHEET
            and data.properties.get("name") == "my_tableau_sheet"
            else ...
        )


tableau_specs = load_tableau_asset_specs(
    tableau_workspace,
    dagster_tableau_translator=MyCustomTableauTranslator(),
)
# end_upstream_asset

defs = dg.Definitions(assets=[*tableau_specs], resources={"tableau": tableau_workspace})
