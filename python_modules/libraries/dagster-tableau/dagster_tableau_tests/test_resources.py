import uuid
from unittest.mock import MagicMock

import pytest
from dagster import asset, instance_for_test, materialize
from dagster_tableau.resources import TableauCloudWorkspace, TableauServerWorkspace, Union


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_basic_resource_request(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    api_token: str,
    workbook_id: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore

    @asset
    def test_assets():
        with resource.get_client() as client:
            client.get_workbooks()
            client.get_workbook(workbook_id=workbook_id)

    with instance_for_test() as instance:
        materialize(
            [test_assets],
            instance=instance,
            resources={"tableau": resource},
        )

    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    get_workbook.assert_called_with(workbook_id=workbook_id)


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_add_data_quality_warning(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    api_token: str,
    workbook_id: str,
    sign_in: MagicMock,
    get_data_source_by_id: MagicMock,
    build_data_quality_warning_item: MagicMock,
    add_data_quality_warning: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore

    with resource.get_client() as client:
        client.add_data_quality_warning_to_data_source(data_source_id="fake_datasource_id")

    assert get_data_source_by_id.call_count == 1
    assert build_data_quality_warning_item.call_count == 1
    add_data_quality_warning.assert_called_with(
        item=get_data_source_by_id.return_value,
        warning=build_data_quality_warning_item.return_value,
    )


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)  # type: ignore

    response = resource.get_or_fetch_workspace_data()

    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert response.data_sources_by_id.__len__() == 3
    assert (
        response.data_sources_by_id.get("0f5660c7-2b05-4ff0-90ce-3199226956c6").properties.get(  # type: ignore
            "name"
        )
        == "Superstore Datasource"
    )
    assert (
        response.data_sources_by_id.get("1f5660c7-3b05-5ff0-90ce-4199226956c6").properties.get(  # type: ignore
            "name"
        )
        == "Embedded Superstore Datasource"
    )


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_workbook_selector_by_id(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data filters workbooks by ID when selector is provided."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)  # type: ignore

    # Import after resource is created to avoid import errors
    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a workbook selector that matches the test workbook ID
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == workbook_id

    response = resource.fetch_tableau_workspace_data(workbook_selector_fn=workbook_selector)

    # Verify that workbooks were filtered
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1  # Should only fetch the matching workbook
    assert len(response.workbooks_by_id) == 1
    assert workbook_id in response.workbooks_by_id


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_workbook_selector_excludes_non_matching_workbooks(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data excludes non-matching workbooks."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)  # type: ignore

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a workbook selector that never matches
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == "non-existent-workbook-id"

    response = resource.fetch_tableau_workspace_data(workbook_selector_fn=workbook_selector)

    # Verify that no workbooks were fetched
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 0  # Should not fetch any workbooks
    assert len(response.workbooks_by_id) == 0
    assert len(response.sheets_by_id) == 0
    assert len(response.dashboards_by_id) == 0
