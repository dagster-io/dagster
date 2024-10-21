from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.tags import build_kind_tag
from dagster_powerbi import DagsterPowerBITranslator
from dagster_powerbi.translator import PowerBIContentData, PowerBIWorkspaceData


def test_translator_dashboard_spec(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_asset_spec(dashboard)

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
    }


def test_translator_report_spec(workspace_data: PowerBIWorkspaceData) -> None:
    report = next(iter(workspace_data.reports_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_asset_spec(report)

    assert asset_spec.key.path == ["report", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["semantic_model", "Sales_Returns_Sample_v201912"])
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/reports/8b7f815d-4e64-40dd-993c-cfa4fb12edee"
        )
    }
    assert asset_spec.tags == {"dagster-powerbi/asset_type": "report", **build_kind_tag("powerbi")}


def test_translator_semantic_model(workspace_data: PowerBIWorkspaceData) -> None:
    semantic_model = next(iter(workspace_data.semantic_models_by_id.values()))

    translator = DagsterPowerBITranslator(workspace_data)
    asset_spec = translator.get_asset_spec(semantic_model)

    assert asset_spec.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]
    deps = list(asset_spec.deps)
    assert len(deps) == 2
    assert deps[0].asset_key == AssetKey(["data_27_09_2019_xlsx"])
    assert deps[1].asset_key == AssetKey(["sales_marketing_datas_xlsx"])
    assert asset_spec.metadata == {
        "dagster-powerbi/web_url": MetadataValue.url(
            "https://app.powerbi.com/groups/a2122b8f-d7e1-42e8-be2b-a5e636ca3221/datasets/8e9c85a1-7b33-4223-9590-76bde70f9a20"
        )
    }
    assert asset_spec.tags == {
        "dagster-powerbi/asset_type": "semantic_model",
        **build_kind_tag("powerbi"),
    }


class MyCustomTranslator(DagsterPowerBITranslator):
    def get_dashboard_spec(self, dashboard: PowerBIContentData) -> AssetSpec:
        return super().get_dashboard_spec(dashboard)._replace(metadata={"custom": "metadata"})


def test_translator_custom_metadata(workspace_data: PowerBIWorkspaceData) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = MyCustomTranslator(workspace_data)
    asset_spec = translator.get_asset_spec(dashboard)

    assert asset_spec.metadata == {"custom": "metadata"}
    assert asset_spec.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]
