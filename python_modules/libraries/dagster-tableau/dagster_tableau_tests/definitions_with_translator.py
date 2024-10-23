from dagster import AssetSpec, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster_tableau import (
    DagsterTableauTranslator,
    TableauCloudWorkspace,
    load_tableau_asset_specs,
)
from dagster_tableau.translator import TableauContentData

from dagster_tableau_tests.conftest import (
    FAKE_CONNECTED_APP_CLIENT_ID,
    FAKE_CONNECTED_APP_SECRET_ID,
    FAKE_CONNECTED_APP_SECRET_VALUE,
    FAKE_POD_NAME,
    FAKE_SITE_NAME,
    FAKE_USERNAME,
)


class MyCoolTranslator(DagsterTableauTranslator):
    def get_sheet_spec(self, data: TableauContentData) -> AssetSpec:
        spec = super().get_sheet_spec(data)
        return spec._replace(key=spec.key.with_prefix("my_prefix"))

    def get_dashboard_spec(self, data: TableauContentData) -> AssetSpec:
        spec = super().get_dashboard_spec(data)
        return spec._replace(key=spec.key.with_prefix("my_prefix"))

    def get_data_source_spec(self, data: TableauContentData) -> AssetSpec:
        spec = super().get_data_source_spec(data)
        return spec._replace(key=spec.key.with_prefix("my_prefix"))


resource = TableauCloudWorkspace(
    connected_app_client_id=FAKE_CONNECTED_APP_CLIENT_ID,
    connected_app_secret_id=FAKE_CONNECTED_APP_SECRET_ID,
    connected_app_secret_value=FAKE_CONNECTED_APP_SECRET_VALUE,
    username=FAKE_USERNAME,
    site_name=FAKE_SITE_NAME,
    pod_name=FAKE_POD_NAME,
)

tableau_specs = load_tableau_asset_specs(
    workspace=resource, dagster_tableau_translator=MyCoolTranslator
)


defs = Definitions(assets=[*tableau_specs], jobs=[define_asset_job("all_asset_job")])
