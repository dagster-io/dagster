from typing import Iterator

import pytest
import responses
from dagster_powerbi.resource import BASE_API_URL, generate_data_source_id
from dagster_powerbi.translator import PowerBIContentData, PowerBIContentType, PowerBIWorkspaceData

SAMPLE_DASH = {
    "id": "efee0b80-4511-42e1-8ee0-2544fd44e122",
    "displayName": "Sales & Returns Sample v201912.pbix",
    "isReadOnly": False,
    "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/dashboards/efee0b80-4511-42e1-8ee0-2544fd44e122",
    "embedUrl": "https://app.powerbi.com/dashboardEmbed?dashboardId=efee0b80-4511-42e1-8ee0-2544fd44e122&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6e319",
    "users": [],
    "subscriptions": [],
}

SAMPLE_DASH_TILES = [
    {
        "id": "726c94ff-c408-4f43-8edf-61fbfa1753c7",
        "title": "Sales & Returns Sample v201912.pbix",
        "embedUrl": "https://app.powerbi.com/embed?dashboardId=efee0b80-4511-42e1-8ee0-2544fd44e122&tileId=726c94ff-c408-4f43-8edf-61fbfa1753c7&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6e319",
        "rowSpan": 0,
        "colSpan": 0,
        "reportId": "8b7f815d-4e64-40dd-993c-cfa4fb12edee",
        "datasetId": "8e9c85a1-7b33-4223-9590-76bde70f9a20",
    }
]

SAMPLE_REPORT = {
    "id": "8b7f815d-4e64-40dd-993c-cfa4fb12edee",
    "reportType": "PowerBIReport",
    "name": "Sales & Returns Sample v201912",
    "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/reports/8b7f815d-4e64-40dd-993c-cfa4fb12edee",
    "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=8b7f815d-4e64-40dd-993c-cfa4fb12edee&groupId=a2122b8f-d7e1-42e8-be2b-a5e636ca3221&w=2&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
    "isFromPbix": True,
    "isOwnedByMe": True,
    "datasetId": "8e9c85a1-7b33-4223-9590-76bde70f9a20",
    "datasetWorkspaceId": "a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
    "users": [],
    "subscriptions": [],
}

SAMPLE_SEMANTIC_MODEL = {
    "id": "8e9c85a1-7b33-4223-9590-76bde70f9a20",
    "name": "Sales & Returns Sample v201912",
    "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/datasets/8e9c85a1-7b33-4223-9590-76bde70f9a20",
    "addRowsAPIEnabled": False,
    "configuredBy": "ben@elementl.com",
    "isRefreshable": True,
    "isEffectiveIdentityRequired": False,
    "isEffectiveIdentityRolesRequired": False,
    "isOnPremGatewayRequired": True,
    "targetStorageMode": "Abf",
    "createdDate": "2024-07-23T23:44:55.707Z",
    "createReportEmbedURL": "https://app.powerbi.com/reportEmbed?config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
    "qnaEmbedURL": "https://app.powerbi.com/qnaEmbed?config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
    "upstreamDatasets": [],
    "users": [],
    "queryScaleOutSettings": {"autoSyncReadOnlyReplicas": True, "maxReadOnlyReplicas": 0},
}


OTHER_SAMPLE_SEMANTIC_MODEL = {
    "id": "ae9c85a1-7b33-4223-9590-76bde70f9a20",
    "name": "Second Workspace Sample",
    "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/datasets/8e9c85a1-7b33-4223-9590-76bde70f9a20",
    "addRowsAPIEnabled": False,
    "configuredBy": "ben@elementl.com",
    "isRefreshable": True,
    "isEffectiveIdentityRequired": False,
    "isEffectiveIdentityRolesRequired": False,
    "isOnPremGatewayRequired": True,
    "targetStorageMode": "Abf",
    "createdDate": "2024-07-23T23:44:55.707Z",
    "createReportEmbedURL": "https://app.powerbi.com/reportEmbed?config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
    "qnaEmbedURL": "https://app.powerbi.com/qnaEmbed?config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
    "upstreamDatasets": [],
    "users": [],
    "queryScaleOutSettings": {"autoSyncReadOnlyReplicas": True, "maxReadOnlyReplicas": 0},
}


SAMPLE_DATA_SOURCES = [
    {
        "datasourceType": "File",
        "connectionDetails": {"path": "c:\\users\\mimyersm\\dropbox\\data-27-09-2019.xlsx"},
        "datasourceId": "ee219ffe-9d50-4029-9c61-b94b3f029044",
        "gatewayId": "40800873-8e0d-4152-86e3-e6edeb2a738c",
    },
    {
        "datasourceType": "File",
        "connectionDetails": {"path": "c:\\users\\mimyersm\\desktop\\sales & marketing datas.xlsx"},
        "gatewayId": "40800873-8e0d-4152-86e3-e6edeb2a738c",
    },
]


@pytest.fixture(name="workspace_id")
def workspace_id_fixture() -> str:
    return "a2122b8f-d7e1-42e8-be2b-a5e636ca3221"


@pytest.fixture(name="second_workspace_id")
def second_workspace_id_fixture() -> str:
    return "c5322b8a-d7e1-42e8-be2b-a5e636ca3221"


@pytest.fixture(
    name="workspace_data",
)
def workspace_data_fixture(workspace_id: str) -> PowerBIWorkspaceData:
    sample_dash = SAMPLE_DASH.copy()
    # Response from tiles API, which we add to the dashboard data
    sample_dash["tiles"] = SAMPLE_DASH_TILES

    sample_semantic_model = SAMPLE_SEMANTIC_MODEL.copy()

    sample_data_sources = SAMPLE_DATA_SOURCES
    data_sources = [
        ds if "datasourceId" in ds else {"datasourceId": generate_data_source_id(ds), **ds}
        for ds in sample_data_sources
    ]
    sample_semantic_model["sources"] = [ds["datasourceId"] for ds in data_sources]

    return PowerBIWorkspaceData(
        workspace_id=workspace_id,
        dashboards_by_id={
            sample_dash["id"]: PowerBIContentData(
                content_type=PowerBIContentType.DASHBOARD, properties=sample_dash
            )
        },
        reports_by_id={
            SAMPLE_REPORT["id"]: PowerBIContentData(
                content_type=PowerBIContentType.REPORT, properties=SAMPLE_REPORT
            )
        },
        semantic_models_by_id={
            sample_semantic_model["id"]: PowerBIContentData(
                content_type=PowerBIContentType.SEMANTIC_MODEL, properties=sample_semantic_model
            )
        },
        data_sources_by_id={
            ds["datasourceId"]: PowerBIContentData(
                content_type=PowerBIContentType.DATA_SOURCE, properties=ds
            )
            for ds in data_sources
        },
    )


@pytest.fixture(
    name="workspace_data_api_mocks",
)
def workspace_data_api_mocks_fixture(workspace_id: str) -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as response:
        response.add(
            method=responses.GET,
            url=f"{BASE_API_URL}/groups/{workspace_id}/dashboards",
            json={"value": [SAMPLE_DASH]},
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{BASE_API_URL}/groups/{workspace_id}/reports",
            json={"value": [SAMPLE_REPORT]},
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{BASE_API_URL}/groups/{workspace_id}/datasets",
            json={"value": [SAMPLE_SEMANTIC_MODEL]},
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{BASE_API_URL}/groups/{workspace_id}/dashboards/{SAMPLE_DASH['id']}/tiles",
            json={"value": SAMPLE_DASH_TILES},
            status=200,
        )

        response.add(
            method=responses.GET,
            url=f"{BASE_API_URL}/groups/{workspace_id}/datasets/{SAMPLE_SEMANTIC_MODEL['id']}/datasources",
            json={"value": SAMPLE_DATA_SOURCES},
            status=200,
        )

        yield response


@pytest.fixture(
    name="second_workspace_data_api_mocks",
)
def second_workspace_data_api_mocks_fixture(
    second_workspace_id: str, workspace_data_api_mocks: responses.RequestsMock
) -> Iterator[responses.RequestsMock]:
    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{second_workspace_id}/dashboards",
        json={"value": []},
        status=200,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{second_workspace_id}/reports",
        json={"value": []},
        status=200,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{second_workspace_id}/datasets",
        json={"value": [OTHER_SAMPLE_SEMANTIC_MODEL]},
        status=200,
    )

    workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{second_workspace_id}/datasets/{OTHER_SAMPLE_SEMANTIC_MODEL['id']}/datasources",
        json={"value": []},
        status=200,
    )

    yield workspace_data_api_mocks
