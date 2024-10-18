import threading
import time

import pytest
from dagster import Failure, RetryPolicy, graph, in_process_executor, job, op, repository
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import execute_job, execute_run_iterator
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG
from dagster._core.test_utils import poll_for_finished_run
from dagster._core.workspace.context import WorkspaceRequestContext

from dagster_tests.execution_tests.engine_tests.test_step_delegating_executor import (
    test_step_delegating_executor,
)


@op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
def should_never_execute(_x):
    assert False  # this should never execute


@op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
def throw_error():
    raise Exception("bad programmer")


@graph
def error_graph():
    should_never_execute(throw_error())


@op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
def simple_op(context):
    time.sleep(0.1)
    foo_info = context.instance.event_log_storage.get_concurrency_info("foo")
    return {"active": foo_info.active_slot_count, "pending": foo_info.pending_step_count}


@op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
def second_op(context, _):
    time.sleep(0.1)
    foo_info = context.instance.event_log_storage.get_concurrency_info("foo")
    metadata = {"active": foo_info.active_slot_count, "pending": foo_info.pending_step_count}
    context.log_event(AssetMaterialization(asset_key="foo_slot", metadata=metadata))
    return metadata


@graph
def parallel_graph():
    simple_op()
    simple_op()
    simple_op()
    simple_op()
    simple_op()


@graph
def two_tier_graph():
    second_op(simple_op())
    second_op(simple_op())
    second_op(simple_op())
    second_op(simple_op())


@op(tags={GLOBAL_CONCURRENCY_TAG: "foo"}, retry_policy=RetryPolicy(max_retries=1))
def retry_op():
    raise Failure("I fail")


@job(executor_def=in_process_executor)
def retry_job():
    retry_op()
    simple_op()


@job
def simple_job():
    simple_op()


error_job_multiprocess = error_graph.to_job(name="error_job")
error_job_inprocess = error_graph.to_job(
    name="error_job_in_process", executor_def=in_process_executor
)
error_job_stepdelegating = error_graph.to_job(
    name="error_job_step_delegating", executor_def=test_step_delegating_executor
)
parallel_job_multiprocess = parallel_graph.to_job(name="parallel_job")
parallel_job_inprocess = parallel_graph.to_job(
    name="parallel_job_in_process", executor_def=in_process_executor
)
parallel_job_stepdelegating = parallel_graph.to_job(
    name="parallel_job_step_delegating", executor_def=test_step_delegating_executor
)
two_tier_job_multiprocess = two_tier_graph.to_job(name="two_tier_job")
two_tier_job_inprocess = two_tier_graph.to_job(
    name="two_tier_job_in_process", executor_def=in_process_executor
)
two_tier_job_step_delegating = two_tier_graph.to_job(
    name="two_tier_job_step_delegating", executor_def=test_step_delegating_executor
)


@repository
def concurrency_repo():
    return [
        error_job_multiprocess,
        error_job_inprocess,
        error_job_stepdelegating,
        parallel_job_multiprocess,
        parallel_job_inprocess,
        parallel_job_stepdelegating,
        retry_job,
        two_tier_job_multiprocess,
        two_tier_job_inprocess,
        two_tier_job_step_delegating,
        simple_job,
    ]


def define_parallel_inprocess_job():
    return parallel_job_inprocess


def define_parallel_multiprocess_job():
    return parallel_job_multiprocess


def define_parallel_stepdelegating_job():
    return parallel_job_stepdelegating


def define_error_inprocess_job():
    return error_job_inprocess


def define_error_multiprocess_job():
    return error_job_multiprocess


def define_error_stepdelegating_job():
    return error_job_stepdelegating


def define_retry_job():
    return retry_job


def define_simple_job():
    return simple_job


recon_error_inprocess = reconstructable(define_error_inprocess_job)
recon_error_multiprocess = reconstructable(define_error_multiprocess_job)
recon_error_stepdelegating = reconstructable(define_error_stepdelegating_job)
recon_parallel_inprocess = reconstructable(define_parallel_inprocess_job)
recon_parallel_multiprocess = reconstructable(define_parallel_multiprocess_job)
recon_parallel_stepdelegating = reconstructable(define_parallel_stepdelegating_job)
recon_retry_job = reconstructable(define_retry_job)
recon_simple_job = reconstructable(define_simple_job)


@pytest.fixture(
    name="parallel_recon_job",
    params=[recon_parallel_inprocess, recon_parallel_multiprocess, recon_parallel_stepdelegating],
)
def parallel_recon_job_fixture(request):
    return request.param


@pytest.fixture(
    name="parallel_recon_job_not_inprocess",
    params=[recon_parallel_multiprocess, recon_parallel_stepdelegating],
)
def parallel_recon_job_not_inprocess_fixture(request):
    return request.param


@pytest.fixture(
    name="error_recon_job",
    params=[recon_error_inprocess, recon_error_multiprocess, recon_error_stepdelegating],
)
def error_recon_job_fixture(request):
    return request.param


@pytest.fixture(
    name="two_tier_job_def",
    params=[
        # skip the in_process executor, which flakes based on run coordinator / launcher timing
        # two_tier_job_inprocess,
        two_tier_job_multiprocess,
        two_tier_job_step_delegating,
    ],
)
def two_tier_job_def_fixture(request):
    return request.param


def _create_run(
    instance: DagsterInstance, workspace: WorkspaceRequestContext, job_def: JobDefinition
):
    remote_job = (
        workspace.get_code_location("test")
        .get_repository("concurrency_repo")
        .get_full_job(job_def.name)
    )
    run = instance.create_run_for_job(
        job_def=job_def,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.NOT_STARTED
    return run


def test_parallel_concurrency(instance, parallel_recon_job):
    instance.event_log_storage.set_concurrency_slots("foo", 1)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    with execute_job(parallel_recon_job, instance=instance) as result:
        assert result.success
        ordered_node_names = [
            event.node_name for event in result.all_events if event.is_successful_output
        ]
        outputs = [result.output_for_node(name) for name in ordered_node_names]
        # should be 5 steps, each one executing at a time
        for output in outputs:
            assert output["active"] == 1

    # job successes release any claimed slots
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0


def _has_concurrency_blocked_event(events, concurrency_key):
    message_str = f"blocked by concurrency limit for key {concurrency_key}"
    for event in events:
        if message_str in event.message:
            return True
    return False


def test_concurrency_blocked_events(instance, parallel_recon_job_not_inprocess):
    instance.event_log_storage.set_concurrency_slots("foo", 1)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 1

    with execute_job(parallel_recon_job_not_inprocess, instance=instance) as result:
        assert _has_concurrency_blocked_event(result.all_events, "foo")


def test_error_concurrency(instance, error_recon_job):
    instance.event_log_storage.set_concurrency_slots("foo", 1)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    with execute_job(error_recon_job, instance=instance) as result:
        assert not result.success

    # job failures release any claimed slots
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0


def test_multi_slot_concurrency(instance, parallel_recon_job_not_inprocess):
    instance.event_log_storage.set_concurrency_slots("foo", 3)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")

    assert foo_info.slot_count == 3
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    with execute_job(parallel_recon_job_not_inprocess, instance=instance) as result:
        assert result.success
        ordered_node_names = [
            event.node_name for event in result.all_events if event.is_successful_output
        ]
        outputs = [result.output_for_node(name) for name in ordered_node_names]

        # 5 steps, but the max active at any time is 3
        assert max([output["active"] for output in outputs]) <= 3
        assert max([output["active"] for output in outputs]) > 1

    # job successes release any claimed slots
    assert foo_info.slot_count == 3
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0


def test_multi_run_concurrency(instance, workspace, two_tier_job_def):
    instance.event_log_storage.set_concurrency_slots("foo", 2)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")

    assert foo_info.slot_count == 2
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    run_one = _create_run(instance, workspace, two_tier_job_def)
    run_two = _create_run(instance, workspace, two_tier_job_def)
    instance.launch_run(run_id=run_one.run_id, workspace=workspace)
    instance.launch_run(run_id=run_two.run_id, workspace=workspace)
    run_one = poll_for_finished_run(instance, run_one.run_id, timeout=60)
    run_two = poll_for_finished_run(instance, run_two.run_id, timeout=60)

    assert run_one.status == DagsterRunStatus.SUCCESS
    assert run_two.status == DagsterRunStatus.SUCCESS

    records = [
        *instance.fetch_materializations(AssetKey(["foo_slot"]), ascending=True, limit=5000).records
    ]
    max_active = 0
    for record in records:
        num_active = record.asset_materialization.metadata["active"].value
        max_active = max(max_active, num_active)
        assert num_active <= 2

    assert max_active == 2

    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 2
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0


def test_retry_concurrency_release(instance):
    instance.event_log_storage.set_concurrency_slots("foo", 1)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    events = []
    with execute_job(recon_retry_job, instance=instance) as result:
        for event in result.all_events:
            if event.step_key and event.event_type_value in (
                DagsterEventType.STEP_START.value,
                DagsterEventType.STEP_SUCCESS.value,
                DagsterEventType.STEP_FAILURE.value,
                DagsterEventType.STEP_RESTARTED.value,
                DagsterEventType.STEP_UP_FOR_RETRY.value,
            ):
                events.append((event.step_key, event.event_type_value))

    # job has released any claimed slots
    assert foo_info.slot_count == 1
    assert foo_info.active_slot_count == 0
    assert foo_info.pending_step_count == 0
    assert foo_info.assigned_step_count == 0

    # retry_op starts before simple_op starts
    # simple_op succeeds before second execution of retry_op fails
    assert events == [
        ("retry_op", "STEP_START"),
        ("retry_op", "STEP_UP_FOR_RETRY"),
        ("simple_op", "STEP_START"),
        ("simple_op", "STEP_SUCCESS"),
        ("retry_op", "STEP_RESTARTED"),
        ("retry_op", "STEP_FAILURE"),
    ]


def test_multiprocess_simple_job_has_blocked_message(instance):
    instance.event_log_storage.set_concurrency_slots("foo", 0)
    foo_info = instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.slot_count == 0
    run = instance.create_run_for_job(define_simple_job())

    def _unblock_concurrency_key(instance, timeout):
        time.sleep(timeout)
        instance.event_log_storage.set_concurrency_slots("foo", 1)

    start = time.time()
    has_blocked_message = False
    timed_out = False

    TIMEOUT = 5
    threading.Thread(target=_unblock_concurrency_key, args=(instance, TIMEOUT), daemon=True).start()

    for event in execute_run_iterator(recon_simple_job, run, instance=instance):
        if "blocked by concurrency limit for key foo" in event.message:
            has_blocked_message = True
            break
        if time.time() - start > TIMEOUT:
            timed_out = True
            break

    assert not timed_out
    assert has_blocked_message
