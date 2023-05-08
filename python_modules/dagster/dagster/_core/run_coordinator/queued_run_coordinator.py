import logging
from typing import Any, Mapping, NamedTuple, Optional, Sequence

from typing_extensions import Self

from dagster import (
    DagsterEvent,
    DagsterEventType,
    IntSource,
    String,
    _check as check,
)
from dagster._builtins import Bool
from dagster._config import Array, Field, Noneable, ScalarUnion, Shape
from dagster._config.config_schema import UserConfigSchema
from dagster._core.instance import T_DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from .base import RunCoordinator, SubmitRunContext


class RunQueueConfig(
    NamedTuple(
        "_RunQueueConfig",
        [
            ("max_concurrent_runs", int),
            ("tag_concurrency_limits", Sequence[Mapping[str, Any]]),
            ("max_user_code_failure_retries", int),
            ("user_code_failure_retry_delay", int),
        ],
    )
):
    def __new__(
        cls,
        max_concurrent_runs: int,
        tag_concurrency_limits: Optional[Sequence[Mapping[str, Any]]],
        max_user_code_failure_retries: int = 0,
        user_code_failure_retry_delay: int = 60,
    ):
        return super(RunQueueConfig, cls).__new__(
            cls,
            check.int_param(max_concurrent_runs, "max_concurrent_runs"),
            check.opt_sequence_param(tag_concurrency_limits, "tag_concurrency_limits"),
            check.int_param(max_user_code_failure_retries, "max_user_code_failure_retries"),
            check.int_param(user_code_failure_retry_delay, "user_code_failure_retry_delay"),
        )


class QueuedRunCoordinator(RunCoordinator[T_DagsterInstance], ConfigurableClass):
    """Enqueues runs via the run storage, to be deqeueued by the Dagster Daemon process. Requires
    the Dagster Daemon process to be alive in order for runs to be launched.
    """

    def __init__(
        self,
        max_concurrent_runs: Optional[int] = None,
        tag_concurrency_limits: Optional[Sequence[Mapping[str, Any]]] = None,
        dequeue_interval_seconds: Optional[int] = None,
        dequeue_use_threads: Optional[bool] = None,
        dequeue_num_workers: Optional[int] = None,
        max_user_code_failure_retries: Optional[int] = None,
        user_code_failure_retry_delay: Optional[int] = None,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._inst_data: Optional[ConfigurableClassData] = check.opt_inst_param(
            inst_data, "inst_data", ConfigurableClassData
        )
        self._max_concurrent_runs: int = check.opt_int_param(
            max_concurrent_runs, "max_concurrent_runs", 10
        )
        check.invariant(
            self._max_concurrent_runs >= -1,
            (
                "Negative values other than -1 (which disables the limit) for max_concurrent_runs"
                " are disallowed."
            ),
        )
        self._tag_concurrency_limits: Sequence[Mapping[str, Any]] = check.opt_list_param(
            tag_concurrency_limits,
            "tag_concurrency_limits",
        )
        self._dequeue_interval_seconds: int = check.opt_int_param(
            dequeue_interval_seconds, "dequeue_interval_seconds", 5
        )
        self._dequeue_use_threads: bool = check.opt_bool_param(
            dequeue_use_threads, "dequeue_use_threads", False
        )
        self._dequeue_num_workers: Optional[int] = check.opt_int_param(
            dequeue_num_workers, "dequeue_num_workers"
        )
        self._max_user_code_failure_retries: int = check.opt_int_param(
            max_user_code_failure_retries, "max_user_code_failure_retries", 0
        )
        self._user_code_failure_retry_delay: int = check.opt_int_param(
            user_code_failure_retry_delay, "user_code_failure_retry_delay", 60
        )
        self._logger = logging.getLogger("dagster.run_coordinator.queued_run_coordinator")
        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    def get_run_queue_config(self) -> RunQueueConfig:
        return RunQueueConfig(
            max_concurrent_runs=self._max_concurrent_runs,
            tag_concurrency_limits=self._tag_concurrency_limits,
            max_user_code_failure_retries=self._max_user_code_failure_retries,
            user_code_failure_retry_delay=self._user_code_failure_retry_delay,
        )

    @property
    def dequeue_interval_seconds(self) -> int:
        return self._dequeue_interval_seconds

    @property
    def dequeue_use_threads(self) -> bool:
        return self._dequeue_use_threads

    @property
    def dequeue_num_workers(self) -> Optional[int]:
        return self._dequeue_num_workers

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {
            "max_concurrent_runs": Field(
                config=IntSource,
                is_required=False,
                description=(
                    "The maximum number of runs that are allowed to be in progress at once."
                    " Defaults to 10. Set to -1 to disable the limit. Set to 0 to stop any runs"
                    " from launching. Any other negative values are disallowed."
                ),
            ),
            "tag_concurrency_limits": Field(
                config=Noneable(
                    Array(
                        Shape(
                            {
                                "key": String,
                                "value": Field(
                                    ScalarUnion(
                                        scalar_type=String,
                                        non_scalar_schema=Shape({"applyLimitPerUniqueValue": Bool}),
                                    ),
                                    is_required=False,
                                ),
                                "limit": Field(int),
                            }
                        )
                    )
                ),
                is_required=False,
                description=(
                    "A set of limits that are applied to runs with particular tags. If a value is"
                    " set, the limit is applied to only that key-value pair. If no value is set,"
                    " the limit is applied across all values of that key. If the value is set to a"
                    " dict with `applyLimitPerUniqueValue: true`, the limit will apply to the"
                    " number of unique values for that key."
                ),
            ),
            "dequeue_interval_seconds": Field(
                config=IntSource,
                is_required=False,
                description=(
                    "The interval in seconds at which the Dagster Daemon "
                    "should periodically check the run queue for new runs to launch."
                ),
            ),
            "dequeue_use_threads": Field(
                config=bool,
                is_required=False,
                description=(
                    "Whether or not to use threads for concurrency when launching dequeued runs."
                ),
            ),
            "dequeue_num_workers": Field(
                config=IntSource,
                is_required=False,
                description=(
                    "If dequeue_use_threads is true, limit the number of concurrent worker threads."
                ),
            ),
            "max_user_code_failure_retries": Field(
                config=IntSource,
                is_required=False,
                default_value=0,
                description=(
                    "If there is an error reaching a Dagster gRPC server while dequeuing the run,"
                    " how many times to retry the dequeue before failing it. The only run launcher"
                    " that requires the gRPC server to be running is the DefaultRunLauncher, so"
                    " setting this will have no effect unless that run launcher is being used."
                ),
            ),
            "user_code_failure_retry_delay": Field(
                config=IntSource,
                is_required=False,
                default_value=60,
                description=(
                    "If there is an error reaching a Dagster gRPC server while dequeuing the run,"
                    " how long to wait before retrying any runs from that same code location. The"
                    " only run launcher that requires the gRPC server to be running is the"
                    " DefaultRunLauncher, so setting this will have no effect unless that run"
                    " launcher is being used."
                ),
            ),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(
            inst_data=inst_data,
            max_concurrent_runs=config_value.get("max_concurrent_runs"),
            tag_concurrency_limits=config_value.get("tag_concurrency_limits"),
            dequeue_interval_seconds=config_value.get("dequeue_interval_seconds"),
            dequeue_use_threads=config_value.get("dequeue_use_threads"),
            dequeue_num_workers=config_value.get("dequeue_num_workers"),
            max_user_code_failure_retries=config_value.get("max_user_code_failure_retries"),
            user_code_failure_retry_delay=config_value.get("user_code_failure_retry_delay"),
        )

    def submit_run(self, context: SubmitRunContext) -> DagsterRun:
        dagster_run = context.dagster_run

        if dagster_run.status == DagsterRunStatus.NOT_STARTED:
            enqueued_event = DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
                job_name=dagster_run.job_name,
            )
            self._instance.report_dagster_event(enqueued_event, run_id=dagster_run.run_id)
        else:
            # the run was already submitted, this is a no-op
            self._logger.warning(
                f"submit_run called for run {dagster_run.run_id} with status "
                f"{dagster_run.status.value}, skipping enqueue."
            )

        run = self._instance.get_run_by_id(dagster_run.run_id)
        if run is None:
            check.failed(f"Failed to reload run {dagster_run.run_id}")
        return run

    def cancel_run(self, run_id: str) -> bool:
        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False
        # NOTE: possible race condition if the dequeuer acts on this run at the same time
        # https://github.com/dagster-io/dagster/issues/3323
        if run.status == DagsterRunStatus.QUEUED:
            self._instance.report_run_canceling(
                run,
                message="Canceling run from the queue.",
            )
            self._instance.report_run_canceled(run)
            return True
        else:
            return self._instance.run_launcher.terminate(run_id)
