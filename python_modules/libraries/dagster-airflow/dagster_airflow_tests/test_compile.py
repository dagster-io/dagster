from dagster_airflow.compile import coalesce_execution_steps
from dagster_examples.toys.composition import composition

from dagster import PipelineRun
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import EnvironmentConfig


def test_compile():
    pipeline_run = PipelineRun()
    environment_config = EnvironmentConfig.build(
        composition,
        {'solids': {'add_four': {'inputs': {'num': {'value': 1}}}}},
        pipeline_run=pipeline_run,
    )

    plan = ExecutionPlan.build(composition, environment_config, pipeline_run)

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
