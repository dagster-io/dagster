import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster_powerbi import DagsterPowerBITranslator
from dagster_powerbi.translator import PowerBIContentData, PowerBIContentType, PowerBIWorkspaceData


@pytest.fixture(
    name="workspace_data",
)
def workspace_data_fixture() -> PowerBIWorkspaceData:
    sample_dash = {
        "id": "efee0b80-4511-42e1-8ee0-2544fd44e122",
        "displayName": "Sales & Returns Sample v201912.pbix",
        "isReadOnly": False,
        "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/dashboards/efee0b80-4511-42e1-8ee0-2544fd44e122",
        "embedUrl": "https://app.powerbi.com/dashboardEmbed?dashboardId=efee0b80-4511-42e1-8ee0-2544fd44e122&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6e319",
        "users": [],
        "subscriptions": [],
    }
    # Response from tiles API, which we add to the dashboard data
    tiles = [
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
    sample_dash["tiles"] = tiles

    sample_report = {
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
    sample_semantic_model = {
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

    sample_data_sources = [
        {
            "datasourceType": "File",
            "connectionDetails": {"path": "c:\\users\\mimyersm\\dropbox\\data-27-09-2019.xlsx"},
            "datasourceId": "ee219ffe-9d50-4029-9c61-b94b3f029044",
            "gatewayId": "40800873-8e0d-4152-86e3-e6edeb2a738c",
        },
        {
            "datasourceType": "File",
            "connectionDetails": {
                "path": "c:\\users\\mimyersm\\desktop\\sales & marketing datas.xlsx"
            },
            "datasourceId": "46c83f90-3eaa-4658-b716-2307bc56e74d",
            "gatewayId": "40800873-8e0d-4152-86e3-e6edeb2a738c",
        },
    ]
    sample_semantic_model["sources"] = [ds["datasourceId"] for ds in sample_data_sources]

    return PowerBIWorkspaceData(
        dashboards_by_id={
            sample_dash["id"]: PowerBIContentData(
                content_type=PowerBIContentType.DASHBOARD, properties=sample_dash
            )
        },
        reports_by_id={
            sample_report["id"]: PowerBIContentData(
                content_type=PowerBIContentType.REPORT, properties=sample_report
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
            for ds in sample_data_sources
        },
    )


def test_translator_dashboard_spec(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_dashboard_spec(dashboard)

    assert asset_spec.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]
    assert asset_spec.tags == {"dagster/storage_kind": "powerbi"}
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["report", "Sales_Returns_Sample_v201912"])


def test_translator_report_spec(workspace_data: PowerBIWorkspaceData) -> None:
    report = next(iter(workspace_data.reports_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_report_spec(report)

    assert asset_spec.key.path == ["report", "Sales_Returns_Sample_v201912"]
    assert asset_spec.tags == {"dagster/storage_kind": "powerbi"}
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])


def test_translator_semantic_model(workspace_data: PowerBIWorkspaceData) -> None:
    semantic_model = next(iter(workspace_data.semantic_models_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_semantic_model_spec(semantic_model)

    assert asset_spec.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]
    assert asset_spec.tags == {"dagster/storage_kind": "powerbi"}
    deps = list(asset_spec.deps)
    assert len(deps) == 2
    assert deps[0].asset_key == AssetKey(["data_27_09_2019.xlsx"])
    assert deps[1].asset_key == AssetKey(["sales_marketing_datas.xlsx"])


class MyCustomTranslator(DagsterPowerBITranslator):
    def get_dashboard_spec(self, dashboard: PowerBIContentData) -> AssetSpec:
        return super().get_dashboard_spec(dashboard)._replace(metadata={"custom": "metadata"})


def test_translator_custom_metadata(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = MyCustomTranslator(workspace_data)
    asset_spec = translator.get_dashboard_spec(dashboard)

    assert asset_spec.metadata == {"custom": "metadata"}
    assert asset_spec.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]
    assert asset_spec.tags == {"dagster/storage_kind": "powerbi"}
