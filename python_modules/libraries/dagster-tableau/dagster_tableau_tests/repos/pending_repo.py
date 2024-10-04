from typing import cast

from dagster import asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    PendingRepositoryDefinition,
)
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


pending_repo_from_cached_asset_metadata = cast(
    PendingRepositoryDefinition,
    Definitions.merge(
        Definitions(assets=[my_materializable_asset], jobs=[define_asset_job("all_asset_job")]),
        pbi_defs,
    ).get_inner_repository(),
)
