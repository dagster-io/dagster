import pytest

from dagster.core import types

from dagster.core.definitions import (
    SolidDefinition, OutputDefinition, create_single_source_input, MaterializationDefinition
)

from dagster.core.execution import (
    _execute_core_transform, DagsterTypeError, DagsterExecutionContext, _execute_materialization,
    _read_source
)


def create_test_context():
    return DagsterExecutionContext()


def _read_new_single_source_input(context, new_input, arg_dict):
    assert len(new_input.sources) == 1
    return _read_source(context, new_input.sources[0], arg_dict)


def test_read_source():
    expected_output = [{'data_key': 'data_value'}]
    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: expected_output,
        argument_def_dict={}
    )

    output = _read_source(create_test_context(), some_input.sources[0], {})

    assert output == expected_output


def test_source_arg_mismiatch():
    extra_arg_source = create_single_source_input(
        name='some_input', source_fn=lambda context, arg_dict: [], argument_def_dict={}
    ).sources[0]

    with pytest.raises(DagsterTypeError):
        _read_source(create_test_context(), extra_arg_source, {'extra_arg': None})

    some_input_with_arg = create_single_source_input(
        name='some_input_with_arg',
        source_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': types.STRING}
    )

    with pytest.raises(DagsterTypeError):
        _read_new_single_source_input(create_test_context(), some_input_with_arg, {})


def test_materialize_input_arg_type_mismatch():
    some_input_with_arg = create_single_source_input(
        name='some_input_with_arg',
        source_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': types.STRING}
    )

    with pytest.raises(DagsterTypeError):
        _read_new_single_source_input(create_test_context(), some_input_with_arg, {'in_arg': 1})


def noop_output():
    return OutputDefinition()


def test_materialize_output():
    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={},
    )

    def tranform_fn_inst(context, args):
        args['some_input'][0]['data_key'] = 'new_value'
        return args['some_input']

    single_solid = SolidDefinition(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        output=noop_output(),
    )

    value = _read_new_single_source_input(create_test_context(), some_input, {})

    output = _execute_core_transform(
        create_test_context(),
        single_solid.transform_fn,
        {'some_input': value},
    )

    assert output == [{'data_key': 'new_value'}]


def test_materialize_input_with_args():
    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': types.STRING}
    )

    output = _read_new_single_source_input(
        create_test_context(), some_input, {'str_arg': 'passed_value'}
    )
    expected_output = [{'key': 'passed_value'}]
    assert output == expected_output


def single_materialization_output(materialization_type, materialization_fn, argument_def_dict):
    return OutputDefinition(
        materializations=[
            MaterializationDefinition(
                materialization_type=materialization_type,
                materialization_fn=materialization_fn,
                argument_def_dict=argument_def_dict
            )
        ]
    )


def test_execute_output_with_args():
    test_output = {}

    def materialization_fn_inst(context, arg_dict, value):
        assert isinstance(context, DagsterExecutionContext)
        assert isinstance(arg_dict, dict)
        test_output['thedata'] = value
        test_output['thearg'] = arg_dict['out_arg']

    materialization = MaterializationDefinition(
        materialization_type='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={'out_arg': types.STRING}
    )

    _execute_materialization(
        create_test_context(), materialization, {'out_arg': 'the_out_arg'}, [{
            'key': 'value'
        }]
    )


def test_execute_materialization_arg_mismatch():
    materialization = MaterializationDefinition(
        materialization_type='CUSTOM',
        materialization_fn=lambda out, dict: [],
        argument_def_dict={'out_arg': types.STRING}
    )

    with pytest.raises(DagsterTypeError):
        _execute_materialization(create_test_context(), materialization, arg_dict={}, value=[{}])

    with pytest.raises(DagsterTypeError):
        _execute_materialization(
            create_test_context(),
            materialization,
            arg_dict={
                'out_arg': 'foo',
                'extra_arg': 'bar'
            },
            value=[{}]
        )


def test_execute_materialization_arg_type_mismatch():
    custom_output = MaterializationDefinition(
        materialization_type='CUSTOM',
        materialization_fn=lambda out, dict: [],
        argument_def_dict={'out_arg': types.STRING}
    )

    with pytest.raises(DagsterTypeError):
        _execute_materialization(
            create_test_context(), custom_output, arg_dict={'out_arg': 1}, value=[{}]
        )
