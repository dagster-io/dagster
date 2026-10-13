import logging
import os
from multiprocessing import get_context
from unittest import mock

import dagster as dg
import pytest
from dagster import DagsterEvent, DagsterInstance
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.errors import DagsterBackfillAdmissionClosed, DagsterInvariantViolationError
from dagster._core.execution.api import execute_run
from dagster._core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
    cancel_backfill_runs_and_cancellation_complete,
)
from dagster._core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.multiprocess import execute_step_out_of_process
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
    StepDelegatingExecutor,
    StepHandler,
)
from dagster._core.instance.config import ConcurrencyConfig
from dagster._core.launcher.base import (
    BackfillWorkerExitStatus,
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._core.remote_origin import (
    RegisteredCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.run_coordinator.queued_run_coordinator import RunQueueConfig
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.runs.base import K8sWorkerTarget
from dagster._core.storage.tags import (
    BACKFILL_ID_TAG,
    BACKFILL_STOP_PROTOCOL_TAG,
    PARENT_BACKFILL_ID_TAG,
    RETRY_NUMBER_TAG,
    ROOT_BACKFILL_ID_TAG,
    WILL_RETRY_TAG,
)
from dagster._core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
    consume_new_runs_for_automatic_reexecution,
    retry_run,
    should_retry,
)
from dagster._daemon.monitoring.run_monitoring import monitor_started_run
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon

LOGGER = logging.getLogger(__name__)
BACKFILL_ID = "backfill-stop"


class DefinitiveTestLauncher(RunLauncher):
    def __init__(self):
        self.launches = []
        self.exit_status = BackfillWorkerExitStatus.UNKNOWN
        self.on_launch = None

    def launch_run(self, context: LaunchRunContext) -> None:
        self.launches.append(context.dagster_run.run_id)
        if self.on_launch:
            self.on_launch()

    def terminate(self, run_id: str) -> bool:
        return True

    def get_backfill_worker_exit_status(self, run: DagsterRun, launch) -> BackfillWorkerExitStatus:
        return self.exit_status


@pytest.fixture
def instance():
    with DagsterInstance.ephemeral() as instance:
        launcher = DefinitiveTestLauncher()
        launcher.register_instance(instance)
        instance._run_launcher = launcher  # noqa: SLF001
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={BACKFILL_STOP_PROTOCOL_TAG: "v1"},
                backfill_timestamp=1.0,
            )
        )
        yield instance


def owned_run(instance, status=DagsterRunStatus.NOT_STARTED):
    return create_run_for_test(
        instance,
        status=status,
        tags={BACKFILL_ID_TAG: BACKFILL_ID},
        remote_job_origin=RemoteJobOrigin(
            RemoteRepositoryOrigin(RegisteredCodeLocationOrigin(location_name="test"), "repo"),
            "job",
        ),
    )


@pytest.mark.parametrize("status", [DagsterRunStatus.NOT_STARTED, DagsterRunStatus.QUEUED])
def test_closed_unclaimed_run_never_launches_and_drains(instance, status):
    run = owned_run(instance, status)
    instance.request_backfill_stop(BACKFILL_ID)
    instance.launch_run(run.run_id, mock.Mock())
    assert instance.run_launcher.launches == []
    assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELED
    instance.update_backfill(
        instance.get_backfill(BACKFILL_ID).with_status(BulkActionStatus.CANCELED)
    )
    assert instance.get_backfill(BACKFILL_ID).status == BulkActionStatus.CANCELED


def test_close_during_admitted_rpc_requires_ack_and_worker_exit(instance):
    run = owned_run(instance)

    def close_during_rpc():
        instance.request_backfill_stop(BACKFILL_ID)
        assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
        assert not instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged

    instance.run_launcher.on_launch = close_during_rpc
    instance.launch_run(run.run_id, mock.Mock())
    assert instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged
    instance.report_run_canceled(instance.get_run_by_id(run.run_id))
    assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
    instance.run_launcher.exit_status = BackfillWorkerExitStatus.EXITED
    assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
    assert instance.get_backfill_worker_launches(BACKFILL_ID) == []


def test_lost_rpc_response_never_redispatches_or_completes(instance):
    run = owned_run(instance)

    def lose_response():
        raise RuntimeError("worker started but response was lost")

    instance.run_launcher.on_launch = lose_response
    with pytest.raises(RuntimeError, match="response was lost"):
        instance.launch_run(run.run_id, mock.Mock())
    instance.launch_run(run.run_id, mock.Mock())
    assert instance.run_launcher.launches == [run.run_id]
    instance.request_backfill_stop(BACKFILL_ID)
    instance.run_launcher.exit_status = BackfillWorkerExitStatus.EXITED
    assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
    assert not instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged


def test_finished_parent_worker_still_requires_exit_proof(instance):
    run = owned_run(instance)
    instance.launch_run(run.run_id, mock.Mock())
    instance.report_run_failed(instance.get_run_by_id(run.run_id))
    instance.request_backfill_stop(BACKFILL_ID)
    assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
    instance.run_launcher.exit_status = BackfillWorkerExitStatus.EXITED
    assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)


def test_normal_completion_resolves_acknowledged_workers(instance):
    run = owned_run(instance)
    instance.launch_run(run.run_id, mock.Mock())
    instance.report_run_failed(instance.get_run_by_id(run.run_id))
    completed = instance.get_backfill(BACKFILL_ID).with_status(BulkActionStatus.COMPLETED_FAILED)
    instance.update_backfill(completed)
    assert instance.get_backfill(BACKFILL_ID).status == BulkActionStatus.REQUESTED
    instance.run_launcher.exit_status = BackfillWorkerExitStatus.EXITED
    instance.update_backfill(completed)
    assert instance.get_backfill(BACKFILL_ID).status == BulkActionStatus.COMPLETED_FAILED


def test_owned_worker_resume_is_rejected(instance):
    run = owned_run(instance)
    instance.launch_run(run.run_id, mock.Mock())
    with pytest.raises(DagsterInvariantViolationError, match="cannot resume"):
        instance.resume_run(run.run_id, mock.Mock(), attempt_number=1)


def test_duplicate_run_dispatch_does_not_regress_started_status(instance):
    run = owned_run(instance)
    instance.launch_run(run.run_id, mock.Mock())
    instance.report_dagster_event(
        DagsterEvent(event_type_value="PIPELINE_START", job_name=run.job_name), run_id=run.run_id
    )
    instance.launch_run(run.run_id, mock.Mock())
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.STARTED
    assert instance.run_launcher.launches == [run.run_id]


def test_marked_run_never_promises_worker_resumption(instance):
    run = owned_run(instance)
    with (
        mock.patch.object(
            DagsterInstance,
            "run_monitoring_enabled",
            new_callable=mock.PropertyMock,
            return_value=True,
        ),
        mock.patch.object(
            DagsterInstance,
            "run_monitoring_max_resume_run_attempts",
            new_callable=mock.PropertyMock,
            return_value=3,
        ),
    ):
        assert not instance.run_will_resume(run.run_id)


def test_monitoring_marks_owned_worker_failure_without_dispatching_resume(instance):
    run = owned_run(instance)
    instance.launch_run(run.run_id, mock.Mock())
    instance.report_dagster_event(
        DagsterEvent(event_type_value="PIPELINE_START", job_name=run.job_name), run_id=run.run_id
    )
    record = instance.get_run_records(RunsFilter(run_ids=[run.run_id]))[0]
    with (
        mock.patch.object(
            DefinitiveTestLauncher,
            "supports_check_run_worker_health",
            new_callable=mock.PropertyMock,
            return_value=True,
        ),
        mock.patch.object(
            instance.run_launcher,
            "check_run_worker_health",
            return_value=CheckRunHealthResult(WorkerStatus.FAILED),
        ),
        mock.patch.object(instance.run_launcher, "resume_run") as resume,
        mock.patch.object(
            DagsterInstance,
            "run_monitoring_max_resume_run_attempts",
            new_callable=mock.PropertyMock,
            return_value=3,
        ),
    ):
        monitor_started_run(instance, mock.Mock(), record, LOGGER)
        resume.assert_not_called()
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.FAILURE


def test_queued_launch_failure_is_not_reenqueued(instance):
    run = owned_run(instance)
    instance.report_dagster_event(DagsterEvent.job_enqueue(run), run_id=run.run_id)
    from dagster._core.errors import DagsterUserCodeUnreachableError

    def unreachable():
        raise DagsterUserCodeUnreachableError("ambiguous dispatch")

    instance.run_launcher.on_launch = unreachable
    config = ConcurrencyConfig.from_concurrency_settings(
        {}, RunQueueConfig(10, [], max_user_code_failure_retries=5)
    )
    with QueuedRunCoordinatorDaemon(interval_seconds=1) as daemon:
        assert not daemon._dequeue_run(instance, mock.Mock(), run, config, None)  # noqa: SLF001
    assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.FAILURE
    assert not instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged


@pytest.mark.parametrize("status", list(BulkActionStatus))
def test_auto_retry_requires_requested_backfill(status):
    instance = mock.Mock()
    instance.get_backfill.return_value = mock.Mock(status=status)
    run = DagsterRun(
        job_name="job",
        status=DagsterRunStatus.FAILURE,
        tags={BACKFILL_ID_TAG: BACKFILL_ID, WILL_RETRY_TAG: "true"},
    )
    assert should_retry(run, instance) == (status == BulkActionStatus.REQUESTED)


def retry_context(parent, child=None):
    instance = mock.Mock()
    instance.get_backfill.return_value = mock.Mock(status=BulkActionStatus.REQUESTED)
    instance.get_run_group.return_value = (parent.run_id, [parent] + ([child] if child else []))
    instance.get_run_by_id.return_value = child
    context = mock.Mock(instance=instance)
    return context


def retry_parent():
    return DagsterRun(
        job_name="job",
        status=DagsterRunStatus.FAILURE,
        remote_job_origin=RemoteJobOrigin(
            RemoteRepositoryOrigin(RegisteredCodeLocationOrigin(location_name="test"), "repo"),
            "job",
        ),
        tags={
            BACKFILL_ID_TAG: BACKFILL_ID,
            PARENT_BACKFILL_ID_TAG: "parent-backfill",
            ROOT_BACKFILL_ID_TAG: "root-backfill",
            WILL_RETRY_TAG: "true",
        },
    )


def test_existing_detached_auto_retry_is_not_submitted():
    parent = retry_parent()
    child = DagsterRun(
        job_name="job",
        parent_run_id=parent.run_id,
        root_run_id=parent.run_id,
        tags={RETRY_NUMBER_TAG: "1"},
    )
    context = retry_context(parent, child)
    retry_run(parent, context)
    context.instance.submit_run.assert_not_called()
    context.instance.create_reexecuted_run.assert_not_called()


def test_auto_retry_registration_preserves_ownership_when_admission_closes():
    parent = retry_parent()
    context = retry_context(parent)
    context.instance.create_reexecuted_run.side_effect = DagsterBackfillAdmissionClosed("closed")
    retry_run(parent, context)
    tags = context.instance.create_reexecuted_run.call_args.kwargs["extra_tags"]
    assert tags[BACKFILL_ID_TAG] == BACKFILL_ID
    assert tags[PARENT_BACKFILL_ID_TAG] == "parent-backfill"
    assert tags[ROOT_BACKFILL_ID_TAG] == "root-backfill"
    context.instance.submit_run.assert_not_called()


def test_base_launcher_worker_evidence_is_unknown():
    launcher = DefinitiveTestLauncher()
    run = DagsterRun(job_name="job", status=DagsterRunStatus.CANCELED)
    assert (
        RunLauncher.get_backfill_worker_exit_status(launcher, run, mock.Mock())
        == BackfillWorkerExitStatus.UNKNOWN
    )


def test_unknown_stop_protocol_version_cannot_downgrade_to_legacy(instance):
    backfill = instance.get_backfill(BACKFILL_ID)._replace(tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"})
    with pytest.raises(DagsterInvariantViolationError, match="unsupported stop protocol version"):
        _ = backfill.uses_stop_protocol


@pytest.mark.parametrize("enabled", [False, True])
def test_protocol_setting_controls_new_backfills_only(enabled):
    with instance_for_test(overrides={"backfill_stop_protocol": {"enabled": enabled}}) as instance:
        assert instance.backfill_stop_protocol_enabled == enabled
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=1.0,
            )
        )
        assert instance.get_backfill(BACKFILL_ID).uses_stop_protocol == enabled


@pytest.mark.parametrize("enabled, explicit_marker", [(True, False), (False, True), (False, False)])
def test_creation_policy_requires_capable_backend_only_for_protocol_backfills(
    instance, enabled, explicit_marker
):
    backend = mock.Mock(supports_backfill_stop_protocol=False)
    backfill = PartitionBackfill(
        backfill_id="unsupported-backend",
        status=BulkActionStatus.REQUESTED,
        from_failure=False,
        tags={BACKFILL_STOP_PROTOCOL_TAG: "v1"} if explicit_marker else {},
        backfill_timestamp=1.0,
    )
    with (
        mock.patch.object(instance, "_run_storage", backend),
        mock.patch.object(
            DagsterInstance,
            "backfill_stop_protocol_enabled",
            new_callable=mock.PropertyMock,
            return_value=enabled,
        ),
    ):
        if enabled or explicit_marker:
            with pytest.raises(DagsterInvariantViolationError, match="requires storage"):
                instance.add_backfill(backfill)
            backend.add_backfill.assert_not_called()
        else:
            instance.add_backfill(backfill)
            backend.add_backfill.assert_called_once_with(backfill)


def test_enabled_creation_cannot_replace_unknown_protocol_version(instance):
    backend = mock.Mock(supports_backfill_stop_protocol=True)
    backfill = PartitionBackfill(
        backfill_id="unknown-version",
        status=BulkActionStatus.REQUESTED,
        from_failure=False,
        tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"},
        backfill_timestamp=1.0,
    )
    with (
        mock.patch.object(instance, "_run_storage", backend),
        mock.patch.object(
            DagsterInstance,
            "backfill_stop_protocol_enabled",
            new_callable=mock.PropertyMock,
            return_value=True,
        ),
        pytest.raises(DagsterInvariantViolationError, match="unsupported stop protocol version"),
    ):
        instance.add_backfill(backfill)
    backend.add_backfill.assert_not_called()


def test_unmarked_backfill_keeps_legacy_launcher_and_drain_behavior():
    with DagsterInstance.ephemeral() as instance:
        launcher = DefinitiveTestLauncher()
        launcher.register_instance(instance)
        instance._run_launcher = launcher  # noqa: SLF001
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=1.0,
            )
        )
        run = owned_run(instance)
        instance.launch_run(run.run_id, mock.Mock())
        assert launcher.launches == [run.run_id]
        assert instance.get_backfill_worker_launches(BACKFILL_ID) == []
        instance.report_run_canceled(instance.get_run_by_id(run.run_id))
        instance.request_backfill_stop(BACKFILL_ID)
        assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)


class UnsupportedExecutor(Executor):
    @property
    def retries(self):
        return RetryMode.DISABLED

    def execute(self, context, plan):
        raise AssertionError("Unsupported executor reached dispatch")
        yield from ()


@dg.executor
def unsupported_test_executor(_):
    return UnsupportedExecutor()


@dg.job(executor_def=unsupported_test_executor)
def unsupported_test_job():
    pass


@pytest.mark.dagster_run
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Run Dagster execution checks locally.")
def test_unsupported_executor_rejected_before_execute(instance):
    run = instance.create_run_for_job(unsupported_test_job, tags={BACKFILL_ID_TAG: BACKFILL_ID})
    result = execute_run(InMemoryJob(unsupported_test_job), run, instance)
    assert not result.success
    failures = [event for event in result.all_events if event.is_job_failure]
    assert (
        "does not support durable backfill worker admission"
        in failures[0].job_failure_data.error.message
    )


@pytest.mark.parametrize("close_during_resource_init", [False, True])
@pytest.mark.dagster_run
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Run Dagster execution checks locally.")
def test_native_step_launcher_cannot_dispatch_for_marked_backfill(
    instance, close_during_resource_init
):
    dispatches = []

    class RemoteStepLauncher(StepLauncher):
        def launch_step(self, context):
            dispatches.append(context.instance.get_backfill(BACKFILL_ID).status)
            raise RuntimeError("external dispatch reached")
            yield from ()

    @dg.resource
    def remote_launcher(context):
        if close_during_resource_init:
            context.instance.request_backfill_stop(BACKFILL_ID)
        return RemoteStepLauncher()

    @dg.op(required_resource_keys={"remote_launcher"})
    def remote_op():
        return 1

    @dg.job(executor_def=dg.in_process_executor, resource_defs={"remote_launcher": remote_launcher})
    def remote_job():
        remote_op()

    run = instance.create_run_for_job(remote_job, tags={BACKFILL_ID_TAG: BACKFILL_ID})
    instance.launch_run(run.run_id, mock.Mock())
    result = execute_run(InMemoryJob(remote_job), run, instance)
    assert not result.success
    assert dispatches == []
    assert instance.get_backfill(BACKFILL_ID).status == (
        BulkActionStatus.CANCELING if close_during_resource_init else BulkActionStatus.REQUESTED
    )
    failures = [event for event in result.all_events if event.is_step_failure]
    assert "Native StepLauncher" in failures[0].step_failure_data.error.message
    if not close_during_resource_init:
        instance.request_backfill_stop(BACKFILL_ID)
    instance.run_launcher.exit_status = BackfillWorkerExitStatus.EXITED
    assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)


@pytest.mark.dagster_run
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Run Dagster execution checks locally.")
def test_unmarked_backfill_preserves_native_step_launcher():
    dispatches = []

    class LocalTestStepLauncher(StepLauncher):
        def launch_step(self, context):
            dispatches.append(context.step.key)
            yield from core_dagster_event_sequence_for_step(context)

    @dg.op(required_resource_keys={"native_launcher"})
    def native_op():
        return 1

    @dg.job(
        executor_def=dg.in_process_executor,
        resource_defs={
            "native_launcher": dg.ResourceDefinition.hardcoded_resource(LocalTestStepLauncher())
        },
    )
    def native_job():
        native_op()

    with DagsterInstance.ephemeral() as instance:
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=1.0,
            )
        )
        run = instance.create_run_for_job(native_job, tags={BACKFILL_ID_TAG: BACKFILL_ID})
        result = execute_run(InMemoryJob(native_job), run, instance)
        assert result.success
        assert dispatches == ["native_op"]


def test_native_step_acknowledges_process_start_before_iterator_exhaustion(instance):
    run = owned_run(instance)
    storage_instance = mock.Mock(wraps=instance)
    storage_instance.get_ref.return_value = mock.Mock()
    context = mock.Mock(instance=storage_instance, dagster_run=run, run_config={})
    step = mock.Mock(key="my_step")
    child = get_context("spawn").Process()

    def launched_process(*_):
        yield child
        yield None

    with (
        mock.patch(
            "dagster._core.executor.multiprocess.execute_child_process_command", launched_process
        ),
        mock.patch.object(
            DagsterEvent, "step_worker_starting", return_value=mock.Mock(spec=DagsterEvent)
        ),
    ):
        iterator = execute_step_out_of_process(
            get_context("spawn"),
            mock.Mock(),
            context,
            step,
            {},
            {},
            {"my_step": mock.Mock()},
            RetryMode.DISABLED,
            KnownExecutionState(),
            None,
        )
        next(iterator)
        assert instance.get_backfill_worker_launches(BACKFILL_ID) == []
        next(iterator)
        assert instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged
        list(iterator)


class TestStepHandler(StepHandler):
    __test__ = False

    def __init__(self):
        self.launches = 0
        self.on_launch = None

    @property
    def name(self):
        return "definitive-test-step-handler"

    @property
    def supports_backfill_stop_protocol(self):
        return True

    def get_backfill_worker_target(self, context):
        return K8sWorkerTarget(job_name="step-job", namespace="step-namespace")

    def launch_step(self, context):
        self.launches += 1
        yield mock.Mock(spec=DagsterEvent)
        if self.on_launch:
            self.on_launch()

    def check_step_health(self, context):
        return CheckStepHealthResult.healthy()

    def terminate_step(self, context):
        yield from ()


def step_context(instance, run, attempt=0):
    return mock.Mock(
        instance=instance,
        dagster_run=run,
        execute_step_args=mock.Mock(
            step_keys_to_execute=["my_step"],
            known_state=KnownExecutionState(previous_retry_attempts={"my_step": attempt}),
        ),
    )


def test_step_dispatch_acknowledges_only_after_generator_success(instance):
    run = owned_run(instance)
    handler = TestStepHandler()
    executor = StepDelegatingExecutor(handler, RetryMode.DISABLED)
    iterator = executor._launch_step(step_context(instance, run))  # noqa: SLF001
    next(iterator)
    assert not instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged
    list(iterator)
    launch = instance.get_backfill_worker_launches(BACKFILL_ID)[0]
    assert launch.acknowledged
    assert launch.target == K8sWorkerTarget(job_name="step-job", namespace="step-namespace")


def test_step_dispatch_closed_gate_prevents_rpc(instance):
    run = owned_run(instance)
    instance.request_backfill_stop(BACKFILL_ID)
    handler = TestStepHandler()
    executor = StepDelegatingExecutor(handler, RetryMode.DISABLED)
    with pytest.raises(DagsterBackfillAdmissionClosed):
        list(executor._launch_step(step_context(instance, run)))  # noqa: SLF001
    assert handler.launches == 0


def test_step_dispatch_lost_response_remains_pending_and_cannot_replay(instance):
    run = owned_run(instance)
    handler = TestStepHandler()

    def lose_response():
        raise RuntimeError("step response lost")

    handler.on_launch = lose_response
    executor = StepDelegatingExecutor(handler, RetryMode.DISABLED)
    context = step_context(instance, run)
    with pytest.raises(RuntimeError):
        list(executor._launch_step(context))  # noqa: SLF001
    assert not instance.get_backfill_worker_launches(BACKFILL_ID)[0].acknowledged
    with pytest.raises(DagsterBackfillAdmissionClosed):
        list(executor._launch_step(context))  # noqa: SLF001
    assert handler.launches == 1


def test_step_retries_have_distinct_durable_attempt_ids(instance):
    run = owned_run(instance)
    handler = TestStepHandler()
    executor = StepDelegatingExecutor(handler, RetryMode.DISABLED)
    list(executor._launch_step(step_context(instance, run, attempt=0)))  # noqa: SLF001
    list(executor._launch_step(step_context(instance, run, attempt=1)))  # noqa: SLF001
    assert (
        len({launch.worker_id for launch in instance.get_backfill_worker_launches(BACKFILL_ID)})
        == 2
    )


def test_long_dynamic_step_key_has_a_bounded_dispatch_identity(instance):
    run = owned_run(instance)
    handler = TestStepHandler()
    executor = StepDelegatingExecutor(handler, RetryMode.DISABLED)
    step_key = f"consume[{'x' * 300}]"
    context = step_context(instance, run)
    context.execute_step_args.step_keys_to_execute = [step_key]
    context.execute_step_args.known_state = KnownExecutionState(
        previous_retry_attempts={step_key: 0}
    )
    list(executor._launch_step(context))  # noqa: SLF001
    launch = instance.get_backfill_worker_launches(BACKFILL_ID)[0]
    assert len(launch.worker_id) <= 255
    assert launch.acknowledged
    with pytest.raises(DagsterBackfillAdmissionClosed):
        list(executor._launch_step(context))  # noqa: SLF001
    assert handler.launches == 1


@dg.op
def native_retry_failure():
    raise RuntimeError("retry fixture failure")


@dg.job(executor_def=dg.in_process_executor)
def native_retry_job():
    native_retry_failure()


native_retry_defs = dg.Definitions(jobs=[native_retry_job])


@pytest.mark.dagster_run
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Run Dagster execution checks locally.")
def test_native_retry_consumer_reuses_child_after_rejected_delete():
    with instance_for_test(
        overrides={
            "run_retries": {"enabled": True, "max_retries": 1},
            "backfill_stop_protocol": {"enabled": True},
            "run_coordinator": {
                "module": "dagster._core.run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        launcher = DefinitiveTestLauncher()
        launcher.register_instance(instance)
        instance._run_launcher = launcher  # noqa: SLF001
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=1.0,
            )
        )
        with in_process_test_workspace(
            instance, LoadableTargetOrigin(python_file=__file__, attribute="native_retry_defs")
        ) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repository = next(iter(location.get_repositories().values()))
            remote_job = repository.get_full_job("native_retry_job")
            parent = instance.create_run_for_job(
                native_retry_job,
                tags={BACKFILL_ID_TAG: BACKFILL_ID},
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            instance.launch_run(parent.run_id, workspace)
            assert not execute_run(InMemoryJob(native_retry_job), parent, instance).success
            records = instance.get_run_records(RunsFilter(run_ids=[parent.run_id]))
            process_context = mock.Mock(instance=instance)
            process_context.create_request_context.return_value = workspace
            list(consume_new_runs_for_automatic_reexecution(process_context, records, LOGGER))
            _, group = instance.get_run_group(parent.run_id)
            child = next(run for run in group if run.parent_run_id == parent.run_id)
            assert (
                child.tags[BACKFILL_STOP_PROTOCOL_TAG]
                == instance.get_backfill(BACKFILL_ID).tags[BACKFILL_STOP_PROTOCOL_TAG]
            )
            with pytest.raises(
                DagsterInvariantViolationError, match="Cannot delete an automatic retry"
            ):
                instance.delete_run(child.run_id)
            list(consume_new_runs_for_automatic_reexecution(process_context, records, LOGGER))
            _, replayed_group = instance.get_run_group(parent.run_id)
            assert {run.run_id for run in replayed_group} == {parent.run_id, child.run_id}
            assert instance.get_run_by_id(child.run_id).tags[BACKFILL_ID_TAG] == BACKFILL_ID
            assert instance.get_run_by_id(child.run_id).status == DagsterRunStatus.QUEUED
            assert launcher.launches == [parent.run_id]


@pytest.mark.dagster_run
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Run Dagster execution checks locally.")
def test_manual_retry_after_backfill_close_detaches_protocol_and_preserves_ancestry():
    with instance_for_test(overrides={"backfill_stop_protocol": {"enabled": True}}) as instance:
        launcher = DefinitiveTestLauncher()
        launcher.register_instance(instance)
        instance._run_launcher = launcher  # noqa: SLF001
        instance.add_backfill(
            PartitionBackfill(
                backfill_id=BACKFILL_ID,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=1.0,
            )
        )
        with in_process_test_workspace(
            instance, LoadableTargetOrigin(python_file=__file__, attribute="native_retry_defs")
        ) as workspace:
            location = workspace.get_code_location(workspace.code_location_names[0])
            repository = next(iter(location.get_repositories().values()))
            remote_job = repository.get_full_job("native_retry_job")
            parent = instance.create_run_for_job(
                native_retry_job,
                tags={BACKFILL_ID_TAG: BACKFILL_ID},
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            instance.launch_run(parent.run_id, workspace)
            assert not execute_run(InMemoryJob(native_retry_job), parent, instance).success
            parent = instance.get_run_by_id(parent.run_id)
            assert parent.tags[BACKFILL_STOP_PROTOCOL_TAG] == "v1"
            instance.request_backfill_stop(BACKFILL_ID)
            launcher.exit_status = BackfillWorkerExitStatus.EXITED
            assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, LOGGER)
            instance.update_backfill(
                instance.get_backfill(BACKFILL_ID).with_status(BulkActionStatus.CANCELED)
            )
            assert instance.get_backfill(BACKFILL_ID).status == BulkActionStatus.CANCELED
            manual = instance.create_reexecuted_run(
                parent_run=parent,
                request_context=workspace,
                code_location=location,
                remote_job=remote_job,
                strategy=ReexecutionStrategy.FROM_FAILURE,
                use_parent_run_tags=True,
            )
            assert manual.parent_run_id == parent.run_id
            assert manual.root_run_id == (parent.root_run_id or parent.run_id)
            assert BACKFILL_ID_TAG not in manual.tags
            instance.launch_run(manual.run_id, workspace)
            assert launcher.launches == [parent.run_id, manual.run_id]
            assert instance.get_backfill_worker_launches(BACKFILL_ID) == []
            assert BACKFILL_STOP_PROTOCOL_TAG not in manual.tags
