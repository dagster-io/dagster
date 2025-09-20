from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster_tableau import DagsterTableauTranslator
from dagster_tableau.translator import TableauTranslatorData, TableauWorkspaceData

from dagster_tableau_tests.conftest import (
    TEST_DATA_SOURCE_ID,
    TEST_EMBEDDED_DATA_SOURCE_ID,
    TEST_PROJECT_ID,
    TEST_PROJECT_NAME,
    TEST_WORKBOOK_ID,
)


def test_translator_sheet_spec(workspace_data: TableauWorkspaceData) -> None:
    translator = DagsterTableauTranslator()
    asset_key_list = ["superstore_datasource", "embedded_superstore_datasource"]
    index = 0
    for sheet in workspace_data.sheets_by_id.values():
        asset_spec = translator.get_asset_spec(
            TableauTranslatorData(content_data=sheet, workspace_data=workspace_data)
        )
        assert asset_spec.key.path == [
            "test_workbook",
            "sheet",
            sheet.properties.get("name").lower(),  # type: ignore
        ]
        assert asset_spec.metadata == {
            "dagster-tableau/id": sheet.properties.get("luid"),
            "dagster-tableau/workbook_id": TEST_WORKBOOK_ID,
            "dagster-tableau/project_name": TEST_PROJECT_NAME,
            "dagster-tableau/project_id": TEST_PROJECT_ID,
        }
        assert asset_spec.tags == {
            "dagster/storage_kind": "tableau",
            "dagster-tableau/asset_type": "sheet",
            "dagster/kind/tableau": "",
            "dagster/kind/sheet": "",
        }
        deps = list(asset_spec.deps)
        assert len(deps) == 1
        assert deps[0].asset_key == AssetKey([asset_key_list[index]])
        index += 1


def test_translator_dashboard_spec(workspace_data: TableauWorkspaceData, dashboard_id: str) -> None:
    dashboard = next(iter(workspace_data.dashboards_by_id.values()))

    translator = DagsterTableauTranslator()
    asset_spec = translator.get_asset_spec(
        TableauTranslatorData(content_data=dashboard, workspace_data=workspace_data)
    )

    assert asset_spec.key.path == ["test_workbook", "dashboard", "dashboard_sales"]
    assert asset_spec.metadata == {
        "dagster-tableau/id": dashboard_id,
        "dagster-tableau/workbook_id": TEST_WORKBOOK_ID,
        "dagster-tableau/project_name": TEST_PROJECT_NAME,
        "dagster-tableau/project_id": TEST_PROJECT_ID,
    }
    assert asset_spec.tags == {
        "dagster/storage_kind": "tableau",
        "dagster-tableau/asset_type": "dashboard",
        "dagster/kind/tableau": "",
        "dagster/kind/dashboard": "",
    }
    deps = list(asset_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey(["test_workbook", "sheet", "sales"])


def test_translator_data_source_spec(
    workspace_data: TableauWorkspaceData,
) -> None:
    iter_data_sources = iter(workspace_data.data_sources_by_id.values())
    translator = DagsterTableauTranslator()

    published_data_source = next(iter_data_sources)
    asset_spec = translator.get_asset_spec(
        TableauTranslatorData(content_data=published_data_source, workspace_data=workspace_data)
    )

    assert asset_spec.key.path == ["superstore_datasource"]
    assert asset_spec.metadata == {
        "dagster-tableau/id": TEST_DATA_SOURCE_ID,
        "dagster-tableau/has_extracts": False,
        "dagster-tableau/is_published": True,
    }
    assert asset_spec.tags == {
        "dagster/storage_kind": "tableau",
        "dagster-tableau/asset_type": "data_source",
        "dagster/kind/tableau": "",
        "dagster/kind/live": "",
        "dagster/kind/published datasource": "",
    }
    deps = list(asset_spec.deps)
    assert len(deps) == 0

    embedded_data_source = next(iter_data_sources)
    asset_spec = translator.get_asset_spec(
        TableauTranslatorData(content_data=embedded_data_source, workspace_data=workspace_data)
    )

    assert asset_spec.key.path == ["embedded_superstore_datasource"]
    assert asset_spec.metadata == {
        "dagster-tableau/id": TEST_EMBEDDED_DATA_SOURCE_ID,
        "dagster-tableau/has_extracts": True,
        "dagster-tableau/is_published": False,
        "dagster-tableau/workbook_id": TEST_WORKBOOK_ID,
    }
    assert asset_spec.tags == {
        "dagster/storage_kind": "tableau",
        "dagster-tableau/asset_type": "data_source",
        "dagster/kind/tableau": "",
        "dagster/kind/extract": "",
        "dagster/kind/embedded datasource": "",
    }
    deps = list(asset_spec.deps)
    assert len(deps) == 0


class MyCustomTranslator(DagsterTableauTranslator):
    def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
        )


def test_translator_custom_metadata(workspace_data: TableauWorkspaceData) -> None:
    sheet = next(iter(workspace_data.sheets_by_id.values()))

    translator = MyCustomTranslator()
    asset_spec = translator.get_asset_spec(
        TableauTranslatorData(content_data=sheet, workspace_data=workspace_data)
    )

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["prefix", "test_workbook", "sheet", "sales"]
    assert asset_spec.tags == {
        "dagster/storage_kind": "tableau",
        "dagster-tableau/asset_type": "sheet",
        "dagster/kind/sheet": "",
        "dagster/kind/tableau": "",
    }
