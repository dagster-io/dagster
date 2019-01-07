from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    ReentrantInfo,
    lambda_solid,
    solid,
    types,
)

from dagster.core.execution import (
    create_subplan,
    create_execution_plan,
    execute_plan,
    create_typed_environment,
    ExecutionPlanInfo,
    ExecutionPlanSubsetInfo,
    yield_context,
)

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

    step_results = execute_plan(pipeline_def, execution_plan)
    assert len(step_results) == 2

    assert step_results[0].step.key == 'return_one.transform'
    assert step_results[0].success
    assert step_results[0].success_data.value == 1

    assert step_results[1].step.key == 'add_one.transform'
    assert step_results[1].success
    assert step_results[1].success_data.value == 2


def test_create_subplan_source_step():
    pipeline_def = define_two_int_pipeline()
    typed_environment = create_typed_environment(pipeline_def, None)
    execution_plan = create_execution_plan(pipeline_def)
    with yield_context(pipeline_def, typed_environment) as context:
        subplan = create_subplan(
            ExecutionPlanInfo(
                context=context, pipeline=pipeline_def, environment=typed_environment
            ),
            execution_plan,
            ExecutionPlanSubsetInfo(['return_one.transform']),
        )
        assert subplan
        assert len(subplan.steps) == 1
        assert subplan.steps[0].key == 'return_one.transform'
        assert not subplan.steps[0].step_inputs
        assert len(subplan.steps[0].step_outputs) == 1
        assert len(subplan.topological_steps()) == 1


def test_create_subplan_middle_step():
    pipeline_def = define_two_int_pipeline()
    typed_environment = create_typed_environment(pipeline_def, None)
    execution_plan = create_execution_plan(pipeline_def)
    with yield_context(pipeline_def, typed_environment) as context:
        subplan = create_subplan(
            ExecutionPlanInfo(
                context=context, pipeline=pipeline_def, environment=typed_environment
            ),
            execution_plan,
            ExecutionPlanSubsetInfo(['add_one.transform'], {'add_one.transform': {'num': 2}}),
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
        assert step_input.prev_output_handle.step.key == 'add_one.transform.input.num.value'
        assert step_input.prev_output_handle.output_name == VALUE_OUTPUT
        assert len(steps[1].step_outputs) == 1
        assert len(subplan.topological_steps()) == 2
        assert [step.key for step in subplan.topological_steps()] == [
            'add_one.transform.input.num.value',
            'add_one.transform',
        ]


def test_execution_plan_source_step():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(pipeline_def)
    step_results = execute_plan(
        pipeline_def,
        execution_plan,
        subset_info=ExecutionPlanSubsetInfo(included_steps=['return_one.transform']),
    )

    assert len(step_results) == 1
    assert step_results[0].success_data.value == 1


def test_execution_plan_middle_step():
    pipeline_def = define_two_int_pipeline()
    execution_plan = create_execution_plan(pipeline_def)
    step_results = execute_plan(
        pipeline_def,
        execution_plan,
        subset_info=ExecutionPlanSubsetInfo(
            ['add_one.transform'], {'add_one.transform': {'num': 2}}
        ),
    )

    assert len(step_results) == 2
    assert step_results[1].success_data.value == 3


def test_execution_plan_two_outputs():
    @solid(outputs=[OutputDefinition(types.Int, 'num_one'), OutputDefinition(types.Int, 'num_two')])
    def return_one_two(_info):
        yield Result(1, 'num_one')
        yield Result(2, 'num_two')

    pipeline_def = PipelineDefinition(name='return_one_two_pipeline', solids=[return_one_two])

    execution_plan = create_execution_plan(pipeline_def)

    step_results = execute_plan(pipeline_def, execution_plan)

    # FIXME: we should change this to be *single* result with two outputs
    assert step_results[0].step.key == 'return_one_two.transform'
    assert step_results[0].success_data.value == 1
    assert step_results[0].success_data.output_name == 'num_one'
    assert step_results[1].step.key == 'return_one_two.transform'
    assert step_results[1].success_data.value == 2
    assert step_results[1].success_data.output_name == 'num_two'


def test_reentrant_execute_plan():
    called = {}

    @solid
    def has_context_value(info):
        assert info.context.has_context_value('foo')
        assert info.context.get_context_value('foo') == 'bar'
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='has_context_value_pipeline', solids=[has_context_value])
    execution_plan = create_execution_plan(pipeline_def)

    step_results = execute_plan(
        pipeline_def, execution_plan, reentrant_info=ReentrantInfo(context_stack={'foo': 'bar'})
    )

    assert called['yup']
    assert len(step_results) == 1
