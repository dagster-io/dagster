import subprocess
from unittest import mock

from dagster import (
    _check as check,
    job,
    op,
)
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.events.utils import filter_dagster_events_from_cli_logs
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test
from dagster._serdes import serialize_value, unpack_value
from dagster_celery_k8s.executor import celery_k8s_job_executor


@op(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "444m", "memory": "444Mi"},
                    "limits": {"cpu": "444m", "memory": "444Mi"},
                }
            }
        }
    }
)
def op1():
    return


@job(executor_def=celery_k8s_job_executor)
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

            serialized_events = []
            for task_kwargs in self.queue:
                # Run the mocked task
                self.f(self, **task_kwargs)

                # Run the step locally that would have run in the k8s job and return the serialized events
                execute_step_args_packed = task_kwargs["execute_step_args_packed"]
                execute_step_args = unpack_value(
                    check.dict_param(
                        execute_step_args_packed,
                        "execute_step_args_packed",
                    )
                )
                args = execute_step_args.get_command_args()
                result = subprocess.run(args, check=True, capture_output=True)
                raw_logs = result.stdout

                logs = raw_logs.decode("utf-8").split("\n")
                events = filter_dagster_events_from_cli_logs(logs)
                serialized_events += [serialize_value(event) for event in events]

            # apply async must return AsyncResult
            rv = AsyncResult(id="123", task_name="execute_step_k8s_job", backend=celery_mock)
            rv.ready = lambda: True
            rv.get = lambda: serialized_events
            return rv

    celery_mock.return_value.task.return_value = lambda f: SimpleQueueWrapper(f)
    return celery_mock


def test_per_step_k8s_config(kubeconfig_file):
    """We expected precedence order as follows:
    1. celery_k8s_job_executor is most important, it precedes everything else. Is specified, `run_config` from RunRequest is ignored.
    Precedence order:
      1) at job-s definition (via executor_def=...)
      2) at Definitions (via executor=...)
    2. after it goes run_config from request limit in schedule. If celery_k8s_job_executor is configured (via Definitions or via job), RunRequest config is ignored.
    3. Then goes tag "dagster-k8s/config" from op.

    This test only checks executor and op's overrides.
    """
    mock_k8s_client_batch_api = mock.MagicMock()

    default_config = dict(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret1",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
    )

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_celery_k8s",
                "class": "CeleryK8sRunLauncher",
                "config": default_config,
            }
        }
    ) as instance:
        run_config = {
            "execution": {
                "config": {
                    "job_image": "some-job-image:tag",
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
                    "load_incluster_config": False,
                    "kubeconfig_file": kubeconfig_file,
                }
            }
        }

        with (
            mock.patch("dagster_celery.core_execution_loop.make_app", celery_mock()),
            mock.patch(
                "dagster_celery_k8s.executor.DagsterKubernetesClient.production_client",
                mock_k8s_client_batch_api,
            ),
        ):
            result = execute_job(
                ReconstructableJob.for_file(__file__, "some_job"),
                run_config=run_config,
                instance=instance,
            )
            assert result.success

    expected_mock = mock_k8s_client_batch_api().batch_api.create_namespaced_job
    assert expected_mock.called
    created_containers = expected_mock.call_args.kwargs["body"].spec.template.spec.containers
    assert len(created_containers) == 1
    container = created_containers[0]
    assert container.image == "some-job-image:tag"
    assert container.resources.limits == {"cpu": "222m", "memory": "222Mi"}
    assert container.resources.requests == {"cpu": "111m", "memory": "111Mi"}
