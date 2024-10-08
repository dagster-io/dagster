# ruff: noqa: SLF001

import uuid
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from dagster_tableau.translator import TableauContentData, TableauContentType, TableauWorkspaceData

FAKE_CONNECTED_APP_CLIENT_ID = uuid.uuid4().hex
FAKE_CONNECTED_APP_SECRET_ID = uuid.uuid4().hex
FAKE_CONNECTED_APP_SECRET_VALUE = uuid.uuid4().hex
FAKE_USERNAME = "fake_username"
FAKE_SITE_NAME = "fake_site_name"
FAKE_POD_NAME = "fake_pod_name"


SAMPLE_DATA_SOURCE = {
    "luid": "0f5660c7-2b05-4ff0-90ce-3199226956c6",
    "name": "Superstore Datasource",
}

SAMPLE_SHEET = {
    "luid": "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f",
    "name": "Sales",
    "createdAt": "2024-09-05T21:33:26Z",
    "updatedAt": "2024-09-13T00:15:23Z",
    "path": "TestWorkbook/Sales",
    "parentEmbeddedDatasources": [
        {
            "parentPublishedDatasources": [
                {
                    **SAMPLE_DATA_SOURCE,
                }
            ]
        }
    ],
    "workbook": {"luid": "b75fc023-a7ca-4115-857b-4342028640d0"},
}

SAMPLE_DASHBOARD = {
    "luid": "c9bf8403-5daf-427a-b3d6-2ce9bed7798f",
    "name": "Dashboard_Sales",
    "createdAt": "2024-09-06T14:38:42Z",
    "updatedAt": "2024-09-13T00:15:23Z",
    "path": "TestWorkbook/Dashboard_Sales",
    "sheets": [{"luid": "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f"}],
    "workbook": {"luid": "b75fc023-a7ca-4115-857b-4342028640d0"},
}


SAMPLE_WORKBOOK = {
    "luid": "b75fc023-a7ca-4115-857b-4342028640d0",
    "name": "Test Workbook",
    "createdAt": "2024-09-05T21:33:26Z",
    "updatedAt": "2024-09-13T00:15:27Z",
    "uri": "sites/49445/workbooks/690496",
    "sheets": [
        {
            **SAMPLE_SHEET,
        }
    ],
    "dashboards": [
        {
            **SAMPLE_DASHBOARD,
        }
    ],
}

SAMPLE_WORKBOOKS = {"workbooks": {"workbook": [{"id": "b75fc023-a7ca-4115-857b-4342028640d0"}]}}

SAMPLE_VIEW_SHEET = {
    "view": {
        "workbook": {"id": "b75fc023-a7ca-4115-857b-4342028640d0"},
        "owner": {"id": "2a59b27f-a842-4c7a-a6ed-8c9f814e6119"},
        "tags": {},
        "location": {"id": "7239fbb5-f0a3-426f-b9c0-05f829c6cd64", "type": "PersonalSpace"},
        "id": "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f",
        "name": "Sales",
        "contentUrl": "TestWorkbook/sheets/Sales",
        "createdAt": "2024-09-05T21:33:26Z",
        "updatedAt": "2024-09-13T00:15:23Z",
        "viewUrlName": "Sales",
    }
}

SAMPLE_VIEW_DASHBOARD = {
    "view": {
        "workbook": {"id": "b75fc023-a7ca-4115-857b-4342028640d0"},
        "owner": {"id": "2a59b27f-a842-4c7a-a6ed-8c9f814e6119"},
        "tags": {},
        "location": {"id": "7239fbb5-f0a3-426f-b9c0-05f829c6cd64", "type": "PersonalSpace"},
        "id": "c9bf8403-5daf-427a-b3d6-2ce9bed7798f",
        "name": "Dashboard_Sales",
        "contentUrl": "TestWorkbook/sheets/Dashboard_Sales",
        "createdAt": "2024-09-06T14:38:42Z",
        "updatedAt": "2024-09-13T00:15:23Z",
        "viewUrlName": "Test_Sales",
    }
}


@pytest.fixture(name="site_name")
def site_name_fixture() -> str:
    return "info-5a38291c26"


@pytest.fixture(name="site_id")
def site_id_fixture() -> str:
    return uuid.uuid4().hex


@pytest.fixture(name="api_token")
def api_token_fixture() -> str:
    return uuid.uuid4().hex


@pytest.fixture(name="workbook_id")
def workbook_id_fixture() -> str:
    return "b75fc023-a7ca-4115-857b-4342028640d0"


@pytest.fixture(name="sheet_id")
def sheet_id_fixture() -> str:
    return "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f"


@pytest.fixture(name="dashboard_id")
def dashboard_id_fixture() -> str:
    return "c9bf8403-5daf-427a-b3d6-2ce9bed7798f"


@pytest.fixture(name="job_id")
def job_id_fixture() -> str:
    return uuid.uuid4().hex


@pytest.fixture(name="sign_in", autouse=True)
def sign_in_fixture():
    with patch("dagster_tableau.resources.BaseTableauClient.sign_in") as mocked_function:
        yield mocked_function


@pytest.fixture(name="get_workbooks", autouse=True)
def get_workbooks_fixture(build_workbook_item):
    with patch("dagster_tableau.resources.BaseTableauClient.get_workbooks") as mocked_function:
        mocked_function.return_value = [build_workbook_item()]
        yield mocked_function


@pytest.fixture(name="get_workbook", autouse=True)
def get_workbook_fixture():
    with patch("dagster_tableau.resources.BaseTableauClient.get_workbook") as mocked_function:
        mocked_function.return_value = {"data": {"workbooks": [SAMPLE_WORKBOOK]}}
        yield mocked_function


@pytest.fixture(name="get_view", autouse=True)
def get_view_fixture(build_view_item):
    with patch("dagster_tableau.resources.BaseTableauClient.get_view") as mocked_function:
        mocked_function.return_value = build_view_item()
        yield mocked_function


@pytest.fixture(name="get_job", autouse=True)
def get_job_fixture(workbook_id, job_id):
    with patch("dagster_tableau.resources.BaseTableauClient.get_job") as mocked_function:
        type(mocked_function.return_value).id = PropertyMock(return_value=job_id)
        type(mocked_function.return_value).finish_code = PropertyMock(return_value=0)
        type(mocked_function.return_value).workbook_id = PropertyMock(return_value=workbook_id)
        yield mocked_function


@pytest.fixture(name="refresh_workbook", autouse=True)
def refresh_workbook_fixture(workbook_id, job_id):
    with patch("dagster_tableau.resources.BaseTableauClient.refresh_workbook") as mocked_function:
        type(mocked_function.return_value).id = PropertyMock(return_value=job_id)
        type(mocked_function.return_value).finish_code = PropertyMock(return_value=-1)
        type(mocked_function.return_value).workbook_id = PropertyMock(return_value=workbook_id)
        yield mocked_function


@pytest.fixture(name="cancel_job", autouse=True)
def cancel_job_fixture():
    with patch("dagster_tableau.resources.BaseTableauClient.cancel_job") as mocked_function:
        yield mocked_function


@pytest.fixture(name="build_workbook_item", autouse=True)
def build_workbook_item_fixture():
    with patch("dagster_tableau.resources.TSC.WorkbookItem") as mocked_class:
        type(mocked_class.return_value).id = PropertyMock(
            return_value=SAMPLE_WORKBOOKS["workbooks"]["workbook"][0]["id"]
        )
        yield mocked_class


@pytest.fixture(name="build_view_item", autouse=True)
def build_view_item_fixture():
    with patch("dagster_tableau.resources.TSC.ViewItem") as mocked_class:
        mock_sheet = MagicMock()
        type(mock_sheet.return_value).workbook_id = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["workbook"]["id"]
        )
        type(mock_sheet.return_value).owner_id = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["owner"]["id"]
        )
        type(mock_sheet.return_value).name = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["name"]
        )
        type(mock_sheet.return_value).content_url = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["contentUrl"]
        )
        type(mock_sheet.return_value).created_at = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["createdAt"]
        )
        type(mock_sheet.return_value).updated_at = PropertyMock(
            return_value=SAMPLE_VIEW_SHEET["view"]["updatedAt"]
        )
        mock_dashboard = MagicMock()
        type(mock_dashboard.return_value).workbook_id = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["workbook"]["id"]
        )
        type(mock_dashboard.return_value).owner_id = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["owner"]["id"]
        )
        type(mock_dashboard.return_value).name = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["name"]
        )
        type(mock_dashboard.return_value).content_url = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["contentUrl"]
        )
        type(mock_dashboard.return_value).created_at = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["createdAt"]
        )
        type(mock_dashboard.return_value).updated_at = PropertyMock(
            return_value=SAMPLE_VIEW_DASHBOARD["view"]["updatedAt"]
        )
        mocked_class.side_effect = [mock_sheet, mock_dashboard]
        yield mocked_class


@pytest.fixture(name="get_data_source_by_id", autouse=True)
def get_data_source_by_id_fixture():
    with patch(
        "dagster_tableau.resources.TSC.server.endpoint.datasources_endpoint.Datasources.get_by_id"
    ) as mocked_function:
        yield mocked_function


@pytest.fixture(name="build_data_quality_warning_item", autouse=True)
def build_data_quality_warning_item_fixture():
    with patch("dagster_tableau.resources.TSC.DQWItem") as mocked_class:
        yield mocked_class


@pytest.fixture(name="add_data_quality_warning", autouse=True)
def add_data_quality_warning_fixture():
    with patch(
        "dagster_tableau.resources.TSC.server.endpoint.datasources_endpoint.Datasources.add_dqw"
    ) as mocked_function:
        yield mocked_function


@pytest.fixture(
    name="workspace_data",
)
def workspace_data_fixture(site_name: str) -> TableauWorkspaceData:
    return TableauWorkspaceData(
        site_name=site_name,
        workbooks_by_id={
            SAMPLE_WORKBOOK["luid"]: TableauContentData(
                content_type=TableauContentType.WORKBOOK, properties=SAMPLE_WORKBOOK
            )
        },
        sheets_by_id={
            SAMPLE_SHEET["luid"]: TableauContentData(
                content_type=TableauContentType.SHEET, properties=SAMPLE_SHEET
            )
        },
        dashboards_by_id={
            SAMPLE_DASHBOARD["luid"]: TableauContentData(
                content_type=TableauContentType.DASHBOARD, properties=SAMPLE_DASHBOARD
            )
        },
        data_sources_by_id={
            SAMPLE_DATA_SOURCE["luid"]: TableauContentData(
                content_type=TableauContentType.DATA_SOURCE, properties=SAMPLE_DATA_SOURCE
            )
        },
    )
