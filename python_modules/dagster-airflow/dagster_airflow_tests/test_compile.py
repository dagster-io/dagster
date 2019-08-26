from dagster_airflow.compile import coalesce_execution_steps
from dagster_examples.toys.composition import composition

from dagster import RunConfig
from dagster.core.execution.context_creation_pipeline import create_environment_config
from dagster.core.execution.plan.plan import ExecutionPlan


def test_compile():
    run_config = RunConfig()
    environment_config = create_environment_config(
        composition, {'solids': {'add_four': {'inputs': {'num': {'value': 1}}}}}, run_config=None
    )

    plan = ExecutionPlan.build(
        composition, environment_config, composition.get_mode_definition(run_config.mode)
    )

    res = coalesce_execution_steps(plan)

    assert set(res.keys()) == {
        'add_four.adder_1.adder_1',
        'add_four.adder_1.adder_2',
        'add_four.adder_2.adder_1',
        'add_four.adder_2.adder_2',
        'div_four.div_1',
        'div_four.div_2',
    }
