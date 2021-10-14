from dagster import (
    DagsterInstance,
    In,
    Int,
    Out,
    PipelineRun,
    build_input_context,
    build_output_context,
    job,
    op,
    resource,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import execute_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.utils import make_new_run_id
from dagster_aws.s3.io_manager import PickledObjectS3IOManager, s3_pickle_io_manager
from dagster_aws.s3.utils import construct_s3_client


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
    @resource
    def test_s3_resource(_):
        return construct_s3_client(max_attempts=5)

    @op(out=Out(Int, io_manager_key="io_manager"))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=Out(Int, io_manager_key="io_manager"),
    )
    def add_one(num):
        return num + 1

    @job(
        resource_defs={
            "io_manager": s3_pickle_io_manager,
            "s3": test_s3_resource,
        }
    )
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_s3_pickle_io_manager_execution(mock_s3_bucket):
    inty_job = define_inty_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

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

    io_manager = PickledObjectS3IOManager(
        mock_s3_bucket.name, construct_s3_client(max_attempts=5), s3_prefix="dagster"
    )
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


def define_multiple_output_job():
    @resource
    def test_s3_resource(_):
        return construct_s3_client(max_attempts=5)

    @op(
        out={
            "foo": Out(Int, io_manager_key="io_manager"),
            "foobar": Out(Int, io_manager_key="io_manager"),
        }
    )
    def baz():
        yield 5
        yield 10

    
    @job(
        resource_defs={
            "io_manager" = s3_pickle_io_manager,
            "s3": test_s3_resource
            }
    )
    def output_prefix_execution_plan():
        baz()

    return output_prefix_execution_plan


def test_s3_pickle_io_manager_prefix(mock_s3_bucket):

    prefixy_job = define_multiple_output_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

    run_id = make_new_run_id()

    resolved_run_config = ResolvedRunConfig.build(prefixy_job, run_config=run_config)
    execution_plan = ExecutionPlan.build(InMemoryPipeline(prefixy_job), resolved_run_config)

    assert execution_plan.get_step_by_key("baz")

    instance = DagsterInstance.ephemeral()


    step_keys = ["baz"]
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(pipeline_name=prefixy_job.name, run_id=run_id, run_config=run_config)

    baz_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, prefixy_job, resolved_run_config),
            pipeline=InMemoryPipeline(prefixy_job),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )
    
    five = get_step_output(baz_step_events, "baz", "foo")
    ten = get_step_output(baz_step_events, "baz", "foobar")

    assert five and ten
    assert five == 5 and ten == 10

    mocked_s3_client = construct_s3_client(max_attempts=5)
    io_manager = PickledObjectS3IOManager(
        mock_s3_bucket.name, mocked_s3_client, s3_prefix="dagster"
    )

    step_output_handle = StepOutputHandle("baz")
    context = build_output_context(
            step_key = step_output_handle.step_key,
            name = step_output_handle.output_name,
            run_id = run_id
    )
    io_manager.handle_output(context, five)
    io_manager.handle_output(context, ten)
    
    assert mocked_s3_client.get_object(Bucket=mock_s3_bucket.name, Key="five")
    assert mocked_s3_client.get_object(Bucket=mock_s3_bucket.name, Key="ten")

