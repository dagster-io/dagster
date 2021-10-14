import pytest
from dagster import (
    DagsterInstance,
    DynamicOutput,
    DynamicOutputDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineRun,
    build_input_context,
    build_output_context,
    graph,
    op,
    resource,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import execute_plan
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.utils import make_new_run_id
from dagster_azure.adls2 import create_adls2_client
from dagster_azure.adls2.io_manager import PickledObjectADLS2IOManager, adls2_pickle_io_manager
from dagster_azure.adls2.resources import adls2_resource
from dagster_azure.blob import create_blob_client


def fake_io_manager_factory(io_manager):
    @resource
    def fake_io_manager(_):
        return io_manager

    return fake_io_manager


def get_step_output(step_events, step_key, output_name="result"):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def define_inty_job():
    @op(output_defs=[OutputDefinition(Int)])
    def return_one():
        return 1

    @op(
        input_defs=[InputDefinition("num", Int)],
        output_defs=[DynamicOutputDefinition(Int)],
    )
    def add_one(num):
        yield DynamicOutput(num + 1, "foo")
        yield DynamicOutput(num + 1, "bar")

    @graph
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution.to_job(
        resource_defs={"io_manager": adls2_pickle_io_manager, "adls2": adls2_resource}
    )


nettest = pytest.mark.nettest


@nettest
def test_adls2_pickle_io_manager_execution(storage_account, file_system, credential):
    job = define_inty_job()

    run_config = {
        "resources": {
            "io_manager": {"config": {"adls2_file_system": file_system}},
            "adls2": {
                "config": {"storage_account": storage_account, "credential": {"key": credential}}
            },
        }
    }

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(job, run_config=run_config)
    execution_plan = ExecutionPlan.build(InMemoryPipeline(job), resolved_run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(pipeline_name=job.name, run_id=run_id, run_config=run_config)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, job, resolved_run_config),
            pipeline=InMemoryPipeline(job),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key="return_one",
            name="result",
            run_id=run_id,
        )
    )

    io_manager = PickledObjectADLS2IOManager(
        file_system=file_system,
        adls2_client=create_adls2_client(storage_account, credential),
        blob_client=create_blob_client(storage_account, credential),
    )
    assert io_manager.load_input(context) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], job, resolved_run_config),
            pipeline=InMemoryPipeline(job),
            pipeline_run=pipeline_run,
            run_config=run_config,
            instance=instance,
        )
    )

    context = build_input_context(
        upstream_output=build_output_context(
            step_key="add_one",
            name="result",
            run_id=run_id,
            mapping_key="foo",
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    assert io_manager.load_input(context) == 2
