import uuid
from typing import Union
from unittest.mock import MagicMock

import pytest
import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_shared.check import CheckError
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace, load_tableau_asset_specs
from dagster_tableau.asset_utils import parse_tableau_external_and_materializable_asset_specs
from dagster_tableau.translator import DagsterTableauTranslator, TableauTranslatorData


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

    actual_workspace_data = resource.fetch_tableau_workspace_data()
    assert len(actual_workspace_data.workbooks_by_id) == 1
    assert len(actual_workspace_data.sheets_by_id) == 2
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 2


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
        resource.fetch_tableau_workspace_data()

    # Test empty workbook
    get_workbook.return_value = {"data": {"workbooks": []}}
    with pytest.raises(
        Exception, match=f"Could not retrieve data for Tableau workbook for id {workbook_id}."
    ):
        resource.fetch_tableau_workspace_data()


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

        # 2 sheet, 1 dashboard and 2 data source as external assets
        assert len(all_assets) == 5
        assert len(all_assets_keys) == 5

        # Sanity check outputs, translator tests cover details here
        sheet_asset_key = next(
            key for key in all_assets_keys if "workbook" in key.path[0] and "sheet" in key.path[1]
        )
        assert sheet_asset_key.path == ["test_workbook", "sheet", "sales"]

        dashboard_asset_key = next(
            key
            for key in all_assets_keys
            if "workbook" in key.path[0] and "dashboard" in key.path[1]
        )
        assert dashboard_asset_key.path == ["test_workbook", "dashboard", "dashboard_sales"]

        data_source_asset_key = next(key for key in all_assets_keys if "datasource" in key.path[0])
        assert data_source_asset_key.path == ["superstore_datasource"]


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
def test_translator_custom_metadata_legacy(
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

        # Pass the translator type
        with pytest.warns(
            DeprecationWarning,
            match=r"Support of `dagster_tableau_translator` as a Type\[DagsterTableauTranslator\]",
        ):
            all_asset_specs = load_tableau_asset_specs(
                workspace=resource, dagster_tableau_translator=MyCustomTranslator
            )
        asset_spec = next(spec for spec in all_asset_specs)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == ["prefix", "superstore_datasource"]
        assert asset_spec.tags["dagster/storage_kind"] == "tableau"


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
        assert len(external_asset_specs) == 2
        assert len(materializable_asset_specs) == 3

        # Data source with extracts are considered as materializable assets
        external_asset_specs, materializable_asset_specs = (
            parse_tableau_external_and_materializable_asset_specs(
                specs=all_assets, include_data_sources_with_extracts=True
            )
        )
        assert len(external_asset_specs) == 1
        assert len(materializable_asset_specs) == 4
