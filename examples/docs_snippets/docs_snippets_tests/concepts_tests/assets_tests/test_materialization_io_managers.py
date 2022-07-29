import pandas as pd

from dagster import io_manager
from dagster._legacy import ModeDefinition, execute_pipeline, pipeline, solid
from docs_snippets.concepts.assets.materialization_io_managers import (
    PandasCsvIOManager,
    PandasCsvIOManagerWithAsset,
)


class DummyClass(pd.DataFrame):
    def to_csv(self, _path):  # pylint: disable=arguments-differ
        return


def _generate_pipeline_for_io_manager(manager, config_schema=None):
    @io_manager(output_config_schema=config_schema or {})
    def custom_io_manager(_):
        return manager

    @solid
    def dummy_solid():
        return DummyClass.from_dict({"some_column": [2]})

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"io_manager": custom_io_manager})]
    )
    def dummy_pipeline():
        dummy_solid()

    return dummy_pipeline


def test_pipelines_compile_and_execute():
    managers = [
        PandasCsvIOManager(),
        PandasCsvIOManagerWithAsset(),
    ]
    for manager in managers:
        result = execute_pipeline(_generate_pipeline_for_io_manager(manager))
        assert result
        assert result.success
