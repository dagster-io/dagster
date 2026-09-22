from datetime import datetime, timezone
from unittest import mock

import pytest
from dagster import RetryPolicy, job, op, reconstructable
from dagster._cli.api import _execute_step_command_body, verify_step
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.plan.objects import StepFailureData, StepRetryData, StepSuccessData
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.execution.stats import StepEventStatus
from dagster._core.executor.step_delegating import StepDelegatingExecutor, StepHandlerContext
from dagster._core.test_utils import create_run_for_test
from dagster._grpc.types import ExecuteStepArgs
from dagster._utils.error import SerializableErrorInfo
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import K8sStepHandler, k8s_job_executor
from kubernetes.client import (
    V1Job,
    V1JobCondition,
    V1JobStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1PodStatus,
)


@op(retry_policy=RetryPolicy(max_retries=1))
def work():
    return "done"


@job(executor_def=k8s_job_executor)
def step_health_job():
    work()


@pytest.fixture
def health_check(kubeconfig_file, k8s_run_launcher_instance):
    batch_api = mock.MagicMock()
    core_api = mock.MagicMock()
    core_api.list_namespaced_pod.return_value = V1PodList(items=[])
    handler = K8sStepHandler(
        image="test-image",
        container_context=K8sContainerContext(namespace="test-namespace"),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=batch_api,
        k8s_client_core_api=core_api,
    )
    yield handler, k8s_run_launcher_instance, batch_api, core_api


def _context(instance, handler, retry_count=0, retry_mode=RetryMode.ENABLED):
    recon_job = reconstructable(step_health_job)
    run = create_run_for_test(
        instance,
        job_name="step_health_job",
        job_code_origin=recon_job.get_python_origin(),
    )
    known_state = KnownExecutionState(previous_retry_attempts={"work": retry_count})
    execution_plan = create_execution_plan(recon_job, known_state=known_state)
    executor = StepDelegatingExecutor(
        handler,
        retries=retry_mode,
        sleep_seconds=0.0,
        check_step_health_interval_seconds=0,
        should_verify_step=True,
    )
    plan_context = PlanOrchestrationContext(
        plan_data=PlanData(
            job=recon_job,
            dagster_run=run,
            instance=instance,
            execution_plan=execution_plan,
            raise_on_error=False,
            retry_mode=retry_mode,
        ),
        log_manager=create_context_free_log_manager(instance, run),
        executor=executor,
        output_capture=None,
    )
    context = StepHandlerContext(
        instance=instance,
        plan_context=plan_context,
        steps=execution_plan.steps,  # ty: ignore[invalid-argument-type]
        execute_step_args=ExecuteStepArgs(
            job_origin=recon_job.get_python_origin(),
            run_id=run.run_id,
            step_keys_to_execute=["work"],
            instance_ref=instance.get_ref(),
            known_state=known_state,
            should_verify_step=True,
            retry_mode=retry_mode.for_inner_plan(),
            print_serialized_events=False,
        ),
        dagster_run=run,
    )
    return context, plan_context, execution_plan, executor


def _report(context, event_type, step_key="work"):
    event_data = {
        DagsterEventType.RESOURCE_INIT_FAILURE: EngineEventData(
            error=SerializableErrorInfo(message="resource failed", stack=[], cls_name=None)
        ),
        DagsterEventType.STEP_SUCCESS: StepSuccessData(duration_ms=1.0),
        DagsterEventType.STEP_FAILURE: StepFailureData(error=None, user_failure_data=None),
        DagsterEventType.STEP_UP_FOR_RETRY: StepRetryData(
            error=SerializableErrorInfo(message="retry", stack=[], cls_name=None)
        ),
    }.get(event_type)
    context.instance.report_dagster_event(
        DagsterEvent(
            event_type_value=event_type.value,
            job_name=context.dagster_run.job_name,
            step_key=step_key,
            event_specific_data=event_data,
        ),
        context.dagster_run.run_id,
    )


def _set_job_status(batch_api, condition_type=None, condition_status="True", **kwargs):
    batch_api.read_namespaced_job_status.return_value = V1Job(
        status=V1JobStatus(
            conditions=(
                [V1JobCondition(type=condition_type, status=condition_status)]
                if condition_type
                else None
            ),
            **kwargs,
        )
    )


@pytest.mark.parametrize(
    "condition_type,condition_status",
    [(None, "True"), ("Failed", "False"), ("Complete", "False"), ("FailureTarget", "True")],
)
@pytest.mark.parametrize("active", [0, 1])
def test_failed_pod_does_not_mean_job_has_finished(
    health_check, condition_type, condition_status, active
):
    handler, instance, batch_api, core_api = health_check
    context, _, _, _ = _context(instance, handler)
    _report(context, DagsterEventType.STEP_START)
    _set_job_status(batch_api, condition_type, condition_status, failed=1, active=active)

    assert handler.check_step_health(context).is_healthy
    core_api.list_namespaced_pod.assert_not_called()


@pytest.mark.parametrize("started", [False, True])
def test_completed_job_without_step_outcome_is_unhealthy(health_check, started):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler)
    if started:
        _report(context, DagsterEventType.STEP_START)
    _set_job_status(batch_api, "Complete", succeeded=1)

    result = handler.check_step_health(context)

    assert not result.is_healthy
    assert "work" in result.unhealthy_reason
    assert "completed" in result.unhealthy_reason


def test_terminal_failed_job_is_unhealthy(health_check):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler)
    _report(context, DagsterEventType.STEP_START)
    # The condition is authoritative, including when the failed pod count is absent.
    _set_job_status(batch_api, "Failed")

    result = handler.check_step_health(context)

    assert not result.is_healthy
    assert "failed Kubernetes job" in result.unhealthy_reason


@pytest.mark.parametrize("condition_type", ["Complete", "Failed"])
@pytest.mark.parametrize("retry_count", [0, 1])
@pytest.mark.parametrize(
    "outcome",
    [
        DagsterEventType.STEP_SUCCESS,
        DagsterEventType.STEP_FAILURE,
        DagsterEventType.STEP_SKIPPED,
        DagsterEventType.STEP_UP_FOR_RETRY,
    ],
)
def test_persisted_outcome_waits_for_executor_event_tailer(
    health_check, condition_type, retry_count, outcome
):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler, retry_count=retry_count)
    _report(context, DagsterEventType.STEP_START)
    if retry_count:
        _report(context, DagsterEventType.STEP_UP_FOR_RETRY)
        _report(context, DagsterEventType.STEP_RESTARTED)
    _report(context, outcome)
    _set_job_status(batch_api, condition_type, failed=1 if condition_type == "Failed" else 0)

    assert handler.check_step_health(context).is_healthy


@pytest.mark.parametrize("retry_started", [False, True])
def test_previous_attempt_retry_event_does_not_hide_unfinished_current_attempt(
    health_check, retry_started
):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler, retry_count=1)
    _report(context, DagsterEventType.STEP_START)
    _report(context, DagsterEventType.STEP_UP_FOR_RETRY)
    if retry_started:
        _report(context, DagsterEventType.STEP_RESTARTED)
    _set_job_status(batch_api, "Complete", succeeded=1)

    assert not handler.check_step_health(context).is_healthy


@pytest.mark.parametrize("retry_count", [0, 1])
def test_resource_init_failure_waits_for_executor_event_tailer(health_check, retry_count):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler, retry_count=retry_count)
    if retry_count:
        _report(context, DagsterEventType.RESOURCE_INIT_FAILURE)
        _report(context, DagsterEventType.STEP_UP_FOR_RETRY)
    _report(context, DagsterEventType.RESOURCE_INIT_FAILURE)
    _set_job_status(batch_api, "Complete")

    assert handler.check_step_health(context).is_healthy


@pytest.mark.parametrize("retry_started", [False, True])
def test_previous_resource_init_failure_does_not_hide_unfinished_retry(health_check, retry_started):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler, retry_count=1)
    _report(context, DagsterEventType.RESOURCE_INIT_FAILURE)
    _report(context, DagsterEventType.STEP_UP_FOR_RETRY)
    if retry_started:
        _report(context, DagsterEventType.STEP_RESTARTED)
    _set_job_status(batch_api, "Complete")

    assert not handler.check_step_health(context).is_healthy


def test_other_step_resource_init_failure_does_not_hide_unfinished_step(health_check):
    handler, instance, batch_api, _ = health_check
    context, _, _, _ = _context(instance, handler)
    _report(context, DagsterEventType.STEP_START)
    _report(context, DagsterEventType.RESOURCE_INIT_FAILURE, step_key="other_step")
    _set_job_status(batch_api, "Complete")

    assert not handler.check_step_health(context).is_healthy


@pytest.mark.parametrize("condition_type", ["Complete", "Failed"])
@pytest.mark.parametrize("phase", ["Pending", "Running", "Unknown", None])
@pytest.mark.parametrize("terminating", [False, True])
def test_terminal_job_waits_for_nonterminal_pods(health_check, condition_type, phase, terminating):
    handler, instance, batch_api, core_api = health_check
    context, _, _, _ = _context(instance, handler)
    _report(context, DagsterEventType.STEP_START)
    _set_job_status(batch_api, condition_type, failed=1)
    core_api.list_namespaced_pod.return_value = V1PodList(
        items=[
            V1Pod(
                metadata=V1ObjectMeta(
                    deletion_timestamp=datetime.now(timezone.utc) if terminating else None
                ),
                status=V1PodStatus(phase=phase),
            )
        ]
    )

    assert handler.check_step_health(context).is_healthy


@pytest.mark.parametrize("condition_type", ["Complete", "Failed"])
def test_terminal_job_with_active_pods_waits(health_check, condition_type):
    handler, instance, batch_api, core_api = health_check
    context, _, _, _ = _context(instance, handler)
    _set_job_status(batch_api, condition_type, failed=1, active=1)

    assert handler.check_step_health(context).is_healthy
    core_api.list_namespaced_pod.assert_not_called()


@pytest.mark.parametrize("retry_mode", [RetryMode.DISABLED, RetryMode.ENABLED])
@pytest.mark.parametrize("failed_count", [0, 1])
def test_evicted_pod_replacement_drives_executor_failure_or_retry(
    health_check, retry_mode, failed_count
):
    handler, instance, batch_api, core_api = health_check
    context, plan_context, execution_plan, executor = _context(
        instance, handler, retry_mode=retry_mode
    )
    # A podFailurePolicy Ignore rule can exclude the evicted pod from the failed counter.
    _set_job_status(batch_api, "Complete", failed=failed_count, succeeded=1)
    core_api.list_namespaced_pod.return_value = V1PodList(
        items=[
            V1Pod(status=V1PodStatus(phase="Failed", reason="Evicted")),
            V1Pod(status=V1PodStatus(phase="Succeeded")),
        ]
    )
    launched_attempts = []

    def launch_step(step_context):
        args = step_context.execute_step_args
        assert args.should_verify_step
        retry_state = args.known_state.get_retry_state()
        launched_attempts.append(retry_state.get_attempt_count("work"))
        if launched_attempts == [0]:
            assert verify_step(instance, step_context.dagster_run, retry_state, ["work"])
            # The first worker starts and is evicted before writing an outcome. Its replacement
            # uses the same arguments, and must exit successfully without executing the op again.
            _report(step_context, DagsterEventType.STEP_START)
            replacement_events = list(
                _execute_step_command_body(args, instance, step_context.dagster_run)
            )
            assert not any(
                event.is_step_start or event.is_step_success for event in replacement_events
            )
            assert instance.get_run_step_stats(context.dagster_run.run_id)[0].status == (
                StepEventStatus.IN_PROGRESS
            )
            return iter(())
        return _execute_step_command_body(args, instance, step_context.dagster_run)

    pop_events = executor._pop_events  # noqa: SLF001
    poll_count = 0

    def bounded_pop_events(*args):
        nonlocal poll_count
        poll_count += 1
        assert poll_count <= 10, "Completed Kubernetes Job left the Dagster step in progress"
        return pop_events(*args)

    with (
        mock.patch.object(handler, "launch_step", side_effect=launch_step),
        mock.patch.object(executor, "_pop_events", side_effect=bounded_pop_events),
    ):
        events = list(executor.execute(plan_context, execution_plan))

    stats = instance.get_run_step_stats(context.dagster_run.run_id)[0]
    if retry_mode == RetryMode.DISABLED:
        assert launched_attempts == [0]
        assert stats.status == StepEventStatus.FAILURE
        assert sum(event.is_step_failure for event in events) == 1
        assert not any(event.is_step_up_for_retry for event in events)
    else:
        assert launched_attempts == [0, 1]
        assert stats.status == StepEventStatus.SUCCESS
        assert stats.attempts == 2
        assert sum(event.is_step_up_for_retry for event in events) == 1
        assert sum(event.is_step_success for event in events) == 1
        assert not any(event.is_step_failure for event in events)
    assert any(
        "Exiting to prevent re-running the step" in entry.message
        for entry in instance.all_logs(context.dagster_run.run_id)
    )
