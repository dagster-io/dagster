from dagster import asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster_tableau import TableauCloudWorkspace

from dagster_tableau_tests.conftest import (
    FAKE_CONNECTED_APP_CLIENT_ID,
    FAKE_CONNECTED_APP_SECRET_ID,
    FAKE_CONNECTED_APP_SECRET_VALUE,
    FAKE_POD_NAME,
    FAKE_SITE_NAME,
    FAKE_USERNAME,
)

resource = TableauCloudWorkspace(
    connected_app_client_id=FAKE_CONNECTED_APP_CLIENT_ID,
    connected_app_secret_id=FAKE_CONNECTED_APP_SECRET_ID,
    connected_app_secret_value=FAKE_CONNECTED_APP_SECRET_VALUE,
    username=FAKE_USERNAME,
    site_name=FAKE_SITE_NAME,
    pod_name=FAKE_POD_NAME,
)

pbi_defs = resource.build_defs()


@asset
def my_materializable_asset():
    pass


defs = Definitions.merge(
    Definitions(assets=[my_materializable_asset], jobs=[define_asset_job("all_asset_job")]),
    pbi_defs,
)
