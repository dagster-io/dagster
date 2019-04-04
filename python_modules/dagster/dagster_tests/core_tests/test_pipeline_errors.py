import pytest
import sys

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    Result,
    RunConfig,
    SolidDefinition,
    check,
    execute_pipeline,
    lambda_solid,
)

from dagster.core.test_utils import execute_single_solid_in_isolation, single_output_transform
from dagster.core.errors import DagsterExecutionStepExecutionError


def silencing_default_context():
    return {'default': PipelineContextDefinition(context_fn=lambda *_args: ExecutionContext())}


def silencing_pipeline(solids, dependencies=None):
    return PipelineDefinition(
        solids=solids, dependencies=dependencies, context_definitions=silencing_default_context()
    )


def create_root_success_solid(name):
    def root_transform(_context, _args):
        passed_rows = []
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return single_output_transform(
        name=name, inputs=[], transform_fn=root_transform, output=OutputDefinition()
    )


def create_root_transform_failure_solid(name):
    def failed_transform(**_kwargs):
        raise Exception('Transform failed')

    return single_output_transform(
        name=name, inputs=[], transform_fn=failed_transform, output=OutputDefinition()
    )


def test_transform_failure_pipeline():
    pipeline = silencing_pipeline(solids=[create_root_transform_failure_solid('failing')])
    pipeline_result = execute_pipeline(pipeline, run_config=RunConfig.nonthrowing_in_process())

    assert not pipeline_result.success

    result_list = pipeline_result.solid_result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].failure_data


def test_failure_midstream():
    '''
    A
     \\
       C (fails) = D (skipped)
     //
    B
    '''

    solid_a = create_root_success_solid('A')
    solid_b = create_root_success_solid('B')

    def fail_fn(_context, inputs):
        check.failed('user error')
        return [inputs['A'], inputs['B'], {'C': 'transform_called'}]

    def success_fn(_context, inputs):
        return [inputs['C'], {'D': 'transform_called'}]

    solid_c = single_output_transform(
        name='C',
        inputs=[InputDefinition(name='A'), InputDefinition(name='B')],
        transform_fn=fail_fn,
        output=OutputDefinition(),
    )

    solid_d = single_output_transform(
        name='D',
        inputs=[InputDefinition(name='C')],
        transform_fn=success_fn,
        output=OutputDefinition(),
    )

    pipeline = silencing_pipeline(
        solids=[solid_a, solid_b, solid_c, solid_d],
        dependencies={
            'C': {'A': DependencyDefinition(solid_a.name), 'B': DependencyDefinition(solid_b.name)},
            'D': {'C': DependencyDefinition(solid_c.name)},
        },
    )
    pipeline_result = execute_pipeline(pipeline, run_config=RunConfig.nonthrowing_in_process())

    assert pipeline_result.result_for_solid('A').success
    assert pipeline_result.result_for_solid('B').success
    assert not pipeline_result.result_for_solid('C').success
    assert pipeline_result.result_for_solid('C').failure_data.error.cls_name == 'CheckError'
    assert not pipeline_result.result_for_solid('D').success
    assert pipeline_result.result_for_solid('D').skipped


def test_failure_propagation():
    '''
      B =========== C
     //             \\
    A                F (skipped)
     \\             //
      D (fails) == E (skipped)
    '''

    solid_a = create_root_success_solid('A')

    def fail_fn(_context, inputs):
        check.failed('user error')
        return inputs

    def success_fn(_context, inputs):
        return inputs

    solid_b = single_output_transform(
        name='B',
        inputs=[InputDefinition(name='A')],
        transform_fn=success_fn,
        output=OutputDefinition(),
    )

    solid_c = single_output_transform(
        name='C',
        inputs=[InputDefinition(name='B')],
        transform_fn=success_fn,
        output=OutputDefinition(),
    )

    solid_d = single_output_transform(
        name='D',
        inputs=[InputDefinition(name='A')],
        transform_fn=fail_fn,
        output=OutputDefinition(),
    )

    solid_e = single_output_transform(
        name='E',
        inputs=[InputDefinition(name='D')],
        transform_fn=success_fn,
        output=OutputDefinition(),
    )

    solid_f = single_output_transform(
        name='F',
        inputs=[InputDefinition(name='C'), InputDefinition(name='E')],
        transform_fn=success_fn,
        output=OutputDefinition(),
    )

    pipeline = silencing_pipeline(
        solids=[solid_a, solid_b, solid_c, solid_d, solid_e, solid_f],
        dependencies={
            'B': {'A': DependencyDefinition(solid_a.name)},
            'D': {'A': DependencyDefinition(solid_a.name)},
            'C': {'B': DependencyDefinition(solid_b.name)},
            'E': {'D': DependencyDefinition(solid_d.name)},
            'F': {'C': DependencyDefinition(solid_c.name), 'E': DependencyDefinition(solid_e.name)},
        },
    )

    pipeline_result = execute_pipeline(pipeline, run_config=RunConfig.nonthrowing_in_process())

    assert pipeline_result.result_for_solid('A').success
    assert pipeline_result.result_for_solid('B').success
    assert pipeline_result.result_for_solid('C').success
    assert not pipeline_result.result_for_solid('D').success
    assert pipeline_result.result_for_solid('D').failure_data.error.cls_name == 'CheckError'
    assert not pipeline_result.result_for_solid('E').success
    assert pipeline_result.result_for_solid('E').skipped
    assert not pipeline_result.result_for_solid('F').success
    assert pipeline_result.result_for_solid('F').skipped


def test_do_not_yield_result():
    solid_inst = SolidDefinition(
        name='do_not_yield_result',
        inputs=[],
        outputs=[OutputDefinition()],
        transform_fn=lambda *_args, **_kwargs: Result('foo'),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Transform for solid do_not_yield_result returned a Result',
    ):
        execute_single_solid_in_isolation(ExecutionContext(), solid_inst)


def test_yield_non_result():
    def _tn(*_args, **_kwargs):
        yield 'foo'

    solid_inst = SolidDefinition(
        name='yield_wrong_thing', inputs=[], outputs=[OutputDefinition()], transform_fn=_tn
    )

    with pytest.raises(
        DagsterInvariantViolationError, match="Transform for solid yield_wrong_thing yielded 'foo'"
    ):
        execute_single_solid_in_isolation(ExecutionContext(), solid_inst)


def test_single_transform_returning_result():
    solid_inst = single_output_transform(
        'test_return_result',
        inputs=[],
        transform_fn=lambda *_args, **_kwargs: Result(None),
        output=OutputDefinition(),
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid_in_isolation(ExecutionContext(), solid_inst)


def test_user_error_propogation():
    err_msg = 'the user has errored'

    class UserError(Exception):
        pass

    @lambda_solid
    def throws_user_error():
        raise UserError(err_msg)

    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num')])
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='test_user_error_propogation',
        solids=[throws_user_error, return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_pipeline(pipeline_def)

    assert isinstance(e_info.value.__cause__, UserError)
    # meta data on the exception
    assert e_info.value.step_key == 'throws_user_error.transform'
    assert e_info.value.solid_name == 'throws_user_error'
    assert e_info.value.solid_def_name == 'throws_user_error'

    # and in the message
    assert 'step key: "throws_user_error.transform"' in str(e_info.value)
    assert 'solid instance: "throws_user_error"' in str(e_info.value)
    assert 'solid definition: "throws_user_error"' in str(e_info.value)

    # ensure that the inner exception shows up in the error message on python 2
    if sys.version_info[0] == 2:
        assert err_msg in str(e_info.value)
