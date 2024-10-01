import os
import tempfile
import time
import uuid
from collections import defaultdict
from threading import Thread
from typing import List

import pytest
from dagster import (
    AssetCheckResult,
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    DynamicOut,
    DynamicOutput,
    Failure,
    Field,
    Output,
    ResourceDefinition,
    RetryPolicy,
    RetryRequested,
    String,
    asset,
    define_asset_job,
    fs_io_manager,
    job,
    op,
    reconstructable,
    resource,
    with_resources,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.no_step_launcher import no_step_launcher
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import (
    ReexecutionOptions,
    create_execution_plan,
    execute_job,
    execute_run_iterator,
)
from dagster._core.execution.context.system import IStepContext
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.plan.external_step import (
    LocalExternalStepLauncher,
    local_external_step_launcher,
    step_context_to_step_run_ref,
    step_run_ref_to_step_context,
)
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import instance_for_test
from dagster._utils import safe_tempfile_path, send_interrupt
from dagster._utils.merger import deep_merge_dicts, merge_dicts
from dagster._utils.test.definitions import lazy_definitions

RUN_CONFIG_BASE = {"ops": {"return_two": {"config": {"a": "b"}}}}


def make_run_config(scratch_dir: str, resource_set: str):
    if resource_set in ["external", "request_retry"]:
        step_launcher_resource_keys = ["first_step_launcher", "second_step_launcher"]
    else:
        step_launcher_resource_keys = ["second_step_launcher"]
    return deep_merge_dicts(
        RUN_CONFIG_BASE if resource_set != "no_base" else {},
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
    def launch_step(self, step_context):
        if step_context.previous_attempt_count == 0:
            raise RetryRequested()
        else:
            return super(RequestRetryLocalExternalStepLauncher, self).launch_step(step_context)


@resource(config_schema=local_external_step_launcher.config_schema)
def request_retry_local_external_step_launcher(context):
    return RequestRetryLocalExternalStepLauncher(**context.resource_config)


def _define_failing_job(has_policy: bool, is_explicit: bool = True) -> JobDefinition:
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


@op(
    required_resource_keys=set(["first_step_launcher"]),
    config_schema={"a": Field(str)},
)
def return_two(_):
    return 2


@op(required_resource_keys=set(["second_step_launcher"]))
def add_one(_, num):
    return num + 1


def _define_basic_job_2(resource_set: str) -> JobDefinition:
    if resource_set == "external":
        first_launcher = local_external_step_launcher
        second_launcher = local_external_step_launcher
    elif resource_set == "internal_and_external":
        first_launcher = no_step_launcher
        second_launcher = local_external_step_launcher
    elif resource_set == "request_retry":
        first_launcher = request_retry_local_external_step_launcher
        second_launcher = request_retry_local_external_step_launcher
    else:
        raise Exception("Unknown resource set")

    @job(
        resource_defs={
            "first_step_launcher": first_launcher,
            "second_step_launcher": second_launcher,
            "io_manager": fs_io_manager,
        },
    )
    def basic_job():
        add_one(return_two())

    return basic_job


def define_basic_job_external():
    return _define_basic_job_2("external")


def define_basic_job_internal_and_external():
    return _define_basic_job_2("internal_and_external")


def define_basic_job_request_retry():
    return _define_basic_job_2("request_retry")


def define_sleepy_job():
    @op(
        config_schema={"tempfile": Field(String)},
        required_resource_keys=set(["first_step_launcher"]),
    )
    def sleepy_op(context):
        with open(context.op_config["tempfile"], "w", encoding="utf8") as ff:
            ff.write("yup")
        start_time = time.time()
        while True:
            time.sleep(0.1)
            if time.time() - start_time > 120:
                raise Exception("Timed out")

    @job(
        resource_defs={
            "first_step_launcher": local_external_step_launcher,
            "io_manager": fs_io_manager,
        }
    )
    def sleepy_job():
        sleepy_op()

    return sleepy_job


def define_asset_check_job():
    @asset(
        check_specs=[
            AssetCheckSpec(
                asset="asset1",
                name="check1",
            )
        ],
        resource_defs={
            "second_step_launcher": local_external_step_launcher,
            "io_manager": fs_io_manager,
        },
    )
    def asset1():
        yield Output(1)
        yield AssetCheckResult(passed=True)

    return define_asset_job(name="asset_check_job", selection=[asset1]).resolve(
        asset_graph=AssetGraph.from_assets([asset1])
    )


def initialize_step_context(
    scratch_dir: str,
    instance: DagsterInstance,
    job_def_fn=define_basic_job_external,
    resource_set="external",
    step_name="return_two",
) -> IStepContext:
    run = DagsterRun(
        job_name="foo_job",
        run_id=str(uuid.uuid4()),
        run_config=make_run_config(scratch_dir, resource_set),
    )

    recon_job = reconstructable(job_def_fn)

    plan = create_execution_plan(recon_job, run.run_config)

    initialization_manager = PlanExecutionContextManager(
        job=recon_job,
        execution_plan=plan,
        run_config=run.run_config,
        dagster_run=run,
        instance=instance,
        retry_mode=RetryMode.DISABLED,
    )
    for _ in initialization_manager.prepare_context():
        pass
    job_context = initialization_manager.get_context()

    step_context = job_context.for_step(
        plan.get_step_by_key(step_name),  # type: ignore
        KnownExecutionState(),
    )
    return step_context


def test_step_context_to_step_run_ref():
    with DagsterInstance.ephemeral() as instance:
        step_context = initialize_step_context("", instance)
        step = step_context.step
        step_run_ref = step_context_to_step_run_ref(step_context)
        assert step_run_ref.run_config == step_context.dagster_run.run_config
        assert step_run_ref.run_id == step_context.dagster_run.run_id

        rehydrated_step_context = step_run_ref_to_step_context(step_run_ref, instance)
        rehydrated_step = rehydrated_step_context.step
        assert rehydrated_step.job_name == step.job_name
        assert rehydrated_step.step_inputs == step.step_inputs
        assert rehydrated_step.step_outputs == step.step_outputs
        assert rehydrated_step.kind == step.kind
        assert rehydrated_step.node_handle.name == step.node_handle.name
        assert rehydrated_step.logging_tags == step.logging_tags
        assert rehydrated_step.tags == step.tags


def test_local_external_step_launcher():
    with tempfile.TemporaryDirectory() as tmpdir:
        with DagsterInstance.ephemeral() as instance:
            step_context = initialize_step_context(tmpdir, instance)

            step_launcher = LocalExternalStepLauncher(tmpdir)
            events = list(step_launcher.launch_step(step_context))
            event_types = [event.event_type for event in events]
            assert DagsterEventType.STEP_START in event_types
            assert DagsterEventType.STEP_SUCCESS in event_types
            assert DagsterEventType.STEP_FAILURE not in event_types


def test_asset_check_step_launcher():
    with tempfile.TemporaryDirectory() as tmpdir:
        with DagsterInstance.ephemeral() as instance:
            step_context = initialize_step_context(
                tmpdir,
                instance,
                job_def_fn=define_asset_check_job,
                resource_set="no_base",
                step_name="asset1",
            )

            step_launcher = LocalExternalStepLauncher(tmpdir)
            events = list(step_launcher.launch_step(step_context))
            event_types = [event.event_type for event in events]
            assert DagsterEventType.STEP_START in event_types
            assert DagsterEventType.STEP_SUCCESS in event_types
            assert DagsterEventType.STEP_FAILURE not in event_types


def test_asset_check_step_launcher_job():
    with tempfile.TemporaryDirectory() as tmpdir:
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(define_asset_check_job),
                run_config=make_run_config(tmpdir, "no_base"),
                instance=instance,
            ) as result:
                assert result.success
                check_evals = result.get_asset_check_evaluations()
                assert len(check_evals) == 1
                assert check_evals[0].passed


@pytest.mark.parametrize("resource_set", ["external", "internal_and_external"])
def test_job(resource_set):
    if resource_set == "external":
        job_fn = define_basic_job_external
    elif resource_set == "internal_and_external":
        job_fn = define_basic_job_internal_and_external
    else:
        raise Exception("Unknown resource set")

    with tempfile.TemporaryDirectory() as tmpdir:
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(job_fn),
                instance=instance,
                run_config=make_run_config(tmpdir, resource_set),
            ) as result:
                assert result.output_for_node("return_two") == 2
                assert result.output_for_node("add_one") == 3


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
            with execute_job(
                reconstructable(job_fn),
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
            ) as result:
                assert result.output_for_node("total") == 6


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
            with execute_job(
                reconstructable(job_fn),
                run_config=run_config,
                instance=instance,
            ) as result_1:
                assert result_1.success
                assert result_1.output_for_node("combine") == 3
                parent_run_id = result_1.run_id
            with execute_job(
                reconstructable(job_fn),
                reexecution_options=ReexecutionOptions(
                    parent_run_id=parent_run_id, step_selection=["combine"]
                ),
                run_config=run_config,
                instance=instance,
            ) as result_2:
                assert result_2.success
                assert result_2.output_for_node("combine") == 3


def test_retry_policy():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(_define_retry_job),
                run_config=run_config,
                instance=instance,
            ) as result:
                assert result.success
                assert result.output_for_node("retry_op") == 3
                step_retry_events = [
                    e for e in result.all_events if e.event_type_value == "STEP_RESTARTED"
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
            with execute_job(
                reconstructable(_define_failure_job),
                run_config=run_config,
                instance=instance,
                raise_on_error=False,
            ) as result:
                fd = result.failure_data_for_node("retry_op")
                assert fd.user_failure_data.description == "some failure description"
                assert fd.user_failure_data.metadata == {"foo": MetadataValue.float(1.23)}


def test_arbitrary_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(_define_error_job),
                run_config=run_config,
                instance=instance,
                raise_on_error=False,
            ) as result:
                failure_events = [
                    e for e in result.all_events if e.event_type_value == "STEP_FAILURE"
                ]
                assert len(failure_events) == 1
                assert result.failure_data_for_node("retry_op").error.cause.cls_name == "TypeError"


def test_launcher_requests_retry():
    with tempfile.TemporaryDirectory() as tmpdir:
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(define_basic_job_request_retry),
                instance=instance,
                run_config=make_run_config(tmpdir, "request_retry"),
            ) as result:
                assert result.success
                assert result.output_for_node("return_two") == 2
                assert result.output_for_node("add_one") == 3
                for node_name in ["add_one", "return_two"]:
                    events = result.events_for_node(node_name)
                    event_types = [event.event_type for event in events]
                    assert DagsterEventType.STEP_UP_FOR_RETRY in event_types
                    assert DagsterEventType.STEP_RESTARTED in event_types


def _send_interrupt_thread(temp_file):
    while not os.path.exists(temp_file):
        time.sleep(0.1)
    send_interrupt()


def test_interrupt_step_launcher():
    with tempfile.TemporaryDirectory() as tmpdir:
        with safe_tempfile_path() as success_tempfile:
            sleepy_run_config = {
                "resources": {
                    "first_step_launcher": {
                        "config": {"scratch_dir": tmpdir},
                    },
                    "io_manager": {"config": {"base_dir": tmpdir}},
                },
                "ops": {"sleepy_op": {"config": {"tempfile": success_tempfile}}},
            }

            interrupt_thread = Thread(target=_send_interrupt_thread, args=(success_tempfile,))

            interrupt_thread.start()

            event_types = []

            with instance_for_test() as instance:
                dagster_run = instance.create_run_for_job(
                    define_sleepy_job(),
                    run_config=sleepy_run_config,
                )

                for event in execute_run_iterator(
                    reconstructable(define_sleepy_job),
                    dagster_run,
                    instance=instance,
                ):
                    event_types.append(event.event_type)

            assert DagsterEventType.STEP_FAILURE in event_types
            assert DagsterEventType.PIPELINE_FAILURE in event_types

            interrupt_thread.join()


def test_multiproc_launcher_requests_retry():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = make_run_config(tmpdir, "request_retry")
        with execute_job(
            reconstructable(define_basic_job_request_retry),
            run_config=run_config,
            instance=DagsterInstance.local_temp(tmpdir),
        ) as result:
            assert result.success
            assert result.output_for_node("return_two") == 2
            assert result.output_for_node("add_one") == 3
            events_by_step_key = defaultdict(list)
            for event in result.all_events:
                if event.step_key is not None:
                    events_by_step_key[event.step_key].append(event)
            for step_key, events in events_by_step_key.items():
                if step_key:
                    event_types = [event.event_type for event in events]
                    assert DagsterEventType.STEP_UP_FOR_RETRY in event_types
                    assert DagsterEventType.STEP_RESTARTED in event_types


def test_multiproc_launcher_with_repository_load_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_config = {
            "resources": {
                "step_launcher": {"config": {"scratch_dir": tmpdir}},
                "io_manager": {"config": {"base_dir": tmpdir}},
            }
        }
        with instance_for_test() as instance:
            instance.run_storage.set_cursor_values({"val": "INITIAL_VALUE"})
            recon_repo = ReconstructableRepository.for_file(
                __file__, fn_name="cacheable_asset_defs"
            )
            recon_job = ReconstructableJob(repository=recon_repo, job_name="all_asset_job")

            with execute_job(
                recon_job,
                run_config=run_config,
                instance=instance,
            ) as result:
                assert result.success
                assert instance.run_storage.get_cursor_values({"val"}).get("val") == "NEW_VALUE"


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(keys_by_output_name={"result": AssetKey("foo")})

    def compute_cacheable_data(self):
        # used for tracking how many times this function gets called over an execution
        # since we're crossing process boundaries, we pre-populate this value in the host process
        # and assert that this pre-populated value is present, to ensure that we'll error if this
        # gets called in a child process
        instance = DagsterInstance.get()
        val = instance.run_storage.get_cursor_values({"val"}).get("val")
        assert val == "INITIAL_VALUE"
        instance.run_storage.set_cursor_values({"val": "NEW_VALUE"})
        return [self._cacheable_data]

    def build_definitions(self, data):
        assert len(data) == 1
        assert data == [self._cacheable_data]

        @op(required_resource_keys={"step_launcher"})
        def _op():
            return 1

        return with_resources(
            [
                AssetsDefinition.from_op(
                    _op,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ],
            {"step_launcher": local_external_step_launcher},
        )


@lazy_definitions
def cacheable_asset_defs():
    @asset
    def bar(foo):
        return foo + 1

    return Definitions(
        assets=[bar, MyCacheableAssetsDefinition("xyz")],
        jobs=[define_asset_job("all_asset_job")],
    )
