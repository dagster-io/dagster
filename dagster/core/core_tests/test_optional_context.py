from dagster import check

from dagster.core.definitions import (
    create_single_materialization_output, Solid, create_single_source_input
)
from dagster.core.execution import (
    DagsterExecutionContext, output_single_solid, create_single_solid_env_from_arg_dicts
)


def create_test_context():
    return DagsterExecutionContext()


def get_input(with_context):
    check.bool_param(with_context, 'with_context')
    if with_context:

        def input_fn(context, arg_dict):
            assert isinstance(context, DagsterExecutionContext)
            assert arg_dict == {}
            return [{'data_key': 'data_value'}]

        return create_single_source_input(
            name='some_input', source_fn=input_fn, argument_def_dict={}
        )
    else:

        def input_fn(arg_dict):
            assert arg_dict == {}
            return [{'data_key': 'data_value'}]

        return create_single_source_input(
            name='some_input', source_fn=input_fn, argument_def_dict={}
        )


def get_transform_fn(with_context):
    check.bool_param(with_context, 'with_context')
    if with_context:

        def tranform_fn_inst(context, some_input):
            assert isinstance(context, DagsterExecutionContext)
            some_input[0]['data_key'] = 'new_value'
            return some_input

        return tranform_fn_inst
    else:

        def tranform_fn_inst(some_input):
            some_input[0]['data_key'] = 'new_value'
            return some_input

        return tranform_fn_inst


def get_output(with_context, test_output):
    check.bool_param(with_context, 'with_context')
    check.dict_param(test_output, 'test_output')
    if with_context:

        def materialization_fn_inst(data, context, arg_dict):
            assert isinstance(context, DagsterExecutionContext)
            assert isinstance(arg_dict, dict)
            assert arg_dict == {}
            assert isinstance(data, list)
            assert isinstance(data[0], dict)
            assert data[0]['data_key'] == 'new_value'

            test_output['thedata'] = data

        return create_single_materialization_output(
            materialization_type='CUSTOM',
            materialization_fn=materialization_fn_inst,
            argument_def_dict={},
        )
    else:

        def materialization_fn_inst(data, arg_dict):
            assert isinstance(arg_dict, dict)
            assert arg_dict == {}
            assert isinstance(data, list)
            assert isinstance(data[0], dict)
            assert data[0]['data_key'] == 'new_value'
            test_output['thedata'] = data

        return create_single_materialization_output(
            materialization_type='CUSTOM',
            materialization_fn=materialization_fn_inst,
            argument_def_dict={},
        )


def test_all_context():
    test_output = {}

    single_solid = Solid(
        name='some_node',
        inputs=[get_input(with_context=True)],
        transform_fn=get_transform_fn(with_context=True),
        output=get_output(with_context=True, test_output=test_output),
    )

    result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(single_solid, {'some_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert result.success
    assert test_output['thedata'] == [{'data_key': 'new_value'}]


def test_no_input_fn_context():
    test_output = {}

    single_solid = Solid(
        name='some_node',
        inputs=[get_input(with_context=False)],
        transform_fn=get_transform_fn(with_context=True),
        output=get_output(with_context=True, test_output=test_output),
    )

    result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(single_solid, {'some_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert result.success
    assert test_output['thedata'] == [{'data_key': 'new_value'}]


def test_no_transform_conteext():
    test_output = {}

    single_solid = Solid(
        name='some_node',
        inputs=[get_input(with_context=True)],
        transform_fn=get_transform_fn(with_context=False),
        output=get_output(with_context=True, test_output=test_output),
    )

    result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(single_solid, {'some_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert result.success
    assert test_output['thedata'] == [{'data_key': 'new_value'}]


def test_no_materialization_fn_context():
    test_output = {}

    single_solid = Solid(
        name='some_node',
        inputs=[get_input(with_context=True)],
        transform_fn=get_transform_fn(with_context=True),
        output=get_output(with_context=False, test_output=test_output),
    )

    result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(single_solid, {'some_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert result.success
    assert test_output['thedata'] == [{'data_key': 'new_value'}]
