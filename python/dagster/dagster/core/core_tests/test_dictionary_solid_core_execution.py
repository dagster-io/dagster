import pytest

from dagster.core.types import SolidString

from dagster.core.definitions import (Solid, SolidInputDefinition, SolidOutputDefinition)

from dagster.core.execution import (
    _execute_input, _execute_core_transform, _execute_output, SolidTypeError, SolidExecutionContext
)


def create_test_context():
    return SolidExecutionContext()


def test_execute_input():
    expected_output = [{'data_key': 'data_value'}]
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda context, arg_dict: expected_output, argument_def_dict={}
    )

    output = _execute_input(create_test_context(), some_input, {})

    assert output == expected_output


def test_materialize_input_arg_mismatch():
    some_input = SolidInputDefinition(
        name='some_input', input_fn=lambda context, arg_dict: [], argument_def_dict={}
    )

    with pytest.raises(SolidTypeError):
        _execute_input(create_test_context(), some_input, {'extra_arg': None})

    some_input_with_arg = SolidInputDefinition(
        name='some_input_with_arg',
        input_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': SolidString}
    )

    with pytest.raises(SolidTypeError):
        _execute_input(create_test_context(), some_input_with_arg, {})


def test_materialize_input_arg_type_mismatch():
    some_input_with_arg = SolidInputDefinition(
        name='some_input_with_arg',
        input_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': SolidString}
    )

    with pytest.raises(SolidTypeError):
        _execute_input(create_test_context(), some_input_with_arg, {'in_arg': 1})


def test_materialize_output():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda context, arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={},
    )

    def tranform_fn_inst(some_input):
        some_input[0]['data_key'] = 'new_value'
        return some_input

    custom_output_def = SolidOutputDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        outputs=[custom_output_def],
    )

    materialized_input = _execute_input(create_test_context(), some_input, {})

    output = _execute_core_transform(
        create_test_context(),
        single_solid.transform_fn,
        {'some_input': materialized_input},
    )

    assert output == [{'data_key': 'new_value'}]


def test_materialize_output_with_context():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda context, arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={},
    )

    def tranform_fn_inst(context, some_input):
        assert isinstance(context, SolidExecutionContext)
        some_input[0]['data_key'] = 'new_value'
        return some_input

    custom_output_def = SolidOutputDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        outputs=[custom_output_def],
    )

    materialized_input = _execute_input(create_test_context(), some_input, {})

    output = _execute_core_transform(
        create_test_context(),
        single_solid.transform_fn,
        {'some_input': materialized_input},
    )

    assert output == [{'data_key': 'new_value'}]


def test_materialize_input_with_args():
    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda context, arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString}
    )

    output = _execute_input(create_test_context(), some_input, {'str_arg': 'passed_value'})
    expected_output = [{'key': 'passed_value'}]
    assert output == expected_output


def test_execute_output_with_args():
    test_output = {}

    def output_fn_inst(materialized_output, context, arg_dict):
        assert isinstance(context, SolidExecutionContext)
        assert isinstance(arg_dict, dict)
        test_output['thedata'] = materialized_output
        test_output['thearg'] = arg_dict['out_arg']

    custom_output = SolidOutputDefinition(
        name='CUSTOM', output_fn=output_fn_inst, argument_def_dict={'out_arg': SolidString}
    )

    _execute_output(
        create_test_context(), custom_output, {'out_arg': 'the_out_arg'}, [{
            'key': 'value'
        }]
    )


def test_execute_output_arg_mismatch():
    custom_output = SolidOutputDefinition(
        name='CUSTOM', output_fn=lambda out, dict: [], argument_def_dict={'out_arg': SolidString}
    )

    with pytest.raises(SolidTypeError):
        _execute_output(
            create_test_context(), custom_output, output_arg_dict={}, materialized_output=[{}]
        )

    with pytest.raises(SolidTypeError):
        _execute_output(
            create_test_context(),
            custom_output,
            output_arg_dict={
                'out_arg': 'foo',
                'extra_arg': 'bar'
            },
            materialized_output=[{}]
        )


def test_execute_output_arg_type_mismatch():
    custom_output = SolidOutputDefinition(
        name='CUSTOM', output_fn=lambda out, dict: [], argument_def_dict={'out_arg': SolidString}
    )

    with pytest.raises(SolidTypeError):
        _execute_output(
            create_test_context(),
            custom_output,
            output_arg_dict={'out_arg': 1},
            materialized_output=[{}]
        )
