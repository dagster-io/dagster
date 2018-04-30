from dagster import DagsterPipeline

from dagster.solid_defs import (
    Solid, SolidInputDefinition, SolidOutputTypeDefinition, SolidExecutionContext
)

from dagster.execution import (materialize_input, execute_core_transform, execute_solid)


def create_test_context():
    return SolidExecutionContext()


def test_materialize_input():
    expected_output = [{'data_key': 'data_value'}]
    some_input = SolidInputDefinition(name='some_input', input_fn=lambda: expected_output)

    output = materialize_input(create_test_context(), some_input, {})

    assert output == expected_output


def test_materialize_output():
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda: [{'data_key': 'data_value'}]
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    def output_fn_inst(_data):
        pass

    custom_output_type_def = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        output_type_defs=[custom_output_type_def],
    )

    materialized_input = materialize_input(create_test_context(), some_input, {})

    output = execute_core_transform(
        create_test_context(), single_solid, {'some_input': materialized_input}
    )

    assert output == [{'data_key': 'new_value'}]


def test_execute_solid():
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda: [{'data_key': 'data_value'}]
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    test_output = {}

    def output_fn_inst(data):
        test_output['thedata'] = data

    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        output_type_defs=[custom_output],
    )

    execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'some_input': {}},
        output_type='CUSTOM',
        output_arg_dict={}
    )

    assert test_output['thedata'] == [{'data_key': 'new_value'}]
