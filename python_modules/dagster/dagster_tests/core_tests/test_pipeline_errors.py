import sys

import pytest

from dagster import (
    DagsterExecutionStepExecutionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    EventMetadataEntry,
    Failure,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    SolidDefinition,
    check,
    execute_pipeline,
    lambda_solid,
    pipeline,
)

from dagster.core.test_utils import single_output_solid


def create_root_success_solid(name):
    def root_fn(_context, _args):
        passed_rows = []
        passed_rows.append({name: 'compute_called'})
        return passed_rows

    return single_output_solid(
        name=name, input_defs=[], compute_fn=root_fn, output_def=OutputDefinition()
    )


def create_root_fn_failure_solid(name):
    def failed_fn(**_kwargs):
        raise Exception('Compute failed')

    return single_output_solid(
        name=name, input_defs=[], compute_fn=failed_fn, output_def=OutputDefinition()
    )


def test_compute_failure_pipeline():
    pipeline_def = PipelineDefinition(solid_defs=[create_root_fn_failure_solid('failing')])
    pipeline_result = execute_pipeline(pipeline_def, run_config=RunConfig.nonthrowing_in_process())

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
        return [inputs['A'], inputs['B'], {'C': 'compute_called'}]

    def success_fn(_context, inputs):
        return [inputs['C'], {'D': 'compute_called'}]

    solid_c = single_output_solid(
        name='C',
        input_defs=[InputDefinition(name='A'), InputDefinition(name='B')],
        compute_fn=fail_fn,
        output_def=OutputDefinition(),
    )

    solid_d = single_output_solid(
        name='D',
        input_defs=[InputDefinition(name='C')],
        compute_fn=success_fn,
        output_def=OutputDefinition(),
    )

    pipeline_def = PipelineDefinition(
        solid_defs=[solid_a, solid_b, solid_c, solid_d],
        dependencies={
            'C': {'A': DependencyDefinition(solid_a.name), 'B': DependencyDefinition(solid_b.name)},
            'D': {'C': DependencyDefinition(solid_c.name)},
        },
    )
    pipeline_result = execute_pipeline(pipeline_def, run_config=RunConfig.nonthrowing_in_process())

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

    solid_b = single_output_solid(
        name='B',
        input_defs=[InputDefinition(name='A')],
        compute_fn=success_fn,
        output_def=OutputDefinition(),
    )

    solid_c = single_output_solid(
        name='C',
        input_defs=[InputDefinition(name='B')],
        compute_fn=success_fn,
        output_def=OutputDefinition(),
    )

    solid_d = single_output_solid(
        name='D',
        input_defs=[InputDefinition(name='A')],
        compute_fn=fail_fn,
        output_def=OutputDefinition(),
    )

    solid_e = single_output_solid(
        name='E',
        input_defs=[InputDefinition(name='D')],
        compute_fn=success_fn,
        output_def=OutputDefinition(),
    )

    solid_f = single_output_solid(
        name='F',
        input_defs=[InputDefinition(name='C'), InputDefinition(name='E')],
        compute_fn=success_fn,
        output_def=OutputDefinition(),
    )

    pipeline_def = PipelineDefinition(
        solid_defs=[solid_a, solid_b, solid_c, solid_d, solid_e, solid_f],
        dependencies={
            'B': {'A': DependencyDefinition(solid_a.name)},
            'D': {'A': DependencyDefinition(solid_a.name)},
            'C': {'B': DependencyDefinition(solid_b.name)},
            'E': {'D': DependencyDefinition(solid_d.name)},
            'F': {'C': DependencyDefinition(solid_c.name), 'E': DependencyDefinition(solid_e.name)},
        },
    )

    pipeline_result = execute_pipeline(pipeline_def, run_config=RunConfig.nonthrowing_in_process())

    assert pipeline_result.result_for_solid('A').success
    assert pipeline_result.result_for_solid('B').success
    assert pipeline_result.result_for_solid('C').success
    assert not pipeline_result.result_for_solid('D').success
    assert pipeline_result.result_for_solid('D').failure_data.error.cls_name == 'CheckError'
    assert not pipeline_result.result_for_solid('E').success
    assert pipeline_result.result_for_solid('E').skipped
    assert not pipeline_result.result_for_solid('F').success
    assert pipeline_result.result_for_solid('F').skipped


def execute_isolated_solid(solid_def, environment_dict=None):
    return execute_pipeline(
        PipelineDefinition(name='test', solid_defs=[solid_def]), environment_dict=environment_dict
    )


def test_do_not_yield_result():
    solid_inst = SolidDefinition(
        name='do_not_yield_result',
        input_defs=[],
        output_defs=[OutputDefinition()],
        compute_fn=lambda *_args, **_kwargs: Output('foo'),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute function for solid do_not_yield_result returned a Output',
    ):
        execute_isolated_solid(solid_inst)


def test_yield_non_result():
    def _tn(*_args, **_kwargs):
        yield 'foo'

    solid_inst = SolidDefinition(
        name='yield_wrong_thing', input_defs=[], output_defs=[OutputDefinition()], compute_fn=_tn
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Compute function for solid yield_wrong_thing yielded 'foo'",
    ):
        execute_isolated_solid(solid_inst)


def test_single_compute_fn_returning_result():
    solid_inst = single_output_solid(
        'test_return_result',
        input_defs=[],
        compute_fn=lambda *_args, **_kwargs: Output(None),
        output_def=OutputDefinition(),
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_isolated_solid(solid_inst)


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

    @lambda_solid(input_defs=[InputDefinition('num')])
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='test_user_error_propogation',
        solid_defs=[throws_user_error, return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_pipeline(pipeline_def)

    assert isinstance(e_info.value.__cause__, UserError)
    # meta data on the exception
    assert e_info.value.step_key == 'throws_user_error.compute'
    assert e_info.value.solid_name == 'throws_user_error'
    assert e_info.value.solid_def_name == 'throws_user_error'

    # and in the message
    assert 'step key: "throws_user_error.compute"' in str(e_info.value)
    assert 'solid invocation: "throws_user_error"' in str(e_info.value)
    assert 'solid definition: "throws_user_error"' in str(e_info.value)

    # ensure that the inner exception shows up in the error message on python 2
    if sys.version_info[0] == 2:
        assert err_msg in str(e_info.value)


def test_explicit_failure():
    @lambda_solid
    def throws_failure():
        raise Failure(
            description='Always fails.',
            metadata_entries=[EventMetadataEntry.text('why', label='always_fails')],
        )

    @pipeline
    def pipe():
        throws_failure()

    with pytest.raises(DagsterExecutionStepExecutionError) as exc_info:
        execute_pipeline(pipe)

    assert exc_info.value.user_specified_failure.description == 'Always fails.'
    assert exc_info.value.user_specified_failure.metadata_entries == [
        EventMetadataEntry.text('why', label='always_fails')
    ]
