import pytest

from dagster import pipeline, solid
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.api import create_execution_plan

from ..engine_tests.test_multiprocessing import define_diamond_pipeline


def test_topological_sort():
    plan = create_execution_plan(define_diamond_pipeline())

    levels = plan.topological_step_levels()

    assert len(levels) == 3

    assert [step.key for step in levels[0]] == ['return_two.compute']
    assert [step.key for step in levels[1]] == ['add_three.compute', 'mult_three.compute']
    assert [step.key for step in levels[2]] == ['adder.compute']


def test_create_execution_plan_with_bad_inputs():
    with pytest.raises(DagsterInvalidConfigError):
        create_execution_plan(
            define_diamond_pipeline(), {'solids': {'add_three': {'inputs': {'num': 3}}}}
        )


def test_active_execution_plan():
    plan = create_execution_plan(define_diamond_pipeline())

    active_execution = plan.start()

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 1
    step_1 = steps[0]
    assert step_1.key == 'return_two.compute'

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    active_execution.mark_success(step_1.key)

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 2
    step_2 = steps[0]
    step_3 = steps[1]
    assert step_2.key == 'add_three.compute'
    assert step_3.key == 'mult_three.compute'

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    active_execution.mark_success(step_2.key)

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    active_execution.mark_success(step_3.key)

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 1
    step_4 = steps[0]

    assert step_4.key == 'adder.compute'

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    assert not active_execution.is_complete

    active_execution.mark_success(step_4.key)

    assert active_execution.is_complete


def test_failing_execution_plan():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    active_execution = plan.start()

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 1
    step_1 = steps[0]
    assert step_1.key == 'return_two.compute'

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    active_execution.mark_success(step_1.key)

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 2
    step_2 = steps[0]
    step_3 = steps[1]
    assert step_2.key == 'add_three.compute'
    assert step_3.key == 'mult_three.compute'

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    active_execution.mark_success(step_2.key)

    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0  # cant progress

    # uh oh failure
    active_execution.mark_failed(step_3.key)

    # cant progres to 4th step
    steps = active_execution.get_steps_to_execute()
    assert len(steps) == 0

    assert not active_execution.is_complete

    steps = active_execution.get_steps_to_skip()
    assert len(steps) == 1
    step_4 = steps[0]

    assert step_4.key == 'adder.compute'
    active_execution.mark_skipped(step_4.key)

    assert active_execution.is_complete


def test_priorities():
    @solid(tags={'priority': 5})
    def pri_5(_):
        pass

    @solid(tags={'priority': 4})
    def pri_4(_):
        pass

    @solid(tags={'priority': 3})
    def pri_3(_):
        pass

    @solid(tags={'priority': 2})
    def pri_2(_):
        pass

    @solid(tags={'priority': -1})
    def pri_neg_1(_):
        pass

    @solid
    def pri_none(_):
        pass

    @pipeline
    def priorities():
        pri_neg_1()
        pri_3()
        pri_2()
        pri_none()
        pri_5()
        pri_4()

    sort_key_fn = lambda step: int(step.tags.get('priority', 0)) * -1

    plan = create_execution_plan(priorities)
    active_execution = plan.start(sort_key_fn)
    steps = active_execution.get_steps_to_execute()
    assert steps[0].key == 'pri_5.compute'
    assert steps[1].key == 'pri_4.compute'
    assert steps[2].key == 'pri_3.compute'
    assert steps[3].key == 'pri_2.compute'
    assert steps[4].key == 'pri_none.compute'
    assert steps[5].key == 'pri_neg_1.compute'
