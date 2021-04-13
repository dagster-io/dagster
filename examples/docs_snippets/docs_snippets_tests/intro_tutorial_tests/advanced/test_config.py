from dagster import execute_pipeline
from dagster.utils import pushd, script_relative_path
from docs_snippets.intro_tutorial.advanced.configuring_solids.configurable_pipeline import (
    configurable_pipeline,
)


def test_tutorial_config_schema():
    with pushd(
        script_relative_path("../../../docs_snippets/intro_tutorial/advanced/configuring_solids/")
    ):
        result = execute_pipeline(
            configurable_pipeline,
            run_config={
                "solids": {
                    "read_csv": {"config": {"csv_name": "cereal.csv"}},
                }
            },
        )

    assert result.success
