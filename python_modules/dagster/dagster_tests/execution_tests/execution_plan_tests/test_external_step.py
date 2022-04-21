import os
import tempfile
import time
import uuid
from threading import Thread

import pytest

from dagster import (
    DynamicOut,
    DynamicOutput,
    Failure,
    Field,
    MetadataEntry,
    ModeDefinition,
    ResourceDefinition,
    RetryPolicy,
    RetryRequested,
    String,
    execute_pipeline,
    execute_pipeline_iterator,
    fs_io_manager,
    job,
    op,
    pipeline,
    reconstructable,
    reexecute_pipeline,
    resource,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster.core.execution.plan.external_step import (
    LocalExternalStepLauncher,
    local_external_step_launcher,
    step_context_to_step_run_ref,
    step_run_ref_to_step_context,
)
from dagster.core.execution.retries import RetryMode
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.test_utils import instance_for_test
from dagster.utils import safe_tempfile_path, send_interrupt
from dagster.utils.merger import deep_merge_dicts, merge_dicts

RUN_CONFIG_BASE = {"solids": {"return_two": {"config": {"a": "b"}}}}


def make_run_config(scratch_dir, mode):
    if mode in ["external", "request_retry"]:
        step_launcher_resource_keys = ["first_step_launcher", "second_step_launcher"]
    else:
        step_launcher_resource_keys = ["second_step_launcher"]
    return deep_merge_dicts(
        RUN_CONFIG_BASE,
        {
            "resources": merge_dicts(
                {"io_manager": {"config": {"base_dir": scratch_dir}}},
                {
                    step_launcher_resource_key: {"config": {"scratch_dir": scratch_dir}}
                    for step_launcher_resource_key in step_launcher_resource_keys
                },
            ),
        },
    )


class RequestRetryLocalExternalStepLauncher(LocalExternalStepLauncher):
    def launch_step(self, step_context, prior_attempts_count):
        if prior_attempts_count == 0:
            raise RetryRequested()
        else:
            return super(RequestRetryLocalExternalStepLauncher, self).launch_step(
                step_context, prior_attempts_count
            )


@resource(config_schema=local_external_step_launcher.config_schema)
def request_retry_local_external_step_launcher(context):
    return RequestRetryLocalExternalStepLauncher(**context.resource_config)


def _define_failing_job(has_policy: bool, is_explicit: bool = True):
    @op(
        required_resource_keys={"step_launcher"},
        retry_policy=RetryPolicy(max_retries=3) if has_policy else None,
    )
    def retry_op(context):
        if context.retry_number < 3:
            if is_explicit:
                raise Failure(description="some failure description", metadata={"foo": 1.23})
            else:
                _ = "x" + 1
        return context.retry_number

    @job(
        resource_defs={
            "step_launcher": local_external_step_launcher,
            "io_manager": fs_io_manager,
        }
    )
    def retry_job():
        retry_op()

    return retry_job


def _define_retry_job():
    return _define_failing_job(has_policy=True)


def _define_error_job():
    return _define_failing_job(has_policy=False, is_explicit=False)


def _define_failure_job():
    return _define_failing_job(has_policy=False)


def _define_dynamic_job(launch_initial, launch_final):
    from typing import List

    initial_launcher = (
        local_external_step_launcher if launch_initial else ResourceDefinition.mock_resource()
    )
    final_launcher = (
        local_external_step_launcher if launch_final else ResourceDefinition.mock_resource()
    )

    @op(required_resource_keys={"initial_launcher"}, out=DynamicOut(int))
    def dynamic_outs():
        for i in range(0, 3):
            yield DynamicOutput(value=i, mapping_key=f"num_{i}")

    @op
    def increment(i):
        return i + 1

    @op(required_resource_keys={"final_launcher"})
    def total(ins: List[int]):
        return sum(ins)

    @job(
        resource_defs={
            "initial_launcher": initial_launcher,
            "final_launcher": final_launcher,
            "io_manager": fs_io_manager,
        }
    )
    def my_job():
        all_incs = dynamic_outs().map(increment)
        total(all_incs.collect())

    return my_job


def _define_basic_job(launch_initial, launch_final):
    initial_launcher = (
        local_external_step_launcher if launch_initial else ResourceDefinition.mock_resource()
    )
    final_launcher = (
        local_external_step_launcher if launch_final else ResourceDefinition.mock_resource()
    )

    @op(required_resource_keys={"initial_launcher"})
    def op1():
        return 1

    @op(required_resource_keys={"initial_launcher"})
    def op2():
        return 2

    @op(required_resource_keys={"final_launcher"})
    def combine(a, b):
        return a + b

    @job(
        resource_defs={
            "initial_launcher": initial_launcher,
            "final_launcher": final_launcher,
            "io_manager": fs_io_manager,
        }
    )
    def my_job():
        combine(op1(), op2())

    return my_job


def define_dynamic_job_all_launched():
    return _define_dynamic_job(True, True)


def define_dynamic_job_first_launched():
    return _define_dynamic_job(True, False)


def define_dynamic_job_last_launched():
    return _define_dynamic_job(False, True)


def define_basic_job_all_launched():
    return _define_basic_job(True, True)


def define_basic_job_first_launched():
    return _define_basic_job(True, False)


def define_basic_job_last_launched():
    return _define_basic_job(False, True)


def define_basic_pipeline():
    @solid(required_resource_keys=set(["first_step_launcher"]), config_schema={"a": Field(str)})
    def return_two(_):
        return 2

    @solid(required_resource_keys=set(["second_step_launcher"]))
    def add_one(_, num):
        return num + 1

    @pipeline(
        mode_defs=[
            ModeDefinition(
                "external",
                resource_defs={
                    "first_step_launcher": local_external_step_launcher,
                    "second_step_launcher": local_external_step_launcher,
                    "io_manager": fs_io_manager,
                },
            ),
            ModeDefinition(
                "internal_and_external",
                resource_defs={
                    "first_step_launcher": no_step_launcher,
                    "second_step_launcher": local_external_step_launcher,
                    "io_manager": fs_io_manager,
                },
            ),
            ModeDefinition(
                "request_retry",
                resource_defs={
                    "first_step_launcher": request_retry_local_external_step_launcher,
                    "second_step_launcher": request_retry_local_external_step_launcher,
                    "io_manager": fs_io_manager,
                },
            ),
        ]
    )
    def basic_pipeline():
        add_one(return_two())

    return basic_pipeline


def define_sleepy_pipeline():
    @solid(
        config_schema={"tempfile": Field(String)},
        required_resource_keys=set(["first_step_launcher"]),
    )
    def sleepy_solid(context):
        with open(context.solid_config["tempfile"], "w", encoding="utf8") as ff:
            ff.write("yup")
        start_time = time.time()
        while True:
            time.sleep(0.1)
            if time.time() - start_time > 120:
                raise Exception("Timed out")

    @pipeline(
        mode_defs=[
            ModeDefinition(
                "external",
                resource_defs={
                    "first_step_launcher": local_external_step_launcher,
                    "io_manager": fs_io_manager,
                },
            ),
        ]
    )
    def sleepy_pipeline():
        sleepy_solid()

    return sleepy_pipeline


def initialize_step_context(scratch_dir, instance):
    pipeline_run = PipelineRun(
        pipeline_name="foo_pipeline",
        run_id=str(uuid.uuid4()),
        run_config=make_run_config(scratch_dir, "external"),
        mode="external",
    )

    recon_pipeline = reconstructable(define_basic_pipeline)

    plan = create_execution_plan(recon_pipeline, pipeline_run.run_config, mode="external")

    initialization_manager = PlanExecutionContextManager(
        pipeline=recon_pipeline,
        execution_plan=plan,
        run_config=pipeline_run.run_config,
        pipeline_run=pipeline_run,
        instance=instance,
        retry_mode=RetryMode.DISABLED,
    )
    for _ in initialization_manager.prepare_context():
        pass
    pipeline_context = initialization_manager.get_context()

    step_context = pipeline_context.for_step(plan.get_step_by_key("return_two"))
    return step_context


def test_step_context_to_step_run_ref():
    with DagsterInstance.ephemeral() as instance:
        step_context = initialize_step_context("", instance)
        step = step_context.step
        step_run_ref = step_context_to_step_run_ref(step_context, 0)
        assert step_run_ref.run_config == step_context.pipeline_run.run_config
        assert step_run_ref.run_id == step_context.pipeline_run.run_id

        rehydrated_step_context = step_run_ref_to_step_context(step_run_ref, instance)
        rehydrated_step = rehydrated_step_context.step
        assert rehydrated_step.pipeline_name == step.pipeline_name
        assert rehydrated_step.step_inputs == step.step_inputs
        assert rehydrated_step.step_outputs == step.step_outputs
        assert rehydrated_step.kind == step.kind
        assert rehydrated_step.solid_handle.name == step.solid_handle.name
        assert rehydrated_step.logging_tags == step.logging_tags
        assert rehydrated_step.tags == step.tags


def test_local_external_step_launcher():
    with tempfile.TemporaryDirectory() as tmpdir:
        with DagsterInstance.ephemeral() as instance:
            step_context = initialize_step_context(tmpdir, instance)

            step_launcher = LocalExternalStepLauncher(tmpdir)
            events = list(step_launcher.launch_step(step_context, 0))
            event_types = [event.event_type for event in events]
            assert DagsterEventType.STEP_START in event_types
            assert DagsterEventType.STEP_SUCCESS in event_types
            assert DagsterEventType.STEP_FAILURE not in event_types


@pytest.mark.parametrize("mode", ["external", "internal_and_external"])
def test_pipeline(mode):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = execute_pipeline(
            pipeline=reconstructable(define_basic_pipeline),
            mode=mode,
            run_config=make_run_config(tmpdir, mode),
        )
        assert result.result_for_solid("return_two").output_value() == 2
        assert result.result_for_solid("add_one").output_value() == 3


@pytest.mark.parametrize(
    "job_fn",
    [
        define_dynamic_job_all_launched,
        define_dynamic_job_first_launched,
        define_dynamic_job_last_launched,
    ],
)
def test_dynamic_job(job_fn):
    with tempfile.TemporaryDirectory() as tmpdir:
        with instance_for_test() as instance:
            result = execute_pipeline(
                pipeline=reconstructable(job_fn),
                run_config={
                    "resources": {
                        "initial_launcher": {
                            "config": {"scratch_dir": tmpdir},
                        },
                        "final_launcher": {
                            "config": {"scratch_dir": tmpdir},
                        },
                        "io_manager": {"config": {"base_dir": tmpdir}},
                    }
                },
                instance=instance,
            )
            assert result.output_for_solid("total") == 6


@pytest.mark.parametrize(
    "job_fn",
    [
        define_basic_job_all_launched,
        define_basic_job_first_launched,
        define_basic_job_last_launched,
    ],
)
def test_reexecution(job_fn):
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "initial_launcher": {
                    "config": {"scratch_dir": tmpdir},
                },
                "final_launcher": {
                    "config": {"scratch_dir": tmpdir},
                },
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            run1 = execute_pipeline(
                pipeline=reconstructable(job_fn),
                run_config=run_config,
                instance=instance,
            )
            assert run1.success
            assert run1.result_for_solid("combine").output_value() == 3
            run2 = reexecute_pipeline(
                pipeline=reconstructable(job_fn),
                parent_run_id=run1.run_id,
                run_config=run_config,
                instance=instance,
                step_selection=["combine"],
            )
            assert run2.success
            assert run2.result_for_solid("combine").output_value() == 3


def test_retry_policy():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            run = execute_pipeline(
                pipeline=reconstructable(_define_retry_job),
                run_config=run_config,
                instance=instance,
            )
            assert run.success
            assert run.result_for_solid("retry_op").output_value() == 3
            step_retry_events = [
                e for e in run.event_list if e.event_type_value == "STEP_RESTARTED"
            ]
            assert len(step_retry_events) == 3


def test_explicit_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            run = execute_pipeline(
                pipeline=reconstructable(_define_failure_job),
                run_config=run_config,
                instance=instance,
                raise_on_error=False,
            )
            fd = run.result_for_solid("retry_op").failure_data
            assert fd.user_failure_data.description == "some failure description"
            assert fd.user_failure_data.metadata_entries == [
                MetadataEntry.float(label="foo", value=1.23)
            ]


def test_arbitrary_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            run = execute_pipeline(
                pipeline=reconstructable(_define_error_job),
                run_config=run_config,
                instance=instance,
                raise_on_error=False,
            )
            failure_events = [e for e in run.event_list if e.event_type_value == "STEP_FAILURE"]
            assert len(failure_events) == 1
            fd = run.result_for_solid("retry_op").failure_data
            assert fd.error.cause.cls_name == "TypeError"


def test_launcher_requests_retry():
    mode = "request_retry"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = execute_pipeline(
            pipeline=reconstructable(define_basic_pipeline),
            mode=mode,
            run_config=make_run_config(tmpdir, mode),
        )
        assert result.success
        assert result.result_for_solid("return_two").output_value() == 2
        assert result.result_for_solid("add_one").output_value() == 3
        for step_key, events in result.events_by_step_key.items():
            if step_key:
                event_types = [event.event_type for event in events]
                assert DagsterEventType.STEP_UP_FOR_RETRY in event_types
                assert DagsterEventType.STEP_RESTARTED in event_types


def _send_interrupt_thread(temp_file):
    while not os.path.exists(temp_file):
        time.sleep(0.1)
    send_interrupt()


@pytest.mark.parametrize("mode", ["external"])
def test_interrupt_step_launcher(mode):
    with tempfile.TemporaryDirectory() as tmpdir:
        with safe_tempfile_path() as success_tempfile:
            sleepy_run_config = {
                "resources": {
                    "first_step_launcher": {
                        "config": {"scratch_dir": tmpdir},
                    },
                    "io_manager": {"config": {"base_dir": tmpdir}},
                },
                "solids": {"sleepy_solid": {"config": {"tempfile": success_tempfile}}},
            }

            interrupt_thread = Thread(target=_send_interrupt_thread, args=(success_tempfile,))

            interrupt_thread.start()

            results = []

            for result in execute_pipeline_iterator(
                pipeline=reconstructable(define_sleepy_pipeline),
                mode=mode,
                run_config=sleepy_run_config,
            ):
                results.append(result.event_type)

            assert DagsterEventType.STEP_FAILURE in results
            assert DagsterEventType.PIPELINE_FAILURE in results

            interrupt_thread.join()


def test_multiproc_launcher_requests_retry():
    mode = "request_retry"
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = make_run_config(tmpdir, mode)
        run_config["execution"] = {"multiprocess": {}}
        result = execute_pipeline(
            instance=DagsterInstance.local_temp(tmpdir),
            pipeline=reconstructable(define_basic_pipeline),
            mode=mode,
            run_config=run_config,
        )
        assert result.success
        assert result.result_for_solid("return_two").output_value() == 2
        assert result.result_for_solid("add_one").output_value() == 3
        for step_key, events in result.events_by_step_key.items():
            if step_key:
                event_types = [event.event_type for event in events]
                assert DagsterEventType.STEP_UP_FOR_RETRY in event_types
                assert DagsterEventType.STEP_RESTARTED in event_types
