import uuid

import pytest
import responses
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_fetch_tableau_workspace_data(
    clazz, host_key, host_value, site_name, workspace_data_api_mocks_fn
) -> None:
    fake_personal_access_token_name = "fake_personal_access_token_name"
    fake_personal_access_token_value = uuid.uuid4().hex

    resource_args = {
        "personal_access_token_name": fake_personal_access_token_name,
        "personal_access_token_value": fake_personal_access_token_value,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)

    yield from workspace_data_api_mocks_fn(api_base_url=resource.api_base_url)

    actual_workspace_data = resource.fetch_tableau_workspace_data()
    assert len(actual_workspace_data.workbooks_by_id) == 1
    assert len(actual_workspace_data.views_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 1


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_translator_spec(
    clazz, host_key, host_value, site_name, workspace_data_api_mocks_fn
) -> None:
    fake_personal_access_token_name = "fake_personal_access_token_name"
    fake_personal_access_token_value = uuid.uuid4().hex

    resource_args = {
        "personal_access_token_name": fake_personal_access_token_name,
        "personal_access_token_value": fake_personal_access_token_value,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)

    yield from workspace_data_api_mocks_fn(api_base_url=resource.api_base_url)

    all_asset_specs = resource.build_asset_specs()

    # 1 view and 1 data source
    assert len(all_asset_specs) == 2

    # Sanity check outputs, translator tests cover details here
    view_spec = next(spec for spec in all_asset_specs if spec.key.path[0] == "view")
    assert view_spec.key.path == ["view", "sales"]

    data_source_spec = next(spec for spec in all_asset_specs if spec.key.path[0] == "data_source")
    assert data_source_spec.key.path == ["superstore_datasource"]
