import pytest

from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import DagsterInvalidConfigError
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
