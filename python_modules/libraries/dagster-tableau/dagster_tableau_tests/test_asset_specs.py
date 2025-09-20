import uuid
from typing import Union
from unittest.mock import MagicMock

import pytest
import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_shared.check import CheckError
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace, load_tableau_asset_specs
from dagster_tableau.asset_utils import parse_tableau_external_and_materializable_asset_specs
from dagster_tableau.translator import DagsterTableauTranslator, TableauTranslatorData

from dagster_tableau_tests.conftest import (
    TEST_DATA_SOURCE_ID,
    TEST_EMBEDDED_DATA_SOURCE_ID,
    TEST_PROJECT_ID,
    TEST_PROJECT_NAME,
    TEST_WORKBOOK_ID,
)


@responses.activate
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
    resource.build_client()

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    assert len(actual_workspace_data.workbooks_by_id) == 1
    assert len(actual_workspace_data.sheets_by_id) == 2
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 3


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_invalid_workbook(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
    workbook_id: str,
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
    resource.build_client()

    # Test invalid workbook
    get_workbook.return_value = {"data": {"workbooks": None}}
    with pytest.raises(
        CheckError, match=f"Invalid data for Tableau workbook for id {workbook_id}."
    ):
        resource.get_or_fetch_workspace_data()

    # Test empty workbook
    get_workbook.return_value = {"data": {"workbooks": []}}
    with pytest.raises(
        Exception, match=f"Could not retrieve data for Tableau workbook for id {workbook_id}."
    ):
        resource.get_or_fetch_workspace_data()


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("sign_in")
@pytest.mark.usefixtures("get_workbooks")
@pytest.mark.usefixtures("get_workbook")
def test_translator_spec(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    with environ({"TABLEAU_CLIENT_ID": connected_app_client_id}):
        resource_args = {
            "connected_app_client_id": EnvVar("TABLEAU_CLIENT_ID"),
            "connected_app_secret_id": connected_app_secret_id,
            "connected_app_secret_value": connected_app_secret_value,
            "username": username,
            "site_name": site_name,
            host_key: host_value,
        }

        resource = clazz(**resource_args)
        resource.build_client()

        all_assets = load_tableau_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 2 sheet, 1 dashboard and 3 data source as external assets
        assert len(all_assets) == 6
        assert len(all_assets_keys) == 6

        # Sanity check outputs, translator tests cover details here
        sheet_asset_spec = next(
            spec
            for spec in all_assets
            if "workbook" in spec.key.path[0] and "sheet" in spec.key.path[1]
        )
        assert sheet_asset_spec.key.path == ["test_workbook", "sheet", "sales"]

        dashboard_asset_spec = next(
            spec
            for spec in all_assets
            if "workbook" in spec.key.path[0] and "dashboard" in spec.key.path[1]
        )
        assert dashboard_asset_spec.key.path == ["test_workbook", "dashboard", "dashboard_sales"]
        asset_deps_iter = iter(dashboard_asset_spec.deps)
        assert next(asset_deps_iter).asset_key.path == [
            "test_workbook",
            "sheet",
            "sales",
        ]
        assert next(asset_deps_iter).asset_key.path == ["hidden_sheet_datasource"]

        iter_data_source = iter(spec for spec in all_assets if "datasource" in spec.key.path[0])
        published_data_source_asset_spec = next(iter_data_source)
        assert published_data_source_asset_spec.key.path == ["superstore_datasource"]
        assert published_data_source_asset_spec.metadata == {
            "dagster-tableau/id": TEST_DATA_SOURCE_ID,
            "dagster-tableau/has_extracts": False,
            "dagster-tableau/is_published": True,
        }

        embedded_data_source_asset_spec = next(iter_data_source)
        assert embedded_data_source_asset_spec.key.path == ["embedded_superstore_datasource"]
        assert embedded_data_source_asset_spec.metadata == {
            "dagster-tableau/id": TEST_EMBEDDED_DATA_SOURCE_ID,
            "dagster-tableau/has_extracts": True,
            "dagster-tableau/is_published": False,
            "dagster-tableau/workbook_id": TEST_WORKBOOK_ID,
        }


class MyCustomTranslator(DagsterTableauTranslator):
    def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
        ).merge_attributes(metadata={"custom": "metadata"})


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("sign_in")
@pytest.mark.usefixtures("get_workbooks")
@pytest.mark.usefixtures("get_workbook")
def test_translator_custom_metadata(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    with environ({"TABLEAU_CLIENT_ID": connected_app_client_id}):
        resource_args = {
            "connected_app_client_id": EnvVar("TABLEAU_CLIENT_ID"),
            "connected_app_secret_id": connected_app_secret_id,
            "connected_app_secret_value": connected_app_secret_value,
            "username": username,
            "site_name": site_name,
            host_key: host_value,
        }

        resource = clazz(**resource_args)
        resource.build_client()

        all_asset_specs = load_tableau_asset_specs(
            workspace=resource, dagster_tableau_translator=MyCustomTranslator()
        )
        asset_spec = next(spec for spec in all_asset_specs)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == ["prefix", "superstore_datasource"]
        assert asset_spec.tags["dagster/storage_kind"] == "tableau"
        assert asset_spec.kinds == {"tableau","live","published datasource"}


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (
            TableauServerWorkspace,
            "server_name",
            "fake_server_name",
        ),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("sign_in")
@pytest.mark.usefixtures("get_workbooks")
@pytest.mark.usefixtures("get_workbook")
def test_parse_asset_specs(
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    with environ({"TABLEAU_CLIENT_ID": connected_app_client_id}):
        resource_args = {
            "connected_app_client_id": EnvVar("TABLEAU_CLIENT_ID"),
            "connected_app_secret_id": connected_app_secret_id,
            "connected_app_secret_value": connected_app_secret_value,
            "username": username,
            "site_name": site_name,
            host_key: host_value,
        }

        resource = clazz(**resource_args)
        resource.build_client()

        all_assets = load_tableau_asset_specs(resource)

        # Data source with extracts are considered as external assets
        external_asset_specs, materializable_asset_specs = (
            parse_tableau_external_and_materializable_asset_specs(
                specs=all_assets, include_data_sources_with_extracts=False
            )
        )
        assert len(external_asset_specs) == 3
        assert len(materializable_asset_specs) == 3

        # Data source with extracts are considered as materializable assets
        external_asset_specs, materializable_asset_specs = (
            parse_tableau_external_and_materializable_asset_specs(
                specs=all_assets, include_data_sources_with_extracts=True
            )
        )
        assert len(external_asset_specs) == 2
        assert len(materializable_asset_specs) == 4


@responses.activate
@pytest.mark.parametrize(
    "attribute, value, expected_result_before_selection, expected_result_after_selection",
    [
        (None, None, 1, 1),
        ("id", TEST_WORKBOOK_ID, 1, 1),
        ("project_name", TEST_PROJECT_NAME, 1, 1),
        ("project_id", TEST_PROJECT_ID, 1, 1),
        ("id", "non_matching_workbook_id", 1, 0),
        ("project_name", "non_matching_project_name", 1, 0),
        ("project_id", "non_matching_project_id", 1, 0),
    ],
    ids=[
        "no_selector_present_workbook",
        "workbook_id_selector_present_workbook",
        "project_name_selector_present_workbook",
        "project_id_selector_present_workbook",
        "workbook_id_selector_absent_workbook",
        "project_name_selector_absent_workbook",
        "project_id_selector_absent_workbook",
    ],
)
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("sign_in")
@pytest.mark.usefixtures("get_workbooks")
@pytest.mark.usefixtures("get_workbook")
def test_tableau_workbook_selector(
    attribute: str,
    value: str,
    expected_result_before_selection: int,
    expected_result_after_selection: int,
    clazz: Union[type[TableauCloudWorkspace], type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
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
    resource.build_client()

    workbook_selector_fn = (
        (lambda workbook: getattr(workbook, attribute) == value) if attribute else None
    )

    workspace_data = resource.get_or_fetch_workspace_data()
    assert len(workspace_data.workbooks_by_id) == expected_result_before_selection

    workspace_data_selection = workspace_data.to_workspace_data_selection(
        workbook_selector_fn=workbook_selector_fn
    )
    assert len(workspace_data_selection.workbooks_by_id) == expected_result_after_selection
