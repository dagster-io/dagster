from dagster import (
    DagsterInstance,
    DynamicOut,
    DynamicOutput,
    In,
    Int,
    Out,
    PipelineRun,
    build_input_context,
    build_output_context,
    job,
    op,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import execute_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.utils import make_new_run_id
from dagster_gcp.gcs.io_manager import PickledObjectGCSIOManager, gcs_pickle_io_manager
from dagster_gcp.gcs.resources import gcs_resource
from google.cloud import storage


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
    @op(out=Out(Int, io_manager_key="io_manager"))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=Out(Int, io_manager_key="io_manager"),
    )
    def add_one(num):
        return num + 1

    @job(resource_defs={"io_manager": gcs_pickle_io_manager, "gcs": gcs_resource})
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_gcs_pickle_io_manager_execution(gcs_bucket):
    inty_job = define_inty_job()

    run_config = {
        "resources": {
            "io_manager": {
                "config": {
                    "gcs_bucket": gcs_bucket,
                }
            }
        }
    }

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(inty_job, run_config=run_config)
    execution_plan = ExecutionPlan.build(InMemoryPipeline(inty_job), resolved_run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(pipeline_name=inty_job.name, run_id=run_id, run_config=run_config)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, inty_job, resolved_run_config),
            pipeline=InMemoryPipeline(inty_job),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")

    io_manager = PickledObjectGCSIOManager(gcs_bucket, storage.Client())
    step_output_handle = StepOutputHandle("return_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            run_id=run_id,
        )
    )
    assert io_manager.load_input(context) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], inty_job, resolved_run_config),
            pipeline=InMemoryPipeline(inty_job),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    step_output_handle = StepOutputHandle("add_one")
    context = build_input_context(
        upstream_output=build_output_context(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            run_id=run_id,
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    assert io_manager.load_input(context) == 2


def test_dynamic(gcs_bucket):
    @op(out=DynamicOut())
    def numbers():
        for i in range(3):
            yield DynamicOutput(i, mapping_key=str(i))

    @op
    def echo(_, x):
        return x

    @job(resource_defs={"io_manager": gcs_pickle_io_manager, "gcs": gcs_resource})
    def dynamic():
        numbers().map(echo)  # pylint: disable=no-member

    result = dynamic.execute_in_process(
        run_config={"resources": {"io_manager": {"config": {"gcs_bucket": gcs_bucket}}}}
    )
    assert result.success
