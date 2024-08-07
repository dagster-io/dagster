import uuid

from dagster._core.definitions.asset_key import AssetKey
from dagster_powerbi import PowerBIWorkspace


def test_fetch_powerbi_workspace_data(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        api_token=fake_token,
        workspace_id=workspace_id,
    )

    actual_workspace_data = resource.fetch_powerbi_workspace_data()
    assert len(actual_workspace_data.dashboards_by_id) == 1
    assert len(actual_workspace_data.reports_by_id) == 1
    assert len(actual_workspace_data.semantic_models_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 2


def test_translator_dashboard_spec(workspace_data_api_mocks: None, workspace_id: str) -> None:
    fake_token = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        api_token=fake_token,
        workspace_id=workspace_id,
    )
    all_asset_specs = resource.build_asset_specs()

    # 1 dashboard, 1 report, 1 semantic model, 2 data sources
    assert len(all_asset_specs) == 5

    # Sanity check outputs, translator tests cover details here
    dashboard_spec = next(spec for spec in all_asset_specs if spec.key.path[0] == "dashboard")
    assert dashboard_spec.key.path == ["dashboard", "Sales_Returns_Sample_v201912"]

    report_spec = next(spec for spec in all_asset_specs if spec.key.path[0] == "report")
    assert report_spec.key.path == ["report", "Sales_Returns_Sample_v201912"]

    semantic_model_spec = next(
        spec for spec in all_asset_specs if spec.key.path[0] == "semantic_model"
    )
    assert semantic_model_spec.key.path == ["semantic_model", "Sales_Returns_Sample_v201912"]

    data_source_specs = [
        spec
        for spec in all_asset_specs
        if spec.key.path[0] not in ("dashboard", "report", "semantic_model")
    ]
    assert len(data_source_specs) == 2

    data_source_keys = {spec.key for spec in data_source_specs}
    assert data_source_keys == {
        AssetKey(["data_27_09_2019.xlsx"]),
        AssetKey(["sales_marketing_datas.xlsx"]),
    }
