from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import EnvironmentConfig
from dagster_airflow.compile import coalesce_execution_steps
from dagster_test.toys.composition import composition


def test_compile():
    environment_config = EnvironmentConfig.build(
        composition,
        {"solids": {"add_four": {"inputs": {"num": {"value": 1}}}}},
    )

    plan = ExecutionPlan.build(InMemoryPipeline(composition), environment_config)

    res = coalesce_execution_steps(plan)
    assert set(res.keys()) == {
        "add_four.add",
        "div_four.div_two",
        "div_four.div_two_2",
        "add_four.emit_two.emit_one_2",
        "add_four.emit_two_2.add",
        "int_to_float",
        "add_four.emit_two_2.emit_one_2",
        "add_four.emit_two.add",
        "add_four.emit_two_2.emit_one",
        "add_four.emit_two.emit_one",
    }
