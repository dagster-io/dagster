from pathlib import Path

from dagster import AssetExecutionContext, materialize
from dagster._core.definitions.metadata import TableSchemaMetadataValue
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator, DagsterSdfTranslatorSettings
from dagster_sdf.resource import SdfCliResource
from dagster_sdf.sdf_workspace import SdfWorkspace

from dagster_sdf_tests.sdf_workspaces import moms_flower_shop_path


def test_table_metadata_column_schema(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_raw_sql_description=True)
        ),
    )
    def my_flower_shop_assets(context: AssetExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(
            ["run", "--save", "info-schema"],
            target_dir=moms_flower_shop_target_dir,
            context=context,
        ).stream()

    result = materialize(
        [my_flower_shop_assets],
        resources={"sdf": SdfCliResource(workspace_dir=moms_flower_shop_path)},
    )

    assert result.success

    for event in result.get_asset_observation_events():
        metadata = event.asset_observation_data.asset_observation.metadata
        assert "dagster/column_schema" in metadata
        assert isinstance(metadata["dagster/column_schema"], TableSchemaMetadataValue)
        assert len(metadata["dagster/column_schema"].schema.columns) > 0
