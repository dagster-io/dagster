from unittest import mock

from dagster import job, op
from dagster._config import process_config, resolve_to_config_type
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.init import InitExecutorContext
from dagster._core.launcher import LaunchRunContext
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster_celery_k8s.config import celery_k8s_executor_config
from dagster_celery_k8s.executor import celery_k8s_job_executor
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher


def _get_executor(instance, job_def, executor_config=None):
    process_result = process_config(
        resolve_to_config_type(celery_k8s_executor_config()),
        executor_config or {},
    )
    assert process_result.success, str(process_result.errors)

    return celery_k8s_job_executor.executor_creation_fn(
        InitExecutorContext(
            job=job_def,
            executor_def=celery_k8s_job_executor,
            executor_config=process_result.value,
            instance=instance,
        )
    )


@op
def op1():
    return


@job
def some_job():
    op1()


def celery_mock():
    # Wrap around celery into single-process queue
    celery_mock = mock.MagicMock()

    class SimpleQueueWrapper:
        queue = []

        def __init__(self, f):
            self.f = f
            self.request = mock.MagicMock()
            # self.request.hostname inside celery task definition
            self.request.hostname = "test-celery-worker-name"

        def si(self, **kwargs):
            self.queue.append(kwargs)
            return self

        def apply_async(self, **kwargs):
            from celery.result import AsyncResult

            events = []
            for task_kwargs in self.queue:
                events += self.f(self, **task_kwargs)
            # apply async must return AsyncResult
            rv = AsyncResult(id="123", task_name="execute_step_k8s_job", backend=celery_mock)
            rv.ready = lambda: True
            rv.get = lambda: events
            return rv

    celery_mock.return_value.task.return_value = lambda f: SimpleQueueWrapper(f)
    return celery_mock


def test_step_handler_with_container_context(kubeconfig_file):
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )
    recon_job = reconstructable(some_job)
    python_origin = recon_job.get_python_origin()
    default_config = dict(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret1",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
    )

    try:
        # This way of running job and op does not issue a STEP_SUCCESS event after op end
        # so Dagster engine reports that job is in unknown state and raises error.
        # try/except is a workaround - we don't care about shutdown routine in this test,
        # we only need to ensure k8s API is called with proper limits
        with instance_for_test(
            overrides={
                "run_launcher": {
                    "module": "dagster_celery_k8s",
                    "class": "CeleryK8sRunLauncher",
                    "config": default_config,
                }
            }
        ) as instance:
            executor = _get_executor(
                instance,
                recon_job,
                executor_config={
                    "per_step_k8s_config": {
                        "op1": {
                            "container_config": {
                                "resources": {
                                    "requests": {"cpu": "111m", "memory": "111Mi"},
                                    "limits": {"cpu": "222m", "memory": "222Mi"},
                                }
                            }
                        }
                    },
                    "job_image": "some-image:some-tag",
                    "load_incluster_config": False,
                },
            )
            celery_k8s_run_launcher.register_instance(instance)
            execution_plan = create_execution_plan(
                some_job,
                run_config={},
                instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
            )
            run = create_run_for_test(
                instance,
                job_name="some_job",
                status=DagsterRunStatus.STARTED,
                job_code_origin=python_origin,
                run_config={
                    "execution": {"celery-k8s": {"config": {"job_image": "some-job-image:tag"}}}
                },
            )
            loadable_target_origin = LoadableTargetOrigin(python_file=__file__)
            with in_process_test_workspace(instance, loadable_target_origin) as workspace:
                celery_k8s_run_launcher.launch_run(LaunchRunContext(run, workspace=workspace))

                log_manager = create_context_free_log_manager(instance, run)
                plan_context = PlanOrchestrationContext(
                    plan_data=PlanData(
                        job=recon_job,
                        dagster_run=run,
                        instance=instance,
                        execution_plan=execution_plan,
                        raise_on_error=True,
                        retry_mode=RetryMode.DISABLED,
                    ),
                    log_manager=log_manager,
                    executor=executor,
                    output_capture=None,
                )
                with mock.patch(
                    "dagster_celery.core_execution_loop.make_app", celery_mock()
                ), mock.patch(
                    "dagster_celery_k8s.executor.DagsterKubernetesClient.production_client",
                    mock_k8s_client_batch_api,
                ):
                    list(executor.execute(plan_context=plan_context, execution_plan=execution_plan))
    except Exception:
        pass

    expected_mock = mock_k8s_client_batch_api().batch_api.create_namespaced_job
    assert expected_mock.called
    created_containers = expected_mock.call_args.kwargs["body"].spec.template.spec.containers
    assert len(created_containers) == 1
    container = created_containers[0]
    assert container.resources.limits == {"cpu": "222m", "memory": "222Mi"}
    assert container.resources.requests == {"cpu": "111m", "memory": "111Mi"}
