from dagster_airflow.compile import coalesce_execution_steps
from dagster_test.toys.composition import composition

from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.system_config.objects import ResolvedRunConfig


def test_compile():
    resolved_run_config = ResolvedRunConfig.build(
        composition.to_job(),
        {"solids": {"add_four": {"inputs": {"num": {"value": 1}}}}},
    )

    plan = ExecutionPlan.build(InMemoryPipeline(composition.to_job()), resolved_run_config)

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
