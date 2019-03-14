from dagster.core.execution import create_execution_plan
from .test_multiprocessing import define_diamond_pipeline


def test_topological_sort():
    plan = create_execution_plan(define_diamond_pipeline())

    levels = plan.topological_step_levels()

    assert len(levels) == 3

    assert [step.key for step in levels[0]] == ['return_two.transform']
    assert [step.key for step in levels[1]] == ['add_three.transform', 'mult_three.transform']
    assert [step.key for step in levels[2]] == ['adder.transform']
