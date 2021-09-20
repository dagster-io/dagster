import yaml
from dagster import execute_pipeline
from dagster.utils import file_relative_path


def test_make_values_resource_any():
    from docs_snippets_crag.concepts.configuration.make_values_resource_any import (
        my_pipeline,
    )

    assert execute_pipeline(
        my_pipeline, run_config={"resources": {"value": {"config": "some_value"}}}
    )


def test_make_values_resource_config_schema():
    from docs_snippets_crag.concepts.configuration.make_values_resource_config_schema import (
        my_pipeline,
    )

    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets_crag/concepts/configuration/make_values_resource_values.yaml",
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert execute_pipeline(my_pipeline, run_config).success
