from unittest.mock import MagicMock

import pytest
from dagster_shared.check.functions import ParameterCheckError
from dagster_tableau.asset_utils import parse_tableau_external_and_materializable_asset_specs
from dagster_tableau.assets import build_tableau_materializable_assets_definition
from dagster_tableau.resources import TableauCloudWorkspace, load_tableau_asset_specs

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


def test_tableau_assets_refreshable_ids_invalid(
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
    get_view: MagicMock,
    get_job: MagicMock,
    refresh_workbook: MagicMock,
    cancel_job: MagicMock,
    workbook_id: str,
    data_source_id: str,
) -> None:
    tableau_specs = load_tableau_asset_specs(
        workspace=resource,
    )

    external_asset_specs, materializable_asset_specs = (
        parse_tableau_external_and_materializable_asset_specs(tableau_specs)
    )

    resource_key = "tableau"

    with pytest.raises(ParameterCheckError):
        build_tableau_materializable_assets_definition(
            resource_key=resource_key,
            specs=materializable_asset_specs,
            refreshable_workbook_ids=[workbook_id],
            refreshable_data_source_ids=[data_source_id],
        )
