from dagster import Field, Int, String, job, op
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance import DagsterInstance


@op(config_schema={"foo": Field(String)})
def node_a(context):
    return context.op_config["foo"]


@op(config_schema={"bar": Int})
def node_b(context, input_):
    return input_ * context.op_config["bar"]


@graph
def graph_with_nested_config_graph():
    return node_b(node_a())


@job
def composite_job():
    graph_with_nested_config_graph()


@graph(
    config=ConfigMapping(
        config_schema={"foo": Field(String), "bar": Int},
        config_fn=lambda cfg: {
            "node_a": {"config": {"foo": cfg["foo"]}},
            "node_b": {"config": {"bar": cfg["bar"]}},
        },
    )
)
def graph_with_nested_config_graph_and_config_mapping():
    return node_b(node_a())


@job
def composite_job_with_config_mapping():
    graph_with_nested_config_graph_and_config_mapping()


def test_execution_plan_for_graph():
    run_config = {
        "ops": {
            "graph_with_nested_config_graph": {
                "ops": {
                    "node_a": {"config": {"foo": "baz"}},
                    "node_b": {"config": {"bar": 3}},
                }
            }
        }
    }
    execution_plan = create_execution_plan(composite_job, run_config=run_config)
    instance = DagsterInstance.ephemeral()
    dagster_run = instance.create_run_for_job(job_def=composite_job, execution_plan=execution_plan)
    events = execute_plan(
        execution_plan,
        InMemoryJob(composite_job),
        run_config=run_config,
        dagster_run=dagster_run,
        instance=instance,
    )

    assert [e.event_type_value for e in events] == [
        "RESOURCE_INIT_STARTED",
        "RESOURCE_INIT_SUCCESS",
        "LOGS_CAPTURED",
        "STEP_START",
        "STEP_OUTPUT",
        "HANDLED_OUTPUT",
        "STEP_SUCCESS",
        "STEP_START",
        "LOADED_INPUT",
        "STEP_INPUT",
        "STEP_OUTPUT",
        "HANDLED_OUTPUT",
        "STEP_SUCCESS",
    ]


def test_execution_plan_for_graph_with_config_mapping():
    run_config = {
        "ops": {
            "graph_with_nested_config_graph_and_config_mapping": {
                "config": {"foo": "baz", "bar": 3}
            }
        }
    }
    execution_plan = create_execution_plan(composite_job_with_config_mapping, run_config=run_config)
    instance = DagsterInstance.ephemeral()
    dagster_run = instance.create_run_for_job(
        job_def=composite_job_with_config_mapping,
        execution_plan=execution_plan,
    )

    events = execute_plan(
        execution_plan,
        InMemoryJob(composite_job_with_config_mapping),
        run_config=run_config,
        dagster_run=dagster_run,
        instance=instance,
    )

    assert [e.event_type_value for e in events] == [
        "RESOURCE_INIT_STARTED",
        "RESOURCE_INIT_SUCCESS",
        "LOGS_CAPTURED",
        "STEP_START",
        "STEP_OUTPUT",
        "HANDLED_OUTPUT",
        "STEP_SUCCESS",
        "STEP_START",
        "LOADED_INPUT",
        "STEP_INPUT",
        "STEP_OUTPUT",
        "HANDLED_OUTPUT",
        "STEP_SUCCESS",
    ]
