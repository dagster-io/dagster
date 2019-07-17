from dagster import (
    DagsterEventType,
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    Output,
    RunConfig,
    lambda_solid,
    solid,
)

from dagster.core.execution.api import create_execution_plan, execute_plan


def define_two_int_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('num')])
    def add_one(num):
        return num + 1

    return PipelineDefinition(
        name='pipeline_ints',
        solid_defs=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )


def test_execution_plan_simple_two_steps():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(pipeline_def)

    assert isinstance(execution_plan.steps, list)
    assert len(execution_plan.steps) == 2

    assert execution_plan.get_step_by_key('return_one.compute')
    assert execution_plan.get_step_by_key('add_one.compute')

    step_events = execute_plan(execution_plan)
    # start, out, success, start, input, out, success
    assert len(step_events) == 7

    assert step_events[1].step_key == 'return_one.compute'
    assert step_events[1].is_successful_output

    assert step_events[2].event_type == DagsterEventType.STEP_SUCCESS
    assert step_events[3].event_type == DagsterEventType.STEP_START
    assert step_events[4].event_type == DagsterEventType.STEP_INPUT

    assert step_events[5].step_key == 'add_one.compute'
    assert step_events[5].is_successful_output


def test_execution_plan_two_outputs():
    @solid(output_defs=[OutputDefinition(Int, 'num_one'), OutputDefinition(Int, 'num_two')])
    def return_one_two(_context):
        yield Output(1, 'num_one')
        yield Output(2, 'num_two')

    pipeline_def = PipelineDefinition(name='return_one_two_pipeline', solid_defs=[return_one_two])

    execution_plan = create_execution_plan(pipeline_def)

    step_events = execute_plan(execution_plan)

    assert step_events[1].step_key == 'return_one_two.compute'
    assert step_events[1].step_output_data.output_name == 'num_one'
    assert step_events[2].step_key == 'return_one_two.compute'
    assert step_events[2].step_output_data.output_name == 'num_two'


def test_reentrant_execute_plan():
    called = {}

    @solid
    def has_tag(context):
        assert context.has_tag('foo')
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='has_tag_pipeline', solid_defs=[has_tag])
    execution_plan = create_execution_plan(pipeline_def)

    step_events = execute_plan(execution_plan, run_config=RunConfig(tags={'foo': 'bar'}))

    assert called['yup']
    assert len(step_events) == 3

    assert step_events[0].logging_tags['foo'] == 'bar'
