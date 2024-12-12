from pathlib import Path

from dagster import AssetKey
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
)
from dagster_components.lib.dlt_pipeline_collection import DltPipelineCollection

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

DLT_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "dlt_location"
COMPONENT_RELPATH = "components/my_dlt_project"


def test_python_params() -> None:
    context = script_load_context()
    component = DltPipelineCollection.from_decl_node(
        context=context,
        decl_node=YamlComponentDecl(
            path=DLT_LOCATION_PATH / COMPONENT_RELPATH,
            component_file_model=ComponentFileModel(
                type="dagster_components.dlt_pipeline_collection",
                params={
                    "pipeline_runs": [
                        {
                            "pipeline": {
                                "pipeline_name": "csv_to_duckdb",
                                "dataset_name": "csv",
                                "destination": "duckdb",
                            },
                            "source": {
                                "source_reference": "dagster_components_tests.dlt_sources.filesystem.csv_source",
                                "params": {"bucket_url": f"file://{DLT_LOCATION_PATH}/input.csv"},
                            },
                            "runtime_params": {},
                        }
                    ]
                },
            ),
        ),
    )
    assert get_asset_keys(component) == {
        AssetKey("csv_source_filesystem"),
        AssetKey("dlt_csv_source_read_csv"),
    }


def test_load_from_path() -> None:
    components = build_components_from_component_folder(
        script_load_context(), DLT_LOCATION_PATH / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == {
        AssetKey("csv_source_filesystem"),
        AssetKey("dlt_csv_source_read_csv"),
    }

    assert_assets(components[0], 2)
