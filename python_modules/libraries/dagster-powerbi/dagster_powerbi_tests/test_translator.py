from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.tags import build_kind_tag
from dagster_powerbi import DagsterPowerBITranslator
from dagster_powerbi.translator import (
    PowerBIContentData,
    PowerBIContentType,
    PowerBITranslatorData,
    PowerBIWorkspaceData,
)


def test_translator_dashboard_spec(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = DagsterPowerBITranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=dashboard,
            workspace_data=workspace_data,
        )
    )

    assert asset_spec.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["report", "Sales_Returns_Sample_v201912"])
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/dashboards/efee0b80-4511-42e1-8ee0-2544fd44e122"
        )
    }
    assert asset_spec.tags == {
        "dagster-powerbi/asset_type": "dashboard",
        **build_kind_tag("powerbi"),
        **build_kind_tag("dashboard"),
    }


def test_translator_report_spec(workspace_data: PowerBIWorkspaceData) -> None:
    report = next(iter(workspace_data.reports_by_id.values()))

    translator = DagsterPowerBITranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=report,
            workspace_data=workspace_data,
        )
    )

    assert asset_spec.key.path == ["report", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/reports/8b7f815d-4e64-40dd-993c-cfa4fb12edee"
        )
    }
    assert asset_spec.tags == {
        "dagster-powerbi/asset_type": "report",
        **build_kind_tag("powerbi"),
        **build_kind_tag("report"),
    }
    assert asset_spec.owners == ["ben@dagsterlabs.com"]


def test_translator_semantic_model(workspace_data: PowerBIWorkspaceData) -> None:
    semantic_model = next(iter(workspace_data.semantic_models_by_id.values()))

    translator = DagsterPowerBITranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=semantic_model,
            workspace_data=workspace_data,
        )
    )

    assert asset_spec.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 2
    assert deps[0].asset_key == AssetKey(["data_27_09_2019_xlsx"])
    assert deps[1].asset_key == AssetKey(["sales_marketing_datas_xlsx"])
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/datasets/8e9c85a1-7b33-4223-9590-76bde70f9a20"
        ),
        "dagster-powerbi/id": "8e9c85a1-7b33-4223-9590-76bde70f9a20",
        "dagster/table_name": "sales",
        "dagster/column_schema": TableSchema(
            columns=[
                TableColumn(name="order_id", type="Int64"),
                TableColumn(name="product_id", type="Int64"),
                TableColumn(name="quantity", type="Int64"),
                TableColumn(name="price", type="Decimal"),
                TableColumn(name="order_date", type="DateTime"),
            ]
        ),
    }
    assert asset_spec.tags == {
        "dagster-powerbi/asset_type": "semantic_model",
        **build_kind_tag("powerbi"),
        **build_kind_tag("semantic model"),
    }
    assert asset_spec.owners == ["chris@dagsterlabs.com"]


def test_translator_semantic_model_many_tables(second_workspace_data: PowerBIWorkspaceData) -> None:
    semantic_model = next(iter(second_workspace_data.semantic_models_by_id.values()))

    translator = DagsterPowerBITranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=semantic_model,
            workspace_data=second_workspace_data,
        )
    )
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/datasets/8e9c85a1-7b33-4223-9590-76bde70f9a20"
        ),
        "dagster-powerbi/id": "ae9c85a1-7b33-4223-9590-76bde70f9a20",
        "sales_column_schema": TableSchema(
            columns=[
                TableColumn(name="order_id", type="Int64"),
                TableColumn(name="product_id", type="Int64"),
                TableColumn(name="quantity", type="Int64"),
                TableColumn(name="price", type="Decimal"),
                TableColumn(name="order_date", type="DateTime"),
            ]
        ),
        "customers_column_schema": TableSchema(
            columns=[
                TableColumn(name="customer_id", type="Int64"),
                TableColumn(name="customer_name", type="String"),
                TableColumn(name="customer_email", type="String"),
            ]
        ),
    }


class MyCustomTranslator(DagsterPowerBITranslator):
    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
        ).merge_attributes(metadata={"custom": "metadata"})


def test_translator_custom_metadata(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = MyCustomTranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=dashboard,
            workspace_data=workspace_data,
        )
    )

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["prefix", "dashboard", "Sales_Returns_Sample_v201912"]


def test_translator_report_spec_no_dataset(workspace_data: PowerBIWorkspaceData) -> None:
    report_no_dataset = PowerBIContentData(
        content_type=PowerBIContentType.REPORT,
        properties={
            "id": "8b7f815d-4e64-40dd-993c-cfa4fb12edee",
            "reportType": "PowerBIReport",
            "name": "Sales & Returns Sample v201912",
            "webUrl": "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/reports/8b7f815d-4e64-40dd-993c-cfa4fb12edee",
            "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=8b7f815d-4e64-40dd-993c-cfa4fb12edee&groupId=a2122b8f-d7e1-42e8-be2b-a5e636ca3221&w=2&config=eyJjbHVzdGVyVXJsIjoiaHR0cHM6Ly9XQUJJLVdFU1QtVVMtRS1QUklNQVJZLXJlZGlyZWN0LmFuYWx5c2lzLndpbmRvd3MubmV0IiwiZW1iZWRGZWF0dXJlcyI6eyJ1c2FnZU1ldHJpY3NWTmV4dCI6dHJ1ZX19",
            "isFromPbix": True,
            "isOwnedByMe": True,
            "users": [],
            "subscriptions": [],
            "createdBy": "ben@dagsterlabs.com",
        },
    )

    translator = DagsterPowerBITranslator()
    asset_spec = translator.get_asset_spec(
        PowerBITranslatorData(
            content_data=report_no_dataset,
            workspace_data=workspace_data,
        )
    )

    assert asset_spec.key.path == ["report", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 0
