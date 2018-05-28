from dagster import check

import dagster.core
from dagster.core.definitions import (Solid, InputDefinition, OutputDefinition)
from dagster.core.execution import (
    DagsterExecutionContext, DagsterExecutionFailureReason, execute_pipeline, output_pipeline
)


def create_test_context():
    return DagsterExecutionContext()


def create_dummy_output_def():
    return OutputDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )


def create_failing_output_def():
    def failing_output_fn(*_args, **_kwargs):
        raise Exception('something bad happened')

    return OutputDefinition(
        name='CUSTOM',
        output_fn=failing_output_fn,
        argument_def_dict={},
    )


def create_input_set_input_def(input_name):
    return InputDefinition(
        input_name,
        input_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )


def create_root_success_solid(name):
    input_name = name + '_input'

    def root_transform(**kwargs):
        passed_rows = list(kwargs.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return Solid(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        outputs=[create_dummy_output_def()]
    )


def create_root_transform_failure_solid(name):
    input_name = name + '_input'
    inp = InputDefinition(
        input_name,
        input_fn=lambda context, arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )

    def failed_transform(**_kwargs):
        raise Exception('Transform failed')

    return Solid(
        name=name, inputs=[inp], transform_fn=failed_transform, outputs=[create_dummy_output_def()]
    )


def create_root_input_failure_solid(name):
    def failed_input_fn(**_kwargs):
        raise Exception('something bad happened')

    input_name = name + '_input'
    inp = InputDefinition(
        input_name,
        input_fn=failed_input_fn,
        argument_def_dict={},
    )

    return Solid(
        name=name,
        inputs=[inp],
        transform_fn=lambda **_kwargs: {},
        outputs=[create_dummy_output_def()]
    )


def create_root_output_failure_solid(name):
    input_name = name + '_input'

    def root_transform(**kwargs):
        passed_rows = list(kwargs.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return Solid(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        outputs=[create_failing_output_def()]
    )


def test_transform_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_transform_failure_solid('failing')])
    pipeline_result = execute_pipeline(
        create_test_context(), pipeline, {'failing_input': {}}, throw_on_error=False
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_input_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_input_failure_solid('failing_input')])
    pipeline_result = execute_pipeline(
        create_test_context(), pipeline, {'failing_input_input': {}}, throw_on_error=False
    )

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_output_failure_pipeline():
    pipeline = dagster.core.pipeline(solids=[create_root_output_failure_solid('failing_output')])

    pipeline_result = output_pipeline(
        create_test_context(),
        pipeline,
        input_arg_dicts={'failing_output_input': {}},
        output_arg_dicts={'failing_output': {
            'CUSTOM': {}
        }},
        throw_on_error=False,
    )

    assert not pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].exception


def test_failure_midstream():
    node_a = create_root_success_solid('A')
    node_b = create_root_success_solid('B')

    def not_reached_input(*_args, **_kwargs):
        check.failed('should not reach')

    def transform_fn(A, B):
        check.failed('user error')
        return [A, B, {'C': 'transform_called'}]

    solid = Solid(
        name='C',
        inputs=[
            InputDefinition(
                name='A', input_fn=not_reached_input, argument_def_dict={}, depends_on=node_a
            ),
            InputDefinition(
                name='B', input_fn=not_reached_input, argument_def_dict={}, depends_on=node_b
            ),
        ],
        transform_fn=transform_fn,
        outputs=[]
    )

    input_arg_dicts = {'A_input': {}, 'B_input': {}}
    pipeline_result = execute_pipeline(
        create_test_context(),
        dagster.core.pipeline(solids=[node_a, node_b, solid]),
        input_arg_dicts=input_arg_dicts,
        throw_on_error=False,
    )

    result_list = pipeline_result.result_list

    assert result_list[0].success
    assert result_list[1].success
    assert not result_list[2].success
    assert result_list[2].reason == DagsterExecutionFailureReason.USER_CODE_ERROR
