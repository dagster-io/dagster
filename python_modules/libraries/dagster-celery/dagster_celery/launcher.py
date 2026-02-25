import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from celery import Celery
from dagster import (
    DagsterInstance,
    DagsterRun,
    Field,
    Noneable,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._core.events import EngineEventData
from dagster._core.launcher import (
    CheckRunHealthResult,
    LaunchRunContext,
    ResumeRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._grpc.types import ExecuteRunArgs, ResumeRunArgs
from dagster._serdes import ConfigurableClass, ConfigurableClassData, pack_value
from typing_extensions import Self, override

from dagster_celery.config import DEFAULT_CONFIG, TASK_EXECUTE_JOB_NAME, TASK_RESUME_JOB_NAME
from dagster_celery.defaults import task_default_queue
from dagster_celery.make_app import make_app
from dagster_celery.tags import (
    DAGSTER_CELERY_QUEUE_TAG,
    DAGSTER_CELERY_RUN_PRIORITY_TAG,
    DAGSTER_CELERY_TASK_ID_TAG,
)
from dagster_celery.tasks import create_execute_job_task, create_resume_job_task

if TYPE_CHECKING:
    from celery.result import AsyncResult
    from dagster._config import UserConfigSchema


class CeleryRunLauncher(RunLauncher, ConfigurableClass):
    """Dagster [Run Launcher](https://docs.dagster.io/guides/deploy/execution/run-launchers) which
    starts runs as Celery tasks.

    Supports run worker crash detection and automatic resume. When ``run_monitoring``
    is enabled in ``dagster.yaml``, the daemon periodically calls
    ``check_run_worker_health`` which pings the Celery worker via the
    ``inspect`` API. If the worker is unreachable the run is marked as
    failed and, when ``max_resume_run_attempts > 0``, resumed on a
    healthy worker.

    Requires a persistent result backend (e.g. Redis) so that task state
    survives worker restarts.
    """

    _instance: DagsterInstance  # pyright: ignore[reportIncompatibleMethodOverride]
    celery: Celery

    def __init__(
        self,
        default_queue: str,
        broker: str | None = None,
        backend: str | None = None,
        include: list[str] | None = None,
        config_source: dict | None = None,
        inst_data: ConfigurableClassData | None = None,
    ) -> None:
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        self.broker = check.opt_str_param(broker, "broker", default=broker)
        self.backend = check.opt_str_param(backend, "backend", default=backend)
        self.include = check.opt_list_param(include, "include", of_type=str)
        self.config_source = dict(
            DEFAULT_CONFIG, **check.opt_dict_param(config_source, "config_source")
        )
        self.default_queue = check.str_param(default_queue, "default_queue")

        self.celery = make_app(
            app_args=self.app_args(),
        )

        if backend and backend.startswith("rpc://"):
            logging.getLogger(__name__).warning(
                "CeleryRunLauncher is configured with the 'rpc://' result backend. "
                "Crash detection via worker ping requires a persistent result backend "
                "(e.g. Redis). With 'rpc://', task state is lost when a worker crashes "
                "and monitoring falls back to the PENDING/UNKNOWN detection path."
            )

        super().__init__()

    def app_args(self) -> dict:
        return {
            "broker": self.broker,
            "backend": self.backend,
            "include": self.include,
            "config_source": self.config_source,
            "task_default_queue": self.default_queue,
        }

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run
        job_origin = check.not_none(run.job_code_origin)

        args = ExecuteRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=True,
        )

        task = create_execute_job_task(self.celery)
        task_signature = task.si(
            execute_job_args_packed=pack_value(args),
        )

        self._launch_celery_task_run(
            run=run,
            task_signature=task_signature,
            routing_key=TASK_EXECUTE_JOB_NAME,
        )

    def terminate(self, run_id: str) -> bool:
        run = self._instance.get_run_by_id(run_id)
        if run is None:
            return False

        task_id = run.tags[DAGSTER_CELERY_TASK_ID_TAG]

        result: AsyncResult = self.celery.AsyncResult(task_id)
        result.revoke(terminate=True)

        return True

    @property
    def supports_resume_run(self) -> bool:
        return True

    def resume_run(self, context: ResumeRunContext) -> None:
        run = context.dagster_run
        job_origin = check.not_none(run.job_code_origin)

        args = ResumeRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=True,
        )

        task = create_resume_job_task(self.celery)
        task_signature = task.si(
            resume_job_args_packed=pack_value(args),
        )

        self._launch_celery_task_run(
            run=run,
            task_signature=task_signature,
            routing_key=TASK_RESUME_JOB_NAME,
        )

    def _launch_celery_task_run(
        self,
        run: DagsterRun,
        task_signature: Celery.Task,
        routing_key: str,
    ) -> None:
        run_priority = _get_run_priority(run)
        queue = run.tags.get(DAGSTER_CELERY_QUEUE_TAG, self.default_queue)

        self._instance.report_engine_event(
            "Creating Celery run worker job task",
            run,
            cls=self.__class__,
        )

        result: AsyncResult = task_signature.apply_async(
            priority=run_priority,
            queue=queue,
            routing_key=f"{queue}.{routing_key}",
        )

        self._instance.add_run_tags(
            run.run_id,
            {DAGSTER_CELERY_TASK_ID_TAG: result.task_id},
        )

        self._instance.report_engine_event(
            "Celery task has been forwarded to the broker.",
            run,
            EngineEventData(
                {
                    "Run ID": run.run_id,
                    "Celery Task ID": result.task_id,
                    "Celery Queue": queue,
                }
            ),
            cls=self.__class__,
        )

    @property
    def supports_check_run_worker_health(self) -> bool:
        return True

    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        """Check whether the Celery worker running this task is alive."""
        task_id = run.tags[DAGSTER_CELERY_TASK_ID_TAG]

        result: AsyncResult = self.celery.AsyncResult(task_id)
        task_status = result.state

        if task_status == "SUCCESS":
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        if task_status == "FAILURE":
            return CheckRunHealthResult(WorkerStatus.FAILED, "Celery task failed.")
        if task_status == "STARTED":
            return self._check_started_task_worker_health(result)
        # Handles the PENDING and RETRYING states.
        return CheckRunHealthResult(WorkerStatus.UNKNOWN, f"Unknown task status: {task_status}")

    def _check_started_task_worker_health(self, result: "AsyncResult") -> CheckRunHealthResult:
        """When a task reports STARTED, verify the worker is still alive via inspect ping.

        With persistent result backends (e.g. Redis), the task state stays STARTED
        even after the worker crashes. We use Celery's inspect API to ping the specific
        worker and verify it's still responsive.
        """
        worker_hostname = self._get_worker_hostname(result)
        if not worker_hostname:
            # Cannot determine worker — fall back to trusting Celery state
            return CheckRunHealthResult(WorkerStatus.RUNNING)

        try:
            inspector = self.celery.control.inspect(
                destination=[worker_hostname],
                timeout=2.0,
            )
            ping_response = inspector.ping()
        except Exception:
            # If we can't reach the broker to inspect, fall back to trusting state
            return CheckRunHealthResult(WorkerStatus.RUNNING)

        if ping_response and worker_hostname in ping_response:
            return CheckRunHealthResult(WorkerStatus.RUNNING)

        return CheckRunHealthResult(
            WorkerStatus.FAILED,
            f"Celery worker {worker_hostname} is not responding to ping.",
        )

    @staticmethod
    def _get_worker_hostname(result: "AsyncResult") -> "str | None":
        """Extract the worker hostname from an AsyncResult.

        The hostname is available via result.info when the task has been started,
        or via result.worker on some backends.
        """
        # Try result.info dict (standard approach)
        info = result.info
        if isinstance(info, dict) and "hostname" in info:
            return info["hostname"]

        # Try result.worker attribute (available on some backends)
        worker = getattr(result, "worker", None)
        if isinstance(worker, str) and worker:
            return worker

        return None

    @override
    def get_run_worker_debug_info(
        self, run: DagsterRun, include_container_logs: bool | None = True
    ) -> str | None:
        task_id = run.tags[DAGSTER_CELERY_TASK_ID_TAG]

        result: AsyncResult = self.celery.AsyncResult(task_id)
        task_status = result.state
        worker = result.worker

        return str(
            {
                "run_id": run.run_id,
                "celery_task_id": task_id,
                "task_status": task_status,
                "worker": worker,
            }
        )

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> "UserConfigSchema":
        return {
            "broker": Field(
                Noneable(StringSource),
                is_required=False,
                description=(
                    "The URL of the Celery broker. Default: "
                    "'pyamqp://guest@{os.getenv('DAGSTER_CELERY_BROKER_HOST',"
                    "'localhost')}//'."
                ),
            ),
            "backend": Field(
                Noneable(StringSource),
                is_required=False,
                default_value="rpc://",
                description=(
                    "The URL of the Celery results backend. Default: 'rpc://'. "
                    "Note: crash detection via worker ping requires a persistent "
                    "backend such as Redis (e.g. 'redis://localhost:6379/0'). "
                    "The default 'rpc://' backend loses task state on worker "
                    "crash, falling back to the PENDING/UNKNOWN detection path."
                ),
            ),
            "include": Field(
                [str],
                is_required=False,
                description="List of modules every worker should import",
            ),
            "default_queue": Field(
                StringSource,
                is_required=False,
                description="The default queue to use when a run does not specify "
                "Celery queue tag.",
                default_value=task_default_queue,
            ),
            "config_source": Field(
                Noneable(Permissive()),
                is_required=False,
                description="Additional settings for the Celery app.",
            ),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)


def _get_run_priority(run: DagsterRun) -> int:
    if DAGSTER_CELERY_RUN_PRIORITY_TAG not in run.tags:
        return 0
    try:
        return int(run.tags[DAGSTER_CELERY_RUN_PRIORITY_TAG])
    except ValueError:
        return 0
