import pytest
from dagster_tableau.translator import TableauContentData, TableauContentType, TableauWorkspaceData

SAMPLE_WORKBOOK = {
    "location": {
        "id": "7239fbb5-f0a3-426f-b9c0-05f829c6cd64",
    },
    "owner": {
        "id": "2a59b27f-a842-4c7a-a6ed-8c9f814e6119",
    },
    "views": {
        "view": [
            {
                "id": "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f",
            },
        ]
    },
    "connections": {
        "connection": [
            {
                "datasource": {
                    "id": "a15ca565-fb62-4a95-bc71-2a7667f9a3ef",
                },
                "id": "436cb989-74fb-47d4-a209-edd5510d1239",
                "type": "sqlproxy",
                "embedPassword": False,
                "serverAddress": "localhost",
                "serverPort": "8080",
                "userName": "",
                "queryTaggingEnabled": False,
            }
        ]
    },
    "id": "b75fc023-a7ca-4115-857b-4342028640d0",
    "name": "Test Workbook",
    "contentUrl": "TestWorkbook",
    "webpageUrl": "https://prod-ca-a.online.tableau.com/#/site/info-5a38291c26/workbooks/690496",
    "createdAt": "2024-09-05T21:33:26Z",
    "updatedAt": "2024-09-06T14:38:42Z",
}


SAMPLE_VIEW = {
    "id": "ae8a5f27-8b2f-44e9-aec3-94fe6c638f4f",
    "name": "Sales",
    "contentUrl": "TestWorkbook/sheets/Sales",
    "createdAt": "2024-09-05T21:33:26Z",
    "updatedAt": "2024-09-06T14:38:42Z",
    "viewUrlName": "Sales",
    "workbook": {"id": "b75fc023-a7ca-4115-857b-4342028640d0"},
}


SAMPLE_DATA_SOURCE = {
    "id": "a15ca565-fb62-4a95-bc71-2a7667f9a3ef",
    "name": "Superstore Datasource",
}


@pytest.fixture(name="site_id")
def site_id_fixture() -> str:
    return "68245b5e-41fc-4517-aeec-8a96a0d878d4"


@pytest.fixture(
    name="workspace_data",
)
def workspace_data_fixture(site_id: str) -> TableauWorkspaceData:
    return TableauWorkspaceData(
        site_id=site_id,
        workbooks_by_id={
            SAMPLE_WORKBOOK["id"]: TableauContentData(
                content_type=TableauContentType.WORKBOOK, properties=SAMPLE_WORKBOOK
            )
        },
        views_by_id={
            SAMPLE_VIEW["id"]: TableauContentData(
                content_type=TableauContentType.VIEW, properties=SAMPLE_VIEW
            )
        },
        data_sources_by_id={
            SAMPLE_DATA_SOURCE["id"]: TableauContentData(
                content_type=TableauContentType.DATA_SOURCE, properties=SAMPLE_DATA_SOURCE
            )
        },
    )
