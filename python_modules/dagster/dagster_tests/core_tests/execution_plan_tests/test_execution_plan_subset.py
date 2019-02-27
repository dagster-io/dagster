from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    ExecutionMetadata,
    lambda_solid,
    solid,
    types,
)

from dagster.core.execution import create_execution_plan, execute_plan, ExecutionPlanSubsetInfo

from dagster.core.execution_plan.utility import VALUE_OUTPUT


def define_two_int_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num')])
    def add_one(num):
        return num + 1

    return PipelineDefinition(
        name='pipeline_ints',
        solids=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )


def test_execution_plan_simple_two_steps():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(pipeline_def)

    assert isinstance(execution_plan.steps, list)
    assert len(execution_plan.steps) == 2

    assert execution_plan.get_step_by_key('return_one.transform')
    assert execution_plan.get_step_by_key('add_one.transform')

    step_events = execute_plan(execution_plan)
    assert len(step_events) == 2

    assert step_events[0].step.key == 'return_one.transform'
    assert step_events[0].is_successful_output
    assert step_events[0].step_output_data.get_value() == 1

    assert step_events[1].step.key == 'add_one.transform'
    assert step_events[1].is_successful_output
    assert step_events[1].step_output_data.get_value() == 2


def test_create_subplan_source_step():
    subplan = create_execution_plan(
        define_two_int_pipeline(),
        subset_info=ExecutionPlanSubsetInfo.only_subset(['return_one.transform']),
    )
    assert subplan
    assert len(subplan.steps) == 1
    assert subplan.steps[0].key == 'return_one.transform'
    assert not subplan.steps[0].step_inputs
    assert len(subplan.steps[0].step_outputs) == 1
    assert len(subplan.topological_steps()) == 1


def test_create_subplan_middle_step():
    subplan = create_execution_plan(
        define_two_int_pipeline(),
        subset_info=ExecutionPlanSubsetInfo.with_input_values(
            ['add_one.transform'], {'add_one.transform': {'num': 2}}
        ),
    )
    assert subplan
    steps = subplan.topological_steps()
    assert len(steps) == 2
    assert steps[0].key == 'add_one.transform.input.num.value'
    assert not steps[0].step_inputs
    assert len(steps[0].step_outputs) == 1
    assert steps[1].key == 'add_one.transform'
    assert len(steps[1].step_inputs) == 1
    step_input = steps[1].step_inputs[0]
    assert step_input.prev_output_handle.step_key == 'add_one.transform.input.num.value'
    assert step_input.prev_output_handle.output_name == VALUE_OUTPUT
    assert len(steps[1].step_outputs) == 1
    assert len(subplan.topological_steps()) == 2
    assert [step.key for step in subplan.topological_steps()] == [
        'add_one.transform.input.num.value',
        'add_one.transform',
    ]


def test_execution_plan_source_step():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(
        pipeline_def,
        subset_info=ExecutionPlanSubsetInfo.only_subset(
            included_step_keys=['return_one.transform']
        ),
    )
    step_events = execute_plan(execution_plan)

    assert len(step_events) == 1
    assert step_events[0].step_output_data.get_value() == 1


def test_execution_plan_middle_step():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(
        pipeline_def,
        subset_info=ExecutionPlanSubsetInfo.with_input_values(
            ['add_one.transform'], {'add_one.transform': {'num': 2}}
        ),
    )

    step_events = execute_plan(execution_plan)

    assert len(step_events) == 2
    assert step_events[1].step_output_data.get_value() == 3


def test_execution_plan_two_outputs():
    @solid(outputs=[OutputDefinition(types.Int, 'num_one'), OutputDefinition(types.Int, 'num_two')])
    def return_one_two(_context):
        yield Result(1, 'num_one')
        yield Result(2, 'num_two')

    pipeline_def = PipelineDefinition(name='return_one_two_pipeline', solids=[return_one_two])

    execution_plan = create_execution_plan(pipeline_def)

    step_events = execute_plan(execution_plan)

    assert step_events[0].step.key == 'return_one_two.transform'
    assert step_events[0].step_output_data.get_value() == 1
    assert step_events[0].step_output_data.output_name == 'num_one'
    assert step_events[1].step.key == 'return_one_two.transform'
    assert step_events[1].step_output_data.get_value() == 2
    assert step_events[1].step_output_data.output_name == 'num_two'


def test_reentrant_execute_plan():
    called = {}

    @solid
    def has_tag(context):
        assert context.has_tag('foo')
        assert context.get_tag('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='has_tag_pipeline', solids=[has_tag])
    execution_plan = create_execution_plan(pipeline_def)

    step_events = execute_plan(
        execution_plan, execution_metadata=ExecutionMetadata(tags={'foo': 'bar'})
    )

    assert called['yup']
    assert len(step_events) == 1
