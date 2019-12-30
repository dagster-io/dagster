from dagster_airflow.compile import coalesce_execution_steps
from dagster_examples.toys.composition import composition

from dagster import RunConfig
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import EnvironmentConfig


def test_compile():
    run_config = RunConfig()
    environment_config = EnvironmentConfig.build(
        composition, {'solids': {'add_four': {'inputs': {'num': {'value': 1}}}}}, run_config=None
    )

    plan = ExecutionPlan.build(composition, environment_config, run_config)

    res = coalesce_execution_steps(plan)

    assert set(res.keys()) == {
        'add_four.add_two.add_one',
        'add_four.add_two.add_one_2',
        'add_four.add_two_2.add_one',
        'add_four.add_two_2.add_one_2',
        'div_four.div_two',
        'div_four.div_two_2',
        'int_to_float',
    }
