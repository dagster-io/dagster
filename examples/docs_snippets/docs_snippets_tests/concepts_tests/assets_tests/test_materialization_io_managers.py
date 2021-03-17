from dagster import execute_pipeline, io_manager, solid, pipeline, ModeDefinition
import pandas as pd
from docs_snippets.concepts.assets.materialization_io_managers import (
    PandasCsvIOManager,
    PandasCsvIOManagerWithMetadata,
    PandasCsvIOManagerWithAsset,
)


class DummyClass(pd.DataFrame):
    def to_csv(self, _path):
        return


def _generate_pipeline_for_io_manager(manager):
    @io_manager
    def custom_io_manager(_):
        return manager

    @solid
    def dummy_solid(_):
        return DummyClass.from_dict({"some_column": [2]})

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": custom_io_manager})])
    def dummy_pipeline():
        dummy_solid()

    return dummy_pipeline


def test_pipelines_compile_and_execute():
    managers = [
        PandasCsvIOManager(),
        PandasCsvIOManagerWithMetadata(),
        PandasCsvIOManagerWithAsset(),
    ]
    for manager in managers:
        result = execute_pipeline(_generate_pipeline_for_io_manager(manager))
        assert result
        assert result.success
