import copy

import check

import solidic
from solidic.definitions import (Solid, SolidInputDefinition, SolidOutputDefinition)
from solidic.execution import (
    SolidExecutionContext, output_pipeline, OutputConfig, SolidExecutionFailureReason,
    execute_pipeline_and_collect
)


def create_test_context():
    return SolidExecutionContext()


def create_dummy_output_def():
    return SolidOutputDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )


def create_failing_output_def():
    def failing_output_fn(*_args, **_kwargs):
        raise Exception('something bad happened')

    return SolidOutputDefinition(
        name='CUSTOM',
        output_fn=failing_output_fn,
        argument_def_dict={},
    )


def create_input_set_input_def(input_name):
    return SolidInputDefinition(
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
    inp = SolidInputDefinition(
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
    inp = SolidInputDefinition(
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
    pipeline = solidic.pipeline(solids=[create_root_transform_failure_solid('failing')])
    results = execute_pipeline_and_collect(create_test_context(), pipeline, {'failing_input': {}})

    assert len(results) == 1
    assert not results[0].success
    assert results[0].exception


def test_input_failure_pipeline():
    pipeline = solidic.pipeline(solids=[create_root_input_failure_solid('failing_input')])
    results = execute_pipeline_and_collect(
        create_test_context(), pipeline, {'failing_input_input': {}}
    )

    assert len(results) == 1
    assert not results[0].success
    assert results[0].exception


def test_output_failure_pipeline():
    pipeline = solidic.pipeline(solids=[create_root_output_failure_solid('failing_output')])

    results = []
    for result in output_pipeline(
        create_test_context(),
        pipeline,
        input_arg_dicts={'failing_output_input': {}},
        output_configs=[OutputConfig(name='failing_output', output_type='CUSTOM', output_args={})]
    ):
        results.append(copy.deepcopy(result))

    assert len(results) == 1
    assert not results[0].success
    assert results[0].exception


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
            SolidInputDefinition(
                name='A', input_fn=not_reached_input, argument_def_dict={}, depends_on=node_a
            ),
            SolidInputDefinition(
                name='B', input_fn=not_reached_input, argument_def_dict={}, depends_on=node_b
            ),
        ],
        transform_fn=transform_fn,
        outputs=[]
    )

    input_arg_dicts = {'A_input': {}, 'B_input': {}}
    results = execute_pipeline_and_collect(
        create_test_context(),
        solidic.pipeline(solids=[node_a, node_b, solid]),
        input_arg_dicts=input_arg_dicts,
    )

    assert results[0].success
    assert results[1].success
    assert not results[2].success
    assert results[2].reason == SolidExecutionFailureReason.USER_CODE_ERROR
