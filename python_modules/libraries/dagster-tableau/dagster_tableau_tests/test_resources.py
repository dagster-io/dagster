import uuid
from typing import Type, Union
from unittest.mock import MagicMock

import pytest
from dagster import asset, instance_for_test, materialize
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_basic_resource_request(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
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
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
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
