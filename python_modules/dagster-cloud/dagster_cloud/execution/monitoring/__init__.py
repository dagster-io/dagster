import logging
import os
import sys
import threading
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from typing import Any, NamedTuple, TypedDict, cast

import dagster._check as check
import grpc
from dagster import DagsterInstance, DagsterRunStatus
from dagster._core.launcher import CheckRunHealthResult, WorkerStatus
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, RunsFilter
from dagster._grpc.server import DagsterCodeServerUtilizationMetrics
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from typing_extensions import NotRequired

from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.util import SERVER_HANDLE_TAG, is_isolated_run


@whitelist_for_serdes
class CloudCodeServerStatus(Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


class ECSContainerResourceLimits(TypedDict):
    cpu_limit: str | None
    memory_limit: str | None


class K8sContainerResourceLimits(TypedDict):
    cpu_limit: str | None
    memory_limit: str | None
    cpu_request: str | None
    memory_request: str | None


class ServerlessContainerResourceLimits(TypedDict):
    memory_limit: str | None
    cpu_limit: str | None


class ProcessResourceLimits(TypedDict):
    cpu_limit: str | None
    memory_limit: str | None


class CloudContainerResourceLimits(TypedDict):
    ecs: NotRequired[ECSContainerResourceLimits]
    k8s: NotRequired[K8sContainerResourceLimits]
    serverless: NotRequired[ServerlessContainerResourceLimits]
    process: NotRequired[ProcessResourceLimits]


class CloudCodeServerUtilizationMetrics(DagsterCodeServerUtilizationMetrics):
    resource_limits: CloudContainerResourceLimits


class CloudCodeServerHeartbeatMetadata(TypedDict):
    utilization_metrics: NotRequired[CloudCodeServerUtilizationMetrics]


@whitelist_for_serdes
class CloudCodeServerHeartbeat(
    NamedTuple(
        "_CloudCodeServerHeartbeat",
        [
            ("location_name", str),
            ("server_status", CloudCodeServerStatus),
            ("error", SerializableErrorInfo | None),
            ("metadata", CloudCodeServerHeartbeatMetadata),
        ],
    )
):
    def __new__(
        cls,
        location_name: str,
        server_status: CloudCodeServerStatus,
        error: SerializableErrorInfo | None = None,
        metadata: Mapping[str, Any] | None = None,
    ):
        return super().__new__(
            cls,
            location_name=check.str_param(location_name, "location_name"),
            server_status=check.inst_param(server_status, "server_status", CloudCodeServerStatus),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            metadata=cast(
                "CloudCodeServerHeartbeatMetadata", check.opt_mapping_param(metadata, "metadata")
            ),
        )

    def get_code_server_utilization_metrics(self) -> CloudCodeServerUtilizationMetrics | None:
        return self.metadata.get("utilization_metrics")

    def without_messages_and_errors(self) -> "CloudCodeServerHeartbeat":
        return self._replace(
            error=None,
            metadata=cast(
                "CloudCodeServerHeartbeatMetadata",
                {},
            ),
        )


RUN_WORKER_STATUS_MESSAGE_LIMIT = int(
    os.getenv("DAGSTER_CLOUD_RUN_WORKER_STATUS_MESSAGE_SIZE_LIMIT", "1000")
)


@whitelist_for_serdes
class CloudRunWorkerStatus(
    NamedTuple(
        "_CloudRunWorkerStatus",
        [
            ("run_id", str),
            ("status_type", WorkerStatus),
            ("message", str | None),
            ("transient", bool | None),  # If the run worker failed, is there reason to retry?
            (
                "run_worker_id",
                str | None,
            ),  # unique identifier for a particular run worker
        ],
    )
):
    def __new__(
        cls,
        run_id: str,
        status_type: WorkerStatus,
        message: str | None = None,
        transient: bool | None = None,
        run_worker_id: str | None = None,
    ):
        return super().__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            status_type=check.inst_param(status_type, "status_type", WorkerStatus),
            message=check.opt_str_param(message, "message"),
            transient=check.opt_bool_param(transient, "transient", default=False),
            run_worker_id=check.opt_str_param(run_worker_id, "run_worker_id"),
        )

    @classmethod
    def from_check_run_health_result(
        cls,
        run_id: str,
        result: CheckRunHealthResult,
        run_worker_debug_info: str | None = None,
    ) -> "CloudRunWorkerStatus":
        check.inst_param(result, "result", CheckRunHealthResult)
        msg = (result.msg or "") + (f"\n{run_worker_debug_info}" if run_worker_debug_info else "")
        return CloudRunWorkerStatus(
            run_id,
            result.status,
            msg[:RUN_WORKER_STATUS_MESSAGE_LIMIT],
            transient=result.transient,
            run_worker_id=result.run_worker_id,
        )


@whitelist_for_serdes
class CloudRunWorkerStatuses(
    NamedTuple(
        "_CloudRunWorkerStatuses",
        [
            ("statuses", list[CloudRunWorkerStatus]),
            ("run_worker_monitoring_supported", bool),
            ("run_worker_monitoring_thread_alive", bool | None),
        ],
    )
):
    def __new__(
        cls,
        statuses: list[CloudRunWorkerStatus] | None,
        run_worker_monitoring_supported: bool,
        run_worker_monitoring_thread_alive: bool | None,
    ):
        return super().__new__(
            cls,
            statuses=check.opt_list_param(statuses, "statuses", of_type=CloudRunWorkerStatus),
            run_worker_monitoring_supported=check.bool_param(
                run_worker_monitoring_supported, "run_worker_monitoring_supported"
            ),
            run_worker_monitoring_thread_alive=check.opt_bool_param(
                run_worker_monitoring_thread_alive, "run_worker_monitoring_thread_alive"
            ),
        )

    def without_messages_and_errors(self) -> "CloudRunWorkerStatuses":
        return self._replace(statuses=[status._replace(message="") for status in self.statuses])


class _GetCurrentRunsError(Enum):
    UNIMPLEMENTED = "UNIMPLEMENTED"
    OTHER_ERROR = "OTHER_ERROR"


def _is_grpc_unimplemented_error(error: Exception) -> bool:
    cause = error.__cause__
    if not isinstance(cause, grpc.RpcError):
        return False
    return cause.code() == grpc.StatusCode.UNIMPLEMENTED  # type: ignore  # (bad stubs)


def _is_grpc_unknown_error(error: Exception) -> bool:
    cause = error.__cause__
    if not isinstance(cause, grpc.RpcError):
        return False
    return cause.code() == grpc.StatusCode.UNKNOWN  # type: ignore  # (bad stubs)


def get_cloud_run_worker_statuses(
    instance: DagsterCloudAgentInstance, deployment_names: Iterable[str], logger: logging.Logger
) -> Mapping[str, Sequence[CloudRunWorkerStatus]]:
    statuses: dict[str, Sequence[CloudRunWorkerStatus]] = {}

    # protected with a lock inside the method
    active_grpc_server_handles = instance.user_code_launcher.get_active_grpc_server_handles()
    active_grpc_server_handle_strings = [str(s) for s in active_grpc_server_handles]

    active_non_isolated_run_ids_by_server_handle: dict[
        str, Sequence[str] | _GetCurrentRunsError
    ] = {}
    if instance.user_code_launcher.supports_get_current_runs_for_server_handle:
        for handle in active_grpc_server_handles:
            try:
                run_ids = instance.user_code_launcher.get_current_runs_for_server_handle(handle)
                active_non_isolated_run_ids_by_server_handle[str(handle)] = run_ids
            except Exception as e:
                logger.exception(
                    f"Run monitoring: hit error with GetCurrentRunsResult for handle: {handle}"
                )
                if _is_grpc_unimplemented_error(e):
                    logger.info(
                        "Run monitoring: get_current_runs not implemented, skipping server handle"
                    )
                    active_non_isolated_run_ids_by_server_handle[str(handle)] = (
                        _GetCurrentRunsError.UNIMPLEMENTED
                    )

                # NOTE: multipex servers on version 1.1.4 and 1.1.5 had a bug where they would return
                # UNKNOWN errors for GetCurrentRuns. For backcompat, ignore it as unimplemented
                elif _is_grpc_unknown_error(e):
                    logger.info(
                        "Run monitoring: get_current_runs returned UNKNOWN error, skipping server"
                        " handle"
                    )
                    active_non_isolated_run_ids_by_server_handle[str(handle)] = (
                        _GetCurrentRunsError.UNIMPLEMENTED
                    )
                else:
                    logger.info("Run monitoring: error getting current runs for server handle")
                    active_non_isolated_run_ids_by_server_handle[str(handle)] = (
                        _GetCurrentRunsError.OTHER_ERROR
                    )

    for deployment_name in deployment_names:
        with DagsterInstance.from_ref(
            instance.ref_for_deployment(deployment_name)
        ) as scoped_instance:
            runs = scoped_instance.get_runs(RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES))
            statuses_for_deployment: list[CloudRunWorkerStatus] = []
            for run in runs:
                if is_isolated_run(run):
                    launcher = scoped_instance.run_launcher

                    try:
                        run_worker_health = launcher.check_run_worker_health(run)
                    except Exception:
                        logger.exception(
                            f"An exception occurred while checking run worker health for run '{run.run_id}'"
                        )
                        continue

                    run_worker_debug_info = None

                    if run_worker_health.status == WorkerStatus.FAILED:
                        try:
                            run_worker_debug_info = instance.run_launcher.get_run_worker_debug_info(
                                run, include_container_logs=False
                            )
                        except Exception:
                            logger.exception("Failure fetching debug info for failed run worker")

                    statuses_for_deployment.append(
                        CloudRunWorkerStatus.from_check_run_health_result(
                            run.run_id,
                            run_worker_health,
                            run_worker_debug_info,
                        )
                    )
                else:
                    if scoped_instance.is_using_isolated_agents:  # type: ignore  # (instance subclass)
                        # Not currently supported for non isolated run monitoring
                        continue

                    if run.status != DagsterRunStatus.STARTED:
                        # Rely on timeout for runs in STARTING
                        continue

                    server_handle_for_run = run.tags.get(SERVER_HANDLE_TAG)

                    if not server_handle_for_run:
                        # shouldn't be able to happen except right when a user upgrades their agent
                        # and has old runs still in progress
                        continue

                    if server_handle_for_run not in active_grpc_server_handle_strings:
                        logger.info(
                            f"Detected failure: run {run.run_id} on server"
                            f" {server_handle_for_run} is not in the active server handles"
                            f" {', '.join(active_grpc_server_handles)}"
                        )
                        statuses_for_deployment.append(
                            CloudRunWorkerStatus(
                                run.run_id,
                                WorkerStatus.FAILED,
                                "The code location server that was hosting this run is no"
                                " longer running. Upgrading to a newer version of dagster in"
                                " your asset/job code (version 1.1.4) may prevent this from"
                                " occuring.",
                            )
                        )
                        continue

                    get_runs_result_for_server_handle = (
                        active_non_isolated_run_ids_by_server_handle[server_handle_for_run]
                    )
                    if get_runs_result_for_server_handle == _GetCurrentRunsError.UNIMPLEMENTED:
                        # Server is an older version than 1.1.4- we can't fully check on the run
                        continue

                    if get_runs_result_for_server_handle == _GetCurrentRunsError.OTHER_ERROR:
                        logger.info(
                            f"Detected failure: run {run.run_id} on server {server_handle_for_run}."
                            " Server is not responding"
                        )
                        statuses_for_deployment.append(
                            CloudRunWorkerStatus(
                                run.run_id,
                                WorkerStatus.FAILED,
                                "The code location server that was hosting this run is not"
                                " responding. It may have crashed or been OOM killed.",
                            )
                        )
                        continue

                    if not isinstance(get_runs_result_for_server_handle, list):
                        check.failed(
                            "get_runs_result_for_server_handle is an unexpected type:"
                            f" {get_runs_result_for_server_handle}",
                        )

                    # If the run is not in the list of runs returned by the server, maybe the server
                    # crashed and ECS/etc. restarted it
                    if run.run_id not in get_runs_result_for_server_handle:
                        logger.info(
                            f"Detected failure: run {run.run_id} on server"
                            f" {server_handle_for_run} is not in the current runs"
                            f" {', '.join(get_runs_result_for_server_handle)}"
                        )
                        statuses_for_deployment.append(
                            CloudRunWorkerStatus(
                                run.run_id,
                                WorkerStatus.FAILED,
                                "The run process can't be found on the code location server."
                                " The server may have crashed or been OOM killed.",
                            )
                        )

            statuses[deployment_name] = statuses_for_deployment

    return statuses


def run_worker_monitoring_thread(
    instance: DagsterCloudAgentInstance,
    deployments_to_check: set[str],
    statuses_dict: dict[str, Sequence[CloudRunWorkerStatus]],
    run_worker_monitoring_lock: threading.Lock,
    shutdown_event: threading.Event,
    monitoring_interval: int | None = None,
) -> None:
    logger = logging.getLogger("dagster_cloud")
    check.inst_param(instance, "instance", DagsterCloudAgentInstance)
    logger.debug("Run Monitor thread has started")
    interval = (
        monitoring_interval
        if monitoring_interval
        else instance.dagster_cloud_run_worker_monitoring_interval_seconds
    )
    while not shutdown_event.is_set():
        run_worker_monitoring_thread_iteration(
            instance, deployments_to_check, statuses_dict, run_worker_monitoring_lock, logger
        )
        shutdown_event.wait(interval)
    logger.debug("Run monitor thread shutting down")


def run_worker_monitoring_thread_iteration(
    instance: DagsterCloudAgentInstance,
    deployments_to_check: set[str],
    statuses_dict: dict[str, Sequence[CloudRunWorkerStatus]],
    run_worker_monitoring_lock: threading.Lock,
    logger: logging.Logger,
) -> None:
    try:
        # Check the deployment names
        with run_worker_monitoring_lock:
            deployments_to_check_copy = deployments_to_check.copy()

        statuses = get_cloud_run_worker_statuses(instance, deployments_to_check_copy, logger)
        logger.debug(f"Thread got statuses: {statuses}")
        with run_worker_monitoring_lock:
            statuses_dict.clear()
            statuses_dict.update(statuses)

    except Exception:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        logger.error(f"Caught error in run monitoring thread:\n{error_info}")


def start_run_worker_monitoring_thread(
    instance: DagsterCloudAgentInstance,
    deployments_to_check: set[str],
    statuses_dict: dict[str, list[CloudRunWorkerStatus]],
    run_worker_monitoring_lock: threading.Lock,
    monitoring_interval: int | None = None,
) -> tuple[threading.Thread, threading.Event]:
    shutdown_event = threading.Event()
    thread = threading.Thread(
        target=run_worker_monitoring_thread,
        args=(
            instance,
            deployments_to_check,
            statuses_dict,
            run_worker_monitoring_lock,
            shutdown_event,
            monitoring_interval,
        ),
        name="run-monitoring",
    )
    thread.start()
    return thread, shutdown_event
