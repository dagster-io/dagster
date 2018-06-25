from dagster import check
from dagster import config

import dagster.core
from dagster.core.definitions import (
    SolidDefinition,
    create_single_source_input,
    create_no_materialization_output,
    create_single_materialization_output,
    InputDefinition,
)
from dagster.core.execution import (
    DagsterExecutionContext, DagsterExecutionFailureReason, execute_pipeline, materialize_pipeline,
    create_pipeline_env_from_arg_dicts
)


def create_test_context():
    return DagsterExecutionContext()


def create_failing_output_def():
    def failing_materialization_fn(*_args, **_kwargs):
        raise Exception('something bad happened')

    return create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=failing_materialization_fn,
        argument_def_dict={},
    )


def create_input_set_input_def(input_name):
    return create_single_source_input(
        input_name,
        source_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )


def create_root_success_solid(name):
    input_name = name + '_input'

    def root_transform(context, args):
        passed_rows = list(args.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return SolidDefinition(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        output=create_no_materialization_output(),
    )


def create_root_transform_failure_solid(name):
    input_name = name + '_input'
    inp = create_single_source_input(
        input_name,
        source_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )

    def failed_transform(**_kwargs):
        raise Exception('Transform failed')

    return SolidDefinition(
        name=name,
        inputs=[inp],
        transform_fn=failed_transform,
        output=create_no_materialization_output(),
    )


def create_root_input_failure_solid(name):
    def failed_input_fn(context, args):
        raise Exception('something bad happened')

    input_name = name + '_input'
    inp = create_single_source_input(
        input_name,
        source_fn=failed_input_fn,
        argument_def_dict={},
    )

    return SolidDefinition(
        name=name,
        inputs=[inp],
        transform_fn=lambda **_kwargs: {},
        output=create_no_materialization_output(),
    )


def create_root_output_failure_solid(name):
    input_name = name + '_input'

    def root_transform(**kwargs):
        passed_rows = list(kwargs.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return SolidDefinition(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        output=create_failing_output_def(),
    )


def test_transform_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_transform_failure_solid('failing')])
    pipeline_result = execute_pipeline(
        create_test_context(),
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, {'failing_input': {}}),
        throw_on_error=False
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_input_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_input_failure_solid('failing_input')])
    pipeline_result = execute_pipeline(
        create_test_context(),
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, {'failing_input_input': {}}),
        throw_on_error=False
    )

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_output_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_output_failure_solid('failing_output')])

    input_arg_dicts = {'failing_output_input': {}}
    environment = create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts)

    pipeline_result = materialize_pipeline(
        create_test_context(),
        pipeline,
        environment=environment,
        materializations=[
            config.Materialization(solid='failing_output', materialization_type='CUSTOM', args={})
        ],
        throw_on_error=False,
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_failure_midstream():
    solid_a = create_root_success_solid('A')
    solid_b = create_root_success_solid('B')

    def transform_fn(context, args):
        check.failed('user error')
        return [args['A'], args['B'], {'C': 'transform_called'}]

    solid_c = SolidDefinition(
        name='C',
        inputs=[
            InputDefinition(name='A', sources=[], depends_on=solid_a),
            InputDefinition(name='B', sources=[], depends_on=solid_b),
        ],
        transform_fn=transform_fn,
        output=create_no_materialization_output(),
    )

    input_arg_dicts = {'A_input': {}, 'B_input': {}}
    pipeline = dagster.core.pipeline(solids=[solid_a, solid_b, solid_c])
    pipeline_result = execute_pipeline(
        create_test_context(),
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts),
        throw_on_error=False,
    )

    result_list = pipeline_result.result_list

    assert result_list[0].success
    assert result_list[1].success
    assert not result_list[2].success
    assert result_list[2].reason == DagsterExecutionFailureReason.USER_CODE_ERROR
