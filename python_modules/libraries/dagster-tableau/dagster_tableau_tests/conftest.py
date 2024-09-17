import contextlib
import uuid
from typing import Callable, Iterator, Union

import pytest
import responses
from dagster_tableau.resources import TableauCloudClient, TableauServerClient
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

SAMPLE_VIEW = {
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

SAMPLE_WORKBOOK = {
    "luid": "b75fc023-a7ca-4115-857b-4342028640d0",
    "name": "Test Workbook",
    "createdAt": "2024-09-05T21:33:26Z",
    "updatedAt": "2024-09-13T00:15:27Z",
    "uri": "sites/49445/workbooks/690496",
    "sheets": [
        {
            **SAMPLE_VIEW,
        }
    ],
}

SAMPLE_WORKBOOKS = {"workbooks": {"workbook": [{"id": "b75fc023-a7ca-4115-857b-4342028640d0"}]}}


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
        views_by_id={
            SAMPLE_VIEW["luid"]: TableauContentData(
                content_type=TableauContentType.VIEW, properties=SAMPLE_VIEW
            )
        },
        data_sources_by_id={
            SAMPLE_DATA_SOURCE["luid"]: TableauContentData(
                content_type=TableauContentType.DATA_SOURCE, properties=SAMPLE_DATA_SOURCE
            )
        },
    )


@pytest.fixture(
    name="workspace_data_api_mocks_fn",
)
def workspace_data_api_mocks_fn_fixture(site_id: str, api_token: str) -> Callable:
    @contextlib.contextmanager
    def _method(
        client: Union[TableauCloudClient, TableauServerClient],
        site_id: str = site_id,
        api_token: str = api_token,
    ) -> Iterator[responses.RequestsMock]:
        with responses.RequestsMock() as response:
            response.add(
                method=responses.POST,
                url=f"{client.rest_api_base_url}/auth/signin",
                json={"credentials": {"site": {"id": site_id}, "token": api_token}},
                status=200,
            )
            response.add(
                method=responses.GET,
                url=f"{client.rest_api_base_url}/sites/{site_id}/workbooks",
                json=SAMPLE_WORKBOOKS,
                status=200,
            )
            response.add(
                method=responses.POST,
                url=f"{client.metadata_api_base_url}",
                json={"data": {"workbooks": [SAMPLE_WORKBOOK]}},
                status=200,
            )
            response.add(
                method=responses.POST,
                url=f"{client.rest_api_base_url}/auth/signout",
                status=200,
            )

            yield response

    return _method
