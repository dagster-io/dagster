from dagster import SolidDefinition, execute_solid
from docs_snippets.concepts.solids_pipelines.solids import (
    adder,
    context_solid,
    multiple_outputs_solid,
    my_configured_solid,
    my_input_example_solid,
    my_input_output_example_solid,
    my_solid,
    my_typehints_solid,
    no_input_defs_solid,
    single_output_solid,
    untyped_inputs_solid,
    x_solid,
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
        my_solid,
        my_input_example_solid,
        my_typehints_solid,
        my_input_output_example_solid,
        adder,
        single_output_solid,
        multiple_outputs_solid,
        untyped_inputs_solid,
        no_input_defs_solid,
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


def test_my_configured_solid():
    result = execute_solid(
        my_configured_solid,
        run_config={
            "solids": {
                "my_configured_solid": {"config": {"api_endpoint": "https://localhost:3000"}}
            }
        },
    )
    assert result
    assert result.success


def test_solid_factory():
    factory_solid = x_solid("test")
    assert isinstance(factory_solid, SolidDefinition)
