import pandas as pd

from dagster import io_manager, job, op
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

    @op
    def dummy_op():
        return DummyClass.from_dict({"some_column": [2]})

    @job(resource_defs={"io_manager": custom_io_manager})
    def dummy_job():
        dummy_op()

    return dummy_job


def test_pipelines_compile_and_execute():
    managers = [
        PandasCsvIOManager(),
        PandasCsvIOManagerWithAsset(),
    ]
    for manager in managers:
        result = _generate_pipeline_for_io_manager(manager).execute_in_process()
        assert result
        assert result.success
