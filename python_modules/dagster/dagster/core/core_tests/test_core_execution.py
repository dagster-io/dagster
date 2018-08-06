import pytest

from dagster.core import types

from dagster.core.definitions import (
    SolidDefinition,
    OutputDefinition,
    MaterializationDefinition,
    SourceDefinition,
    ArgumentDefinition,
)

from dagster.core.execution import (
    _execute_core_transform,
    DagsterTypeError,
    ExecutionContext,
    _execute_materialization,
    _read_source,
)

from dagster.utils.compatability import create_custom_source_input


def create_test_context():
    return ExecutionContext()


def _read_new_single_source_input(context, new_input, arg_dict):
    assert len(new_input.sources) == 1
    return _read_source(context, new_input.sources[0], arg_dict)


def test_read_source():
    expected_output = [{'data_key': 'data_value'}]
    some_input = create_custom_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: expected_output,
        argument_def_dict={}
    )

    output = _read_source(create_test_context(), some_input.sources[0], {})

    assert output == expected_output


def test_source_arg_mismiatch():
    extra_arg_source = create_custom_source_input(
        name='some_input', source_fn=lambda context, arg_dict: [], argument_def_dict={}
    ).sources[0]

    with pytest.raises(DagsterTypeError):
        _read_source(create_test_context(), extra_arg_source, {'extra_arg': None})

    some_input_with_arg = create_custom_source_input(
        name='some_input_with_arg',
        source_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': ArgumentDefinition(types.String)},
    )

    with pytest.raises(DagsterTypeError):
        _read_new_single_source_input(create_test_context(), some_input_with_arg, {})


def test_source_arg_type_mismatch():
    some_input_with_arg = create_custom_source_input(
        name='some_input_with_arg',
        source_fn=lambda context, arg_dict: [],
        argument_def_dict={'in_arg': ArgumentDefinition(types.String)},
    )

    with pytest.raises(DagsterTypeError):
        _read_new_single_source_input(create_test_context(), some_input_with_arg, {'in_arg': 1})


def test_source_int_type():
    int_arg_source = SourceDefinition(
        source_type='SOMETHING',
        source_fn=lambda _context, _args: True,
        argument_def_dict={'an_int': ArgumentDefinition(types.Int)},
    )
    assert _read_source(create_test_context(), int_arg_source, {'an_int': 0})
    assert _read_source(create_test_context(), int_arg_source, {'an_int': 1})
    assert _read_source(create_test_context(), int_arg_source, {'an_int': None})

    with pytest.raises(DagsterTypeError):
        _read_source(create_test_context(), int_arg_source, {'an_int': 'not_an_int'})


def test_source_bool_type():
    bool_arg_source = SourceDefinition(
        source_type='SOMETHING',
        source_fn=lambda _context, _args: True,
        argument_def_dict={'an_bool': ArgumentDefinition(types.Bool)},
    )

    assert _read_source(create_test_context(), bool_arg_source, {'an_bool': True})
    assert _read_source(create_test_context(), bool_arg_source, {'an_bool': False})
    assert _read_source(create_test_context(), bool_arg_source, {'an_bool': None})

    with pytest.raises(DagsterTypeError):
        _read_source(create_test_context(), bool_arg_source, {'an_bool': 'not_an_bool'})

    with pytest.raises(DagsterTypeError):
        _read_source(create_test_context(), bool_arg_source, {'an_bool': 0})


def noop_output():
    return OutputDefinition()


def test_materialize_output():
    some_input = create_custom_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={},
    )

    def tranform_fn_inst(_context, args):
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
    some_input = create_custom_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': ArgumentDefinition(types.String)},
    )

    output = _read_new_single_source_input(
        create_test_context(), some_input, {'str_arg': 'passed_value'}
    )
    expected_output = [{'key': 'passed_value'}]
    assert output == expected_output


def test_execute_output_with_args():
    test_output = {}

    def materialization_fn_inst(context, arg_dict, value):
        assert isinstance(context, ExecutionContext)
        assert isinstance(arg_dict, dict)
        test_output['thedata'] = value
        test_output['thearg'] = arg_dict['out_arg']

    materialization = MaterializationDefinition(
        name='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={'out_arg': ArgumentDefinition(types.String)}
    )

    _execute_materialization(
        create_test_context(), materialization, {'out_arg': 'the_out_arg'}, [{
            'key': 'value'
        }]
    )


def test_execute_materialization_arg_mismatch():
    materialization = MaterializationDefinition(
        name='CUSTOM',
        materialization_fn=lambda out, dict: [],
        argument_def_dict={'out_arg': ArgumentDefinition(types.String)}
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
        name='CUSTOM',
        materialization_fn=lambda out, dict: [],
        argument_def_dict={'out_arg': ArgumentDefinition(types.String)}
    )

    with pytest.raises(DagsterTypeError):
        _execute_materialization(
            create_test_context(), custom_output, arg_dict={'out_arg': 1}, value=[{}]
        )
