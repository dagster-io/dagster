import pytest

from dagster import config
from dagster.core import types

from dagster.core.definitions import (
    SolidDefinition,
    ExpectationDefinition,
    ExpectationResult,
    create_single_source_input,
    create_single_materialization_output,
    create_no_materialization_output,
)

from dagster.core.execution import (
    output_single_solid, DagsterExecutionResult, DagsterExecutionFailureReason,
    DagsterExecutionContext, execute_single_solid, create_single_solid_env_from_arg_dicts
)

from dagster.core.errors import DagsterExpectationFailedError


def create_test_context():
    return DagsterExecutionContext()


def test_execute_solid_no_args():
    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'data_key': 'data_value'}],
        argument_def_dict={}
    )

    def tranform_fn_inst(context, args):
        args['some_input'][0]['data_key'] = 'new_value'
        return args['some_input']

    test_output = {}

    def materialization_fn_inst(context, arg_dict, data):
        assert isinstance(context, DagsterExecutionContext)
        assert isinstance(arg_dict, dict)
        test_output['thedata'] = data

    custom_output = create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={},
    )

    single_solid = SolidDefinition(
        name='some_node',
        inputs=[some_input],
        transform_fn=tranform_fn_inst,
        output=custom_output,
    )

    output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(single_solid, {'some_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert test_output['thedata'] == [{'data_key': 'new_value'}]


def create_single_dict_input(expectations=None):
    return create_single_source_input(
        name='some_input',
        source_fn=lambda context, arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': types.STRING},
        expectations=expectations or [],
    )


def create_noop_output(test_output, expectations=None):
    def set_test_output(context, arg_dict, output):
        assert isinstance(context, DagsterExecutionContext)
        assert arg_dict == {}
        test_output['thedata'] = output

    return create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=set_test_output,
        argument_def_dict={},
        expectations=expectations
    )


def test_hello_world():
    def transform_fn(context, args):
        assert isinstance(context, DagsterExecutionContext)
        hello_world_input = args['hello_world_input']
        assert isinstance(hello_world_input, dict)
        hello_world_input['hello'] = 'world'
        return hello_world_input

    output_events = {}

    def materialization_fn(context, arg_dict, data):
        assert data['hello'] == 'world'
        assert isinstance(context, DagsterExecutionContext)
        assert arg_dict == {}
        output_events['called'] = True

    hello_world = SolidDefinition(
        name='hello_world',
        inputs=[
            create_single_source_input(
                name='hello_world_input',
                source_fn=lambda context, arg_dict: {},
                argument_def_dict={},
            )
        ],
        transform_fn=transform_fn,
        output=create_single_materialization_output(
            materialization_type='CUSTOM',
            materialization_fn=materialization_fn,
            argument_def_dict={}
        ),
    )

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_single_solid_env_from_arg_dicts(hello_world, {'hello_world_input': {}})
    )

    assert result.success

    assert result.transformed_value['hello'] == 'world'

    assert 'called' not in output_events

    output_result = output_single_solid(
        create_test_context(),
        hello_world,
        environment=create_single_solid_env_from_arg_dicts(hello_world, {'hello_world_input': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    if output_result.exception:
        raise output_result.exception

    assert output_result.success

    assert 'called' in output_events


def test_execute_solid_with_args():
    test_output = {}

    single_solid = SolidDefinition(
        name='some_node',
        inputs=[create_single_dict_input()],
        transform_fn=lambda context, args: args['some_input'],
        output=create_noop_output(test_output),
    )

    result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(
            single_solid,
            {'some_input': {
                'str_arg': 'an_input_arg'
            }},
        ),
        materialization_type='CUSTOM',
        arg_dict={},
    )

    if result.exception:
        raise result.exception

    assert result.success

    assert test_output['thedata'][0]['key'] == 'an_input_arg'


def test_execute_solid_with_failed_input_expectation_non_throwing():
    single_solid = create_input_failing_solid()

    solid_execution_result = output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(
            single_solid, {'some_input': {
                'str_arg': 'an_input_arg'
            }}
        ),
        materialization_type='CUSTOM',
        arg_dict={},
        throw_on_error=False,
    )

    assert isinstance(solid_execution_result, DagsterExecutionResult)
    assert solid_execution_result.success is False
    assert solid_execution_result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE


def test_execute_solid_with_failed_input_expectation_throwing():
    single_solid = create_input_failing_solid()

    with pytest.raises(DagsterExpectationFailedError):
        output_single_solid(
            create_test_context(),
            single_solid,
            environment=create_single_solid_env_from_arg_dicts(
                single_solid, {'some_input': {
                    'str_arg': 'an_input_arg'
                }}
            ),
            materialization_type='CUSTOM',
            arg_dict={},
        )

    with pytest.raises(DagsterExpectationFailedError):
        output_single_solid(
            create_test_context(),
            single_solid,
            environment=create_single_solid_env_from_arg_dicts(
                single_solid, {'some_input': {
                    'str_arg': 'an_input_arg'
                }}
            ),
            materialization_type='CUSTOM',
            arg_dict={},
        )


def create_input_failing_solid():
    test_output = {}

    def failing_expectation_fn(_some_input):
        return ExpectationResult(success=False)

    failing_expect = ExpectationDefinition(name='failing', expectation_fn=failing_expectation_fn)

    return SolidDefinition(
        name='some_node',
        inputs=[create_single_dict_input(expectations=[failing_expect])],
        transform_fn=lambda context, args: args['some_input'],
        output=create_noop_output(test_output),
    )


def test_execute_solid_with_failed_output_expectation_non_throwing():
    failing_solid = create_output_failing_solid()

    solid_execution_result = output_single_solid(
        create_test_context(),
        failing_solid,
        environment=create_single_solid_env_from_arg_dicts(
            failing_solid, {'some_input': {
                'str_arg': 'an_input_arg'
            }}
        ),
        materialization_type='CUSTOM',
        arg_dict={},
        throw_on_error=False
    )

    assert isinstance(solid_execution_result, DagsterExecutionResult)
    assert solid_execution_result.success is False
    assert solid_execution_result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE


def test_execute_solid_with_failed_output_expectation_throwing():
    failing_solid = create_output_failing_solid()

    with pytest.raises(DagsterExpectationFailedError):
        output_single_solid(
            create_test_context(),
            failing_solid,
            environment=create_single_solid_env_from_arg_dicts(
                failing_solid, {'some_input': {
                    'str_arg': 'an_input_arg'
                }}
            ),
            materialization_type='CUSTOM',
            arg_dict={},
        )

    with pytest.raises(DagsterExpectationFailedError):
        output_single_solid(
            create_test_context(),
            failing_solid,
            environment=create_single_solid_env_from_arg_dicts(
                failing_solid, {'some_input': {
                    'str_arg': 'an_input_arg'
                }}
            ),
            materialization_type='CUSTOM',
            arg_dict={},
        )


def _set_key_value(ddict, key, value):
    ddict[key] = value


def test_execute_solid_with_no_inputs():
    did_run_dict = {}
    no_args_solid = SolidDefinition(
        name='no_args_solid',
        inputs=[],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'did_run', True),
        output=create_no_materialization_output(),
    )

    result = execute_single_solid(
        DagsterExecutionContext(), no_args_solid, environment=config.Environment.empty()
    )

    assert result.success
    assert did_run_dict['did_run'] is True


def create_output_failing_solid():
    test_output = {}

    def failing_expectation_fn(_output):
        return ExpectationResult(success=False)

    output_expectation = ExpectationDefinition(
        name='output_failure', expectation_fn=failing_expectation_fn
    )

    return SolidDefinition(
        name='some_node',
        inputs=[create_single_dict_input()],
        transform_fn=lambda context, args: args['some_input'],
        output=create_noop_output(test_output, expectations=[output_expectation]),
    )
