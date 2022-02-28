import yaml

from dagster.utils import file_relative_path
from docs_snippets.concepts.configuration.make_values_resource_any import basic_result
from docs_snippets.concepts.configuration.make_values_resource_config_schema import (
    different_values_job,
)


def test_make_values_resource_any():
    assert basic_result.success


def test_make_values_resource_config_schema():

    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets/concepts/configuration/make_values_resource_values.yaml",
        ),
        "r", encoding="utf8",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    assert different_values_job.execute_in_process(run_config=run_config).success
