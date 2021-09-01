import pytest
from dagster import Failure, execute_solid
from docs_snippets_crag.concepts.solids_pipelines.solid_events import (
    my_asset_solid,
    my_failure_metadata_solid,
    my_failure_solid,
    my_metadata_expectation_solid,
    my_metadata_output,
    my_named_yield_solid,
    my_retry_solid,
    my_simple_return_solid,
    my_simple_yield_solid,
)


def generate_stub_input_values(solid):
    input_values = {}

    default_values = {"String": "abc", "Int": 1, "Any": 1}

    input_defs = solid.input_defs
    for input_def in input_defs:
        input_values[input_def.name] = default_values[str(input_def.dagster_type.display_name)]

    return input_values


def test_solids_compile_and_execute():
    solids = [
        my_simple_yield_solid,
        my_simple_return_solid,
        my_named_yield_solid,
        my_metadata_output,
        my_metadata_expectation_solid,
        my_retry_solid,
        my_asset_solid,
    ]

    for solid in solids:
        input_values = generate_stub_input_values(solid)
        result = execute_solid(solid, input_values=input_values)
        assert result
        assert result.success


def test_failure_solid():
    with pytest.raises(Failure):
        execute_solid(my_failure_solid)


def test_failure_metadata_solid():
    with pytest.raises(Failure):
        execute_solid(my_failure_metadata_solid)
