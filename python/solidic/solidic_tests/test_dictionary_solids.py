import pytest

from solidic.types import SolidString

from solidic.definitions import (
    Solid, SolidInputDefinition, SolidOutputTypeDefinition, SolidExecutionContext
)

from dagster.execution import (
    materialize_input, execute_core_transform, execute_solid, execute_output, SolidExecutionError
)


def create_test_context():
    return SolidExecutionContext()


def test_materialize_input():
    expected_output = [{'data_key': 'data_value'}]
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda arg_dict: expected_output, argument_def_dict={}
    )

    output = materialize_input(create_test_context(), some_input, {})

    assert output == expected_output


def test_materialize_input_arg_mismatch():
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda arg_dict: [], argument_def_dict={}
    )

    with pytest.raises(SolidExecutionError):
        materialize_input(create_test_context(), some_input, {'extra_arg': None})

    some_input_with_arg = SolidInputDefinition(
        name='some_input_with_arg',
        input_fn=lambda arg_dict: [],
        argument_def_dict={'in_arg': SolidString}
    )

    with pytest.raises(SolidExecutionError):
        materialize_input(create_test_context(), some_input_with_arg, {})


def test_materialize_input_arg_type_mismatch():
    some_input_with_arg = SolidInputDefinition(
        name='some_input_with_arg',
        input_fn=lambda arg_dict: [],
        argument_def_dict={'in_arg': SolidString}
    )

    with pytest.raises(SolidExecutionError):
        materialize_input(create_test_context(), some_input_with_arg, {'in_arg': 1})


def test_materialize_output():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={},
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    def output_fn_inst(_data, _output_arg_dict):
        pass

    custom_output_type_def = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
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


def test_execute_solid_no_args():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={}
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    test_output = {}

    def output_fn_inst(data, _output_arg_dict):
        test_output['thedata'] = data

    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
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


def test_materialize_input_with_args():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString}
    )

    output = materialize_input(create_test_context(), some_input, {'str_arg': 'passed_value'})
    expected_output = [{'key': 'passed_value'}]
    assert output == expected_output


def test_execute_output_with_args():
    test_output = {}

    def output_fn_inst(materialized_output, output_arg_dict):
        test_output['thedata'] = materialized_output
        test_output['thearg'] = output_arg_dict['out_arg']

    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM', output_fn=output_fn_inst, argument_def_dict={'out_arg': SolidString}
    )

    execute_output(
        create_test_context(), custom_output, {'out_arg': 'the_out_arg'}, [{
            'key': 'value'
        }]
    )


def test_execute_output_arg_mismatch():
    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM', output_fn=lambda out, dict: [], argument_def_dict={'out_arg': SolidString}
    )

    with pytest.raises(SolidExecutionError):
        execute_output(
            create_test_context(), custom_output, output_arg_dict={}, materialized_output=[{}]
        )

    with pytest.raises(SolidExecutionError):
        execute_output(
            create_test_context(),
            custom_output,
            output_arg_dict={
                'out_arg': 'foo',
                'extra_arg': 'bar'
            },
            materialized_output=[{}]
        )


def test_execute_output_arg_type_mismatch():
    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM', output_fn=lambda out, dict: [], argument_def_dict={'out_arg': SolidString}
    )

    with pytest.raises(SolidExecutionError):
        execute_output(
            create_test_context(),
            custom_output,
            output_arg_dict={'out_arg': 1},
            materialized_output=[{}]
        )


def test_execute_solid_with_args():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString}
    )

    test_output = {}

    def output_fn_inst(materialized_output, output_arg_dict):
        materialized_output[0]['output_key'] = output_arg_dict['str_output_arg']
        test_output['thedata'] = materialized_output

    custom_output = SolidOutputTypeDefinition(
        name='CUSTOM', output_fn=output_fn_inst, argument_def_dict={'str_output_arg': SolidString}
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=lambda some_input: some_input,
        output_type_defs=[custom_output],
    )

    execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'some_input': {
            'str_arg': 'an_input_arg'
        }},
        output_type='CUSTOM',
        output_arg_dict={'str_output_arg': 'an_output_arg'},
    )

    assert test_output['thedata'][0]['key'] == 'an_input_arg'
    assert test_output['thedata'][0]['output_key'] == 'an_output_arg'
