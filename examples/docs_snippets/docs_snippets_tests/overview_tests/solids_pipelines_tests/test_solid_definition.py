from docs_snippets.overview.solids_pipelines.solid_definition import my_solid, solid

from dagster import execute_solid


def test_decorator_solid_example():
    result = execute_solid(my_solid)
    assert result
    assert result.output_values["result"] == 1


def test_definition_class_solid_example():
    result = execute_solid(solid)
    assert result
    assert result.output_values["result"] == 1
