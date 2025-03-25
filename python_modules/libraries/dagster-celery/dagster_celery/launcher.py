from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional

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
from dagster._grpc import ExecuteRunArgs, ResumeRunArgs
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
    """

    _instance: DagsterInstance  # pyright: ignore[reportIncompatibleMethodOverride]
    celery: Celery

    def __init__(
        self,
        default_queue: str,
        broker: Optional[str] = None,
        backend: Optional[str] = None,
        include: Optional[list[str]] = None,
        config_source: Optional[dict] = None,
        inst_data: Optional[ConfigurableClassData] = None,
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

        task = create_resume_job_task(args)
        task_signature = task.si(
            execute_job_args_packed=pack_value(args),
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
        task_id = run.tags[DAGSTER_CELERY_TASK_ID_TAG]

        result: AsyncResult = self.celery.AsyncResult(task_id)
        task_status = result.state

        if task_status == "SUCCESS":
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        if task_status == "FAILURE":
            return CheckRunHealthResult(WorkerStatus.FAILED, "Celery task failed.")
        if task_status == "STARTED":
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        # Handles the PENDING and RETRYING states.
        return CheckRunHealthResult(WorkerStatus.UNKNOWN, f"Unknown task status: {task_status}")

    @override
    def get_run_worker_debug_info(
        self, run: DagsterRun, include_container_logs: Optional[bool] = True
    ) -> Optional[str]:
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
    def inst_data(self) -> Optional[ConfigurableClassData]:
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
                description="The URL of the Celery results backend. Default: 'rpc://'.",
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
