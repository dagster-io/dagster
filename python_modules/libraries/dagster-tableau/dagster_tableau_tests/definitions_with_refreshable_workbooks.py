from dagster import define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster_tableau import (
    TableauCloudWorkspace,
    build_tableau_executable_assets_definition,
    load_tableau_asset_specs,
)

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

tableau_specs = load_tableau_asset_specs(
    workspace=resource,
)

non_executable_asset_specs = [
    spec for spec in tableau_specs if spec.tags.get("dagster-tableau/asset_type") == "data_source"
]

executable_asset_specs = [
    spec
    for spec in tableau_specs
    if spec.tags.get("dagster-tableau/asset_type") in ["dashboard", "sheet"]
]

resource_key = "tableau"

defs = Definitions(
    assets=[
        build_tableau_executable_assets_definition(
            resource_key=resource_key,
            workspace=resource,
            specs=executable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *non_executable_asset_specs,
    ],
    jobs=[define_asset_job("all_asset_job")],
    resources={resource_key: resource},
)
