import json
import os
from pathlib import Path

from dagster import AssetKey, AssetMaterialization, TableColumn, TableSchema
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from pytest_mock import MockerFixture

test_dagster_metadata_dbt_project_dir = test_dagster_metadata_manifest_path = (
    Path(__file__).joinpath("..", "dbt_projects", "test_dagster_metadata").resolve()
)
test_dagster_metadata_manifest_path = test_dagster_metadata_dbt_project_dir.joinpath(
    "manifest.json"
)
test_dagster_metadata_manifest = json.loads(test_dagster_metadata_manifest_path.read_bytes())

dagster_dbt_translator_with_table_schema_metadata = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_table_schema_metadata=True)
)


def test_no_table_schema_metadata(mocker: MockerFixture) -> None:
    mock_context = mocker.MagicMock()
    mock_context.assets_def = None
    mock_context.has_assets_def = False

    dbt = DbtCliResource(project_dir=os.fspath(test_dagster_metadata_dbt_project_dir))

    events = list(
        dbt.cli(
            ["build"],
            manifest=test_dagster_metadata_manifest,
            context=mock_context,
        ).stream()
    )
    materializations_by_asset_key = {
        dagster_event.asset_key: dagster_event
        for dagster_event in events
        if isinstance(dagster_event, AssetMaterialization)
    }
    customers_materialization = materializations_by_asset_key[AssetKey(["customers"])]

    assert "table_schema" not in customers_materialization.metadata


def test_table_schema_metadata(mocker: MockerFixture) -> None:
    mock_context = mocker.MagicMock()
    mock_context.assets_def = None
    mock_context.has_assets_def = False

    dbt = DbtCliResource(project_dir=os.fspath(test_dagster_metadata_dbt_project_dir))

    events = list(
        dbt.cli(
            ["build"],
            manifest=test_dagster_metadata_manifest,
            dagster_dbt_translator=dagster_dbt_translator_with_table_schema_metadata,
            context=mock_context,
        ).stream()
    )
    materializations_by_asset_key = {
        dagster_event.asset_key: dagster_event
        for dagster_event in events
        if isinstance(dagster_event, AssetMaterialization)
    }
    customers_materialization = materializations_by_asset_key[AssetKey(["customers"])]

    assert (
        TableSchema(
            columns=[
                TableColumn("customer_id", type="INTEGER"),
                TableColumn("first_name", type="character varying(256)"),
                TableColumn("last_name", type="character varying(256)"),
                TableColumn("first_order", type="DATE"),
                TableColumn("most_recent_order", type="DATE"),
                TableColumn("number_of_orders", type="BIGINT"),
                TableColumn("customer_lifetime_value", type="DOUBLE"),
            ]
        )
        == customers_materialization.metadata["table_schema"].value
    )
