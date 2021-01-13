from dagster import (
    DagsterInstance,
    InputContext,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputContext,
    OutputDefinition,
    PipelineRun,
    lambda_solid,
    pipeline,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.log_manager import DagsterLogManager
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


def define_inty_pipeline():
    @lambda_solid(output_def=OutputDefinition(Int, io_manager_key="io_manager"))
    def return_one():
        return 1

    @lambda_solid(
        input_defs=[InputDefinition("num", Int)],
        output_def=OutputDefinition(Int, io_manager_key="io_manager"),
    )
    def add_one(num):
        return num + 1

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"io_manager": gcs_pickle_io_manager, "gcs": gcs_resource},
            )
        ]
    )
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_gcs_pickle_io_manager_execution(gcs_bucket):
    pipeline_def = define_inty_pipeline()

    run_config = {"resources": {"io_manager": {"config": {"gcs_bucket": gcs_bucket,}}}}

    run_id = make_new_run_id()

    execution_plan = create_execution_plan(pipeline_def, run_config=run_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name, run_id=run_id, run_config=run_config
    )

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")

    io_manager = PickledObjectGCSIOManager(gcs_bucket, storage.Client())
    step_output_handle = StepOutputHandle("return_one")
    context = InputContext(
        pipeline_name=pipeline_def.name,
        solid_def=pipeline_def.solid_def_named("return_one"),
        upstream_output=OutputContext(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            solid_def=pipeline_def.solid_def_named("return_one"),
        ),
        log_manager=DagsterLogManager(run_id=pipeline_run.run_id, logging_tags={}, loggers=[]),
    )
    assert io_manager.load_input(context) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"]),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    step_output_handle = StepOutputHandle("add_one")
    context = InputContext(
        pipeline_name=pipeline_def.name,
        solid_def=pipeline_def.solid_def_named("add_one"),
        upstream_output=OutputContext(
            step_key=step_output_handle.step_key,
            name=step_output_handle.output_name,
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            solid_def=pipeline_def.solid_def_named("add_one"),
        ),
        log_manager=DagsterLogManager(run_id=pipeline_run.run_id, logging_tags={}, loggers=[]),
    )

    assert get_step_output(add_one_step_events, "add_one")
    assert io_manager.load_input(context) == 2
