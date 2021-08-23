from dagster import SolidDefinition, execute_solid
from docs_snippets_crag.concepts.solids_pipelines.solids import (
    context_solid,
    my_configurable_solid,
    my_input_solid,
    my_multi_output_solid,
    my_output_solid,
    my_solid,
    my_typed_input_solid,
    x_solid,
)


def generate_stub_input_values(solid):
    input_values = {}

    default_values = {"String": "abc", "Int": 1, "Any": 1}

    input_defs = solid.input_defs
    for input_def in input_defs:
        input_values[input_def.name] = default_values.get(
            str(input_def.dagster_type.display_name), 2
        )

    return input_values


def test_solids_compile_and_execute():
    solids = [
        my_input_solid,
        my_typed_input_solid,
        my_output_solid,
        my_multi_output_solid,
        my_solid,
    ]

    for solid in solids:
        input_values = generate_stub_input_values(solid)
        result = execute_solid(solid, input_values=input_values)
        assert result
        assert result.success


def test_context_solid():
    result = execute_solid(
        context_solid,
        run_config={"solids": {"context_solid": {"config": {"name": "my_name"}}}},
    )
    assert result
    assert result.success


def test_my_configurable_solid():
    result = execute_solid(
        my_configurable_solid,
        run_config={
            "solids": {
                "my_configurable_solid": {"config": {"api_endpoint": "https://localhost:3000"}}
            }
        },
    )
    assert result
    assert result.success


def test_solid_factory():
    factory_solid = x_solid("test")
    assert isinstance(factory_solid, SolidDefinition)
