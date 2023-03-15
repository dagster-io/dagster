# pylint: disable=unused-argument
import subprocess
import time

import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    asset,
    define_asset_job,
    executor,
    job,
    op,
    reconstructable,
    repository,
)
from dagster._config import Permissive
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.definitions.reconstruct import ReconstructablePipeline, ReconstructableRepository
from dagster._core.definitions.repository_definition import AssetsDefinitionCacheableData
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import execute_pipeline, reexecute_pipeline
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
    StepDelegatingExecutor,
    StepHandler,
)
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts

from .retry_jobs import (
    assert_expected_failure_behavior,
    get_dynamic_job_op_failure,
    get_dynamic_job_resource_init_failure,
)


class TestStepHandler(StepHandler):
    # This step handler waits for all processes to exit, because windows tests flake when processes
    # are left alive when the test ends. Non-test step handlers should not keep their own state in memory.
    processes = []
    launch_step_count = 0
    saw_baz_op = False
    check_step_health_count = 0
    terminate_step_count = 0
    verify_step_count = 0

    @property
    def name(self):
        return "TestStepHandler"

    def launch_step(self, step_handler_context):
        if step_handler_context.execute_step_args.should_verify_step:
            TestStepHandler.verify_step_count += 1
        if step_handler_context.execute_step_args.step_keys_to_execute[0] == "baz_op":
            TestStepHandler.saw_baz_op = True
            assert step_handler_context.step_tags["baz_op"] == {"foo": "bar"}

        TestStepHandler.launch_step_count += 1
        print("TestStepHandler Launching Step!")  # noqa: T201
        TestStepHandler.processes.append(
            subprocess.Popen(step_handler_context.execute_step_args.get_command_args())
        )
        return iter(())

    def check_step_health(self, step_handler_context) -> CheckStepHealthResult:
        TestStepHandler.check_step_health_count += 1
        return CheckStepHealthResult.healthy()

    def terminate_step(self, step_handler_context):
        TestStepHandler.terminate_step_count += 1
        raise NotImplementedError()

    @classmethod
    def reset(cls):
        cls.processes = []
        cls.launch_step_count = 0
        cls.check_step_health_count = 0
        cls.terminate_step_count = 0
        cls.verify_step_count = 0

    @classmethod
    def wait_for_processes(cls):
        for p in cls.processes:
            p.wait(timeout=5)


@executor(
    name="test_step_delegating_executor",
    requirements=multiple_process_executor_requirements(),
    config_schema=Permissive(),
)
def test_step_delegating_executor(exc_init):
    return StepDelegatingExecutor(
        TestStepHandler(),
        **(merge_dicts({"retries": RetryMode.DISABLED}, exc_init.executor_config)),
    )


@op
def bar_op(_):
    return "bar"


@op(tags={"foo": "bar"})
def baz_op(_, bar):
    return bar * 2


@job(executor_def=test_step_delegating_executor)
def foo_job():
    baz_op(bar_op())
    bar_op()


def test_execute():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(foo_job),
            instance=instance,
            run_config={"execution": {"config": {}}},
        )
        TestStepHandler.wait_for_processes()

    assert any(
        [
            "Starting execution with step handler TestStepHandler" in event.message
            for event in result.event_list
        ]
    )
    assert any(["STEP_START" in event for event in result.event_list])
    assert result.success
    assert TestStepHandler.saw_baz_op
    assert TestStepHandler.verify_step_count == 0


def test_skip_execute():
    from .test_jobs import define_dynamic_skipping_job

    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_dynamic_skipping_job),
            instance=instance,
        )
        TestStepHandler.wait_for_processes()

    assert result.success


def test_dynamic_execute():
    from .test_jobs import define_dynamic_job

    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_dynamic_job),
            instance=instance,
        )
        TestStepHandler.wait_for_processes()

    assert result.success
    assert (
        len(
            [
                e
                for e in result.event_list
                if e.event_type_value == DagsterEventType.STEP_START.value
            ]
        )
        == 11
    )


def test_skipping():
    from .test_jobs import define_skpping_job

    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_skpping_job),
            instance=instance,
        )
        TestStepHandler.wait_for_processes()

    assert result.success


def test_execute_intervals():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(foo_job),
            instance=instance,
            run_config={"execution": {"config": {"check_step_health_interval_seconds": 60}}},
        )
        TestStepHandler.wait_for_processes()

    assert result.success
    assert TestStepHandler.launch_step_count == 3
    assert TestStepHandler.terminate_step_count == 0
    # pipeline should complete before 60s
    assert TestStepHandler.check_step_health_count == 0

    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(foo_job),
            instance=instance,
            run_config={"execution": {"config": {"check_step_health_interval_seconds": 0}}},
        )
        TestStepHandler.wait_for_processes()

    assert result.success
    assert TestStepHandler.launch_step_count == 3
    assert TestStepHandler.terminate_step_count == 0
    # every step should get checked at least once
    # TODO: better way to test this. Skipping for now because if step finishes fast enough the
    # count could be smaller than 3.
    # assert TestStepHandler.check_step_health_count >= 3


@op(tags={"database": "tiny"})
def slow_op(_):
    time.sleep(2)


@job(executor_def=test_step_delegating_executor)
def three_op_job():
    for i in range(3):
        slow_op.alias(f"slow_op_{i}")()


def test_max_concurrent():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(three_op_job),
            instance=instance,
            run_config={"execution": {"config": {"max_concurrent": 1}}},
        )
        TestStepHandler.wait_for_processes()
    assert result.success

    # test that all the steps run serially, since max_concurrent is 1
    active_step = None
    for event in result.event_list:
        if event.event_type_value == DagsterEventType.STEP_START.value:
            assert active_step is None, "A second step started before the first finished!"
            active_step = event.step_key
        elif event.event_type_value == DagsterEventType.STEP_SUCCESS.value:
            assert (
                active_step == event.step_key
            ), "A step finished that wasn't supposed to be active!"
            active_step = None


def test_tag_concurrency_limits():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(three_op_job),
            instance=instance,
            run_config={
                "execution": {
                    "config": {
                        "max_concurrent": 6001,
                        "tag_concurrency_limits": [
                            {"key": "database", "value": "tiny", "limit": 1}
                        ],
                    }
                }
            },
        )
        TestStepHandler.wait_for_processes()
    assert result.success

    # test that all the steps run serially, since database=tiny can only run one at a time
    active_step = None
    for event in result.event_list:
        if event.event_type_value == DagsterEventType.STEP_START.value:
            assert active_step is None, "A second step started before the first finished!"
            active_step = event.step_key
        elif event.event_type_value == DagsterEventType.STEP_SUCCESS.value:
            assert (
                active_step == event.step_key
            ), "A step finished that wasn't supposed to be active!"
            active_step = None


@executor(
    name="test_step_delegating_executor_verify_step",
    requirements=multiple_process_executor_requirements(),
    config_schema=Permissive(),
)
def test_step_delegating_executor_verify_step(exc_init):
    return StepDelegatingExecutor(
        TestStepHandler(),
        retries=RetryMode.DISABLED,
        sleep_seconds=exc_init.executor_config.get("sleep_seconds"),
        check_step_health_interval_seconds=exc_init.executor_config.get(
            "check_step_health_interval_seconds"
        ),
        should_verify_step=True,
    )


@job(executor_def=test_step_delegating_executor_verify_step)
def foo_job_verify_step():
    baz_op(bar_op())
    bar_op()


def test_execute_verify_step():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(foo_job_verify_step),
            instance=instance,
            run_config={"execution": {"config": {}}},
        )
        TestStepHandler.wait_for_processes()

    assert any(
        [
            "Starting execution with step handler TestStepHandler" in event.message
            for event in result.event_list
        ]
    )
    assert result.success
    assert TestStepHandler.verify_step_count == 3


def test_execute_using_repository_data():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        recon_repo = ReconstructableRepository.for_module(
            "dagster_tests.execution_tests.engine_tests.test_step_delegating_executor",
            fn_name="pending_repo",
        )
        recon_pipeline = ReconstructablePipeline(
            repository=recon_repo, pipeline_name="all_asset_job"
        )

        result = execute_pipeline(
            recon_pipeline,
            instance=instance,
            run_config={"execution": {"config": {}}},
        )
        call_counts = instance.run_storage.kvs_get(
            {"compute_cacheable_data_called", "get_definitions_called"}
        )
        assert call_counts.get("compute_cacheable_data_called") == "1"
        assert call_counts.get("get_definitions_called") == "4"
        TestStepHandler.wait_for_processes()

        assert any(
            [
                "Starting execution with step handler TestStepHandler" in (event.message or "")
                for event in result.event_list
            ]
        )
        assert result.success

        result = reexecute_pipeline(recon_pipeline, result.run_id, instance=instance)
        TestStepHandler.wait_for_processes()

        assert any(
            [
                "Starting execution with step handler TestStepHandler" in (event.message or "")
                for event in result.event_list
            ]
        )
        assert result.success
        # we do not attempt to fetch the previous repository load data off of the execution plan
        # from the previous run, so the reexecution will require us to fetch the metadata again
        call_counts = instance.run_storage.kvs_get(
            {"compute_cacheable_data_called", "get_definitions_called"}
        )
        assert call_counts.get("compute_cacheable_data_called") == "2"

        assert call_counts.get("get_definitions_called") == "7"


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(keys_by_output_name={"result": AssetKey("foo")})

    def compute_cacheable_data(self):
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "compute_cacheable_data_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})
        return [self._cacheable_data]

    def build_definitions(self, data):
        assert len(data) == 1
        assert data == [self._cacheable_data]
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "get_definitions_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})

        @op
        def _op():
            return 1

        return [
            AssetsDefinition.from_op(_op, keys_by_output_name=cd.keys_by_output_name) for cd in data
        ]


@asset
def bar(foo):
    return foo + 1


@repository(default_executor_def=test_step_delegating_executor)
def pending_repo():
    return [bar, MyCacheableAssetsDefinition("xyz"), define_asset_job("all_asset_job")]


def get_dynamic_resource_init_failure_job():
    return get_dynamic_job_resource_init_failure(test_step_delegating_executor)[0]


def get_dynamic_op_failure_job():
    return get_dynamic_job_op_failure(test_step_delegating_executor)[0]


# Tests identical retry behavior when a job fails because of resource
# initialization of a dynamic step, and failure during op runtime of a
# dynamic step.
@pytest.mark.parametrize(
    "job_fn,config_fn",
    [
        (
            get_dynamic_resource_init_failure_job,
            get_dynamic_job_resource_init_failure(test_step_delegating_executor)[1],
        ),
        (
            get_dynamic_op_failure_job,
            get_dynamic_job_op_failure(test_step_delegating_executor)[1],
        ),
    ],
)
def test_dynamic_failure_retry(job_fn, config_fn):
    TestStepHandler.reset()
    assert_expected_failure_behavior(job_fn, config_fn)
