from dagster import check
from dagster import config

import dagster
import dagster.core
from dagster.core.definitions import (
    SolidDefinition,
    InputDefinition,
)
from dagster.core.execution import (
    DagsterExecutionFailureReason,
    execute_pipeline,
    ExecutionContext,
)
from dagster.utils.compatability import (
    create_custom_source_input, create_single_materialization_output
)


def silencing_default_context():
    return {
        'default':
        dagster.PipelineContextDefinition(
            argument_def_dict={},
            context_fn=lambda _pipeline, _args: ExecutionContext(),
        )
    }


def silencing_pipeline(solids):
    return dagster.PipelineDefinition(
        solids=solids, context_definitions=silencing_default_context()
    )


def create_failing_output_def():
    def failing_materialization_fn(*_args, **_kwargs):
        raise Exception('something bad happened')

    return create_single_materialization_output(
        name='CUSTOM',
        materialization_fn=failing_materialization_fn,
        argument_def_dict={},
    )


def create_input_set_input_def(input_name):
    return create_custom_source_input(
        input_name,
        source_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )


def create_root_success_solid(name):
    input_name = name + '_input'

    def root_transform(_context, args):
        passed_rows = list(args.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return SolidDefinition(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        output=dagster.OutputDefinition(),
    )


def create_root_transform_failure_solid(name):
    input_name = name + '_input'
    inp = create_custom_source_input(
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
        output=dagster.OutputDefinition(),
    )


def create_root_input_failure_solid(name):
    def failed_input_fn(_context, _args):
        raise Exception('something bad happened')

    input_name = name + '_input'
    inp = create_custom_source_input(
        input_name,
        source_fn=failed_input_fn,
        argument_def_dict={},
    )

    return SolidDefinition(
        name=name,
        inputs=[inp],
        transform_fn=lambda **_kwargs: {},
        output=dagster.OutputDefinition(),
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


def no_args_env(solid_name, input_name, materializations=None):
    return config.Environment(
        sources={solid_name: {
            input_name: config.Source(name='CUSTOM', args={})
        }},
        materializations=materializations,
    )


def test_transform_failure_pipeline():
    pipeline = silencing_pipeline(solids=[create_root_transform_failure_solid('failing')])
    pipeline_result = execute_pipeline(
        pipeline, environment=no_args_env('failing', 'failing_input'), throw_on_error=False
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_input_failure_pipeline():
    pipeline = silencing_pipeline(solids=[create_root_input_failure_solid('failing_input')])
    pipeline_result = execute_pipeline(
        pipeline,
        environment=no_args_env('failing_input', 'failing_input_input'),
        throw_on_error=False
    )

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_output_failure_pipeline():
    pipeline = silencing_pipeline(solids=[create_root_output_failure_solid('failing_output')])

    pipeline_result = execute_pipeline(
        pipeline,
        environment=no_args_env(
            'failing_output', 'failing_output_input',
            [config.Materialization(solid='failing_output', name='CUSTOM', args={})]
        ),
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

    def transform_fn(_context, args):
        check.failed('user error')
        return [args['A'], args['B'], {'C': 'transform_called'}]

    solid_c = SolidDefinition(
        name='C',
        inputs=[
            InputDefinition(name='A', depends_on=solid_a),
            InputDefinition(name='B', depends_on=solid_b),
        ],
        transform_fn=transform_fn,
        output=dagster.OutputDefinition(),
    )

    environment = config.Environment(
        sources={
            'A': {
                'A_input': config.Source('CUSTOM', {}),
            },
            'B': {
                'B_input': config.Source('CUSTOM', {})
            }
        }
    )
    pipeline = silencing_pipeline(solids=[solid_a, solid_b, solid_c])
    pipeline_result = execute_pipeline(
        pipeline,
        environment=environment,
        throw_on_error=False,
    )

    result_list = pipeline_result.result_list

    assert result_list[0].success
    assert result_list[1].success
    assert not result_list[2].success
    assert result_list[2].reason == DagsterExecutionFailureReason.USER_CODE_ERROR
