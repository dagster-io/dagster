import logging
import os
import sys
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import dagster._check as check
from dagster import DagsterInstance
from dagster._core.launcher.base import LaunchRunContext
from dagster._core.remote_origin import CodeLocationOrigin, RegisteredCodeLocationOrigin
from dagster._core.utils import FuturesAwareThreadPoolExecutor
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.types import CancelExecutionRequest
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils.cached_method import cached_method
from dagster._utils.container import retrieve_containerized_utilization_metrics
from dagster._utils.error import (
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
    truncate_serialized_error,
)
from dagster._utils.interrupts import raise_interrupts_as
from dagster._utils.merger import merge_dicts
from dagster._utils.typed_dict import init_optional_typeddict
from dagster_cloud_cli.core.errors import DagsterCloudHTTPError, raise_http_error
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from dagster_shared.record import replace

from dagster_cloud.agent.queries import (
    ADD_AGENT_HEARTBEATS_MUTATION,
    DEPLOYMENTS_QUERY,
    GET_USER_CLOUD_REQUESTS_QUERY,
    WORKSPACE_ENTRIES_QUERY,
)
from dagster_cloud.api.dagster_cloud_api import (
    AgentHeartbeat,
    AgentUtilizationMetrics,
    BatchDagsterCloudUploadApiResponse,
    DagsterCloudApi,
    DagsterCloudApiErrorResponse,
    DagsterCloudApiGrpcResponse,
    DagsterCloudApiRequest,
    DagsterCloudApiResponse,
    DagsterCloudApiSuccess,
    DagsterCloudApiThreadTelemetry,
    DagsterCloudApiUnknownCommandResponse,
    DagsterCloudUploadApiResponse,
    TimestampedError,
)
from dagster_cloud.batching import Batcher
from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.util import SERVER_HANDLE_TAG, compressed_namedtuple_upload_file, is_isolated_run
from dagster_cloud.version import __version__
from dagster_cloud.workspace.user_code_launcher import (
    DagsterCloudUserCodeLauncher,
    UserCodeLauncherEntry,
)
from dagster_cloud.workspace.user_code_launcher.utils import get_instance_ref_for_user_code

if TYPE_CHECKING:
    import datetime

CHECK_WORKSPACE_INTERVAL_SECONDS = 5

# Interval at which Agent heartbeats are sent to the host cloud
AGENT_HEARTBEAT_INTERVAL_SECONDS = 30

# Interval at which to record utilization metrics
AGENT_UTILIZATION_METRICS_INTERVAL_SECONDS = 60

AGENT_HEARTBEAT_ERROR_LIMIT = 25  # Send at most 25 errors

DEFAULT_PENDING_REQUESTS_LIMIT = 100

SLEEP_INTERVAL_SECONDS = float(os.getenv("DAGSTER_CLOUD_AGENT_SLEEP_INTERVAL_SECONDS", "0.5"))


def UPLOAD_API_RESPONSE_BATCHING_ENABLED():
    return os.getenv("DAGSTER_CLOUD_AGENT_UPLOAD_API_RESPONSE_BATCHING_ENABLED") == "true"


DEPLOYMENT_INFO_QUERY = """
    query DeploymentInfo {
         deploymentInfo {
             deploymentName
         }
     }
"""

AGENT_VERSION_LABEL = "version"
AGENT_DEFAULT_MAX_THREADS_PER_CORE = 10
AGENT_MAX_THREADPOOL_WORKERS = int(
    os.getenv(
        "DAGSTER_CLOUD_AGENT_MAX_THREADPOOL_WORKERS",
        str((os.cpu_count() or 1) * AGENT_DEFAULT_MAX_THREADS_PER_CORE),
    )
)

LIVENESS_CHECK_INTERVAL_SECONDS = float(
    os.getenv("DAGSTER_CLOUD_AGENT_LIVENESS_CHECK_INTERVAL", "15.0")
)


class DagsterCloudAgent:
    def __init__(
        self,
        instance: DagsterCloudAgentInstance,
        pending_requests_limit: int = DEFAULT_PENDING_REQUESTS_LIMIT,
    ):
        self._logger = logging.getLogger("dagster_cloud.agent")
        self._instance: DagsterCloudAgentInstance = instance

        self._batcher: defaultdict[
            str, Batcher[tuple[str, DagsterCloudUploadApiResponse], None]
        ] = defaultdict(self._batcher_factory)

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.info("Starting Dagster Cloud agent with debug logging...")
        else:
            self._logger.info("Starting Dagster Cloud agent...")

        self._exit_stack = ExitStack()
        self._iteration = 0

        self._executor = self._exit_stack.enter_context(
            FuturesAwareThreadPoolExecutor(
                max_workers=AGENT_MAX_THREADPOOL_WORKERS,
                thread_name_prefix="dagster_cloud_agent_worker",
            )
        )
        self._request_ids_to_futures: dict[str, Future] = {}
        self._utilization_metrics = init_optional_typeddict(AgentUtilizationMetrics)

        self._last_heartbeat_time: datetime.datetime | None = None

        self._last_workspace_check_time = None

        self._errors: deque = deque(
            maxlen=AGENT_HEARTBEAT_ERROR_LIMIT
        )  # (SerializableErrorInfo, timestamp) tuples

        self._pending_requests: list[dict[str, Any]] = []
        self._locations_with_pending_requests: set[tuple[str, str, bool]] = set()
        self._ready_requests: list[dict[str, Any]] = []

        self._location_query_times: dict[tuple[str, str, bool], float] = {}
        self._pending_requests_limit = check.int_param(
            pending_requests_limit, "pending_requests_limit"
        )
        self._active_deployments: set[tuple[str, bool]] = (  # deployment_name, is_branch_deployment
            set()
        )

        self._last_liveness_check_time = None

        self._warned_about_long_in_progress_reconcile = False

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    def _batcher_factory(
        self,
    ) -> Batcher[tuple[str, DagsterCloudUploadApiResponse], None]:
        return Batcher(
            "upload_api_response",
            self._batch_upload_api_response,
            max_wait_ms=50,
            max_batch_size=32,
        )

    @property
    def _active_deployment_names(self):
        return [deployment[0] for deployment in self._active_deployments]

    @property
    def _active_full_deployment_names(self):
        return [deployment[0] for deployment in self._active_deployments if not deployment[1]]

    def _check_initial_deployment_names(self):
        if self._instance.deployment_names:
            result = self._instance.organization_scoped_graphql_client().execute(
                DEPLOYMENTS_QUERY,
                variable_values={"deploymentNames": self._instance.deployment_names},
            )
            deployments = result["data"]["deployments"]
            existing_deployment_names = {deployment["deploymentName"] for deployment in deployments}
            requested_deployment_names = set(self._instance.deployment_names)
            missing_deployment_names = requested_deployment_names.difference(
                existing_deployment_names
            )

            if missing_deployment_names:
                deployment_str = f"deployment{'s' if len(missing_deployment_names) > 1 else ''} {', '.join(missing_deployment_names)}"
                raise Exception(
                    f"Agent is configured to serve an invalid {deployment_str}. Check your"
                    " agent configuration to make sure it is serving the correct deployment.",
                )

    def _update_agent_resource_limits(
        self, user_code_launcher: DagsterCloudUserCodeLauncher
    ) -> None:
        # The agent should have environment variables defining its resource requests and limits.
        # However, the agent may be running in a container with resource limits that are different
        # For example, on k8s there are ways to effect change on the cpu limit, like mutating admission webhooks.
        # Since the effective cgroup limits precede actual hosts resources when it comes to actual behavior for
        # throttling and oom kills, we attempt to obtain these and fallback on the environment variables.
        container_utilization_metrics = self._utilization_metrics.get("container_utilization", {})
        memory_limit = container_utilization_metrics.get("memory_limit")
        if not memory_limit:
            memory_limit = os.getenv("DAGSTER_CLOUD_AGENT_MEMORY_LIMIT")
            self._logger.info(
                "Cannot obtain cgroup memory limit, using environment value: "
                f"DAGSTER_CLOUD_AGENT_MEMORY_LIMIT={memory_limit}"
            )

        cpu_cfs_period_us = container_utilization_metrics.get("cpu_cfs_period_us")
        cpu_cfs_quota_us = container_utilization_metrics.get("cpu_cfs_quota_us")

        cpu_limit = None
        if cpu_cfs_quota_us and cpu_cfs_period_us:
            cpu_limit = (
                1000.0 * cpu_cfs_quota_us
            ) / cpu_cfs_period_us  # cpu_limit expressed in milliseconds of cpu

        if not cpu_limit:
            cpu_limit = os.getenv("DAGSTER_CLOUD_AGENT_CPU_LIMIT")
            self._logger.info(
                "Cannot obtain CPU CFS values, using environment value: "
                f"DAGSTER_CLOUD_AGENT_CPU_LIMIT={cpu_limit}"
            )

        if not user_code_launcher.user_code_deployment_type.supports_utilization_metrics:
            self._logger.info(
                f"Cannot interpret resource limits for agent type {user_code_launcher.user_code_deployment_type.value}."
                "Skipping utilization metrics retrieval."
            )
            return

        limits = {
            "cpu_limit": cpu_limit,
            "memory_limit": memory_limit,
        }

        cpu_request = os.getenv("DAGSTER_CLOUD_AGENT_CPU_REQUEST")
        memory_request = os.getenv("DAGSTER_CLOUD_AGENT_MEMORY_REQUEST")
        if cpu_request:
            limits["cpu_request"] = cpu_request
        if memory_request:
            limits["memory_request"] = memory_request

        self._utilization_metrics["resource_limits"][
            user_code_launcher.user_code_deployment_type.value
        ] = limits

    def _update_utilization_metrics(self, user_code_launcher: DagsterCloudUserCodeLauncher):
        container_utilization_metrics = retrieve_containerized_utilization_metrics(
            logger=self._logger,
            previous_measurement_timestamp=self._utilization_metrics["container_utilization"][
                "measurement_timestamp"
            ],
            previous_cpu_usage=self._utilization_metrics["container_utilization"]["cpu_usage"],
        )
        self._utilization_metrics["request_utilization"].update(
            self._executor.get_current_utilization_metrics()
        )
        self._utilization_metrics["container_utilization"].update(container_utilization_metrics)

        self._update_agent_resource_limits(user_code_launcher)

        self._logger.info(f"Current utilization metrics: {self._utilization_metrics}")

    def run_loop(
        self,
        user_code_launcher,
        agent_uuid,
    ):
        heartbeat_interval_seconds = AGENT_HEARTBEAT_INTERVAL_SECONDS

        if (
            not self._instance.includes_branch_deployments
            and not self._instance.deployment_names
            and not self._instance.include_all_serverless_deployments
        ):
            self._logger.info(
                "Deployment name was not set - checking to see if it can be fetched from the"
                " server..."
            )
            # Fetch the deployment name from the server if it isn't set (only true
            # for old agents, and only will work if there's a single deployment in the org)
            result = self._instance.graphql_client.execute(DEPLOYMENT_INFO_QUERY)
            deployment_name = result["data"]["deploymentInfo"]["deploymentName"]
            self._instance = self._exit_stack.enter_context(  # ty: ignore[invalid-assignment]
                DagsterInstance.from_ref(
                    self._instance.ref_for_deployment(deployment_name)
                )  # (instance subclass)
            )

        self._check_initial_deployment_names()

        serving = []
        queues = list(filter(None, self._instance.agent_queues_config.queues))
        if queues:
            serving.append(f"queues{queues}")
        if self._instance.deployment_names:
            serving.append(f"deployments{self._instance.deployment_names}")
        if self._instance.include_all_serverless_deployments:
            serving.append("all serverless deployments")
        if self._instance.includes_branch_deployments:
            serving.append("branch deployments")

        self._logger.info(f"Agent is serving: {', '.join(serving)}")

        self._check_update_workspace(
            user_code_launcher,
            upload_outdated=user_code_launcher.upload_outdated_snapshots_on_startup,
        )

        self._logger.info(
            f"Will start polling for requests from {self._instance.dagster_cloud_url} once user code has"
            " been loaded."
        )

        heartbeat_error_size_limit = int(os.getenv("DAGSTER_CLOUD_AGENT_ERROR_SIZE_LIMIT", "10000"))

        while True:
            try:
                for error in self.run_iteration(user_code_launcher):
                    if error:
                        self._logger.error(str(error))
                        self._errors.appendleft(
                            (
                                truncate_serialized_error(
                                    error, heartbeat_error_size_limit, max_depth=3
                                ),
                                get_current_datetime(),
                            )
                        )
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.error(f"Caught error:\n{error_info}")
                self._errors.appendleft(
                    (
                        truncate_serialized_error(
                            error_info, heartbeat_error_size_limit, max_depth=3
                        ),
                        get_current_datetime(),
                    )
                )

            # Check for any received interrupts
            with raise_interrupts_as(KeyboardInterrupt):
                pass

            if user_code_launcher.ready_to_serve_requests:
                try:
                    self._check_add_heartbeat(agent_uuid, heartbeat_interval_seconds)
                except Exception:
                    self._logger.exception("Failed to add heartbeat")

            self._check_for_long_running_reconcile(user_code_launcher)

            # Check for any received interrupts
            with raise_interrupts_as(KeyboardInterrupt):
                pass

            try:
                self._check_update_workspace(user_code_launcher, upload_outdated=False)

            except Exception:
                self._logger.error(
                    f"Failed to check for workspace updates: \n{serializable_error_info_from_exc_info(sys.exc_info())}"
                )

            self._write_liveness_sentinel_if_overdue(user_code_launcher.sentinel_dir)

            # Check for any received interrupts
            with raise_interrupts_as(KeyboardInterrupt):
                time.sleep(SLEEP_INTERVAL_SECONDS)

    def _write_liveness_sentinel_if_overdue(self, sentinel_dir: str | None):
        if self._last_liveness_check_time is False:
            return
        if not sentinel_dir:
            return

        now = time.time()
        if self._last_liveness_check_time is None:
            self._logger.info("Starting liveness sentinel")
        elif self._last_liveness_check_time + LIVENESS_CHECK_INTERVAL_SECONDS > now:
            return

        try:
            if not os.access(sentinel_dir, os.W_OK):
                self._logger.warning(
                    f"Disabling liveness sentinel - {sentinel_dir} is not writable"
                )
                self._last_liveness_check_time = False
                return
            Path(sentinel_dir, "liveness_sentinel.txt").touch(exist_ok=True)
            self._last_liveness_check_time = now
        except Exception as e:
            self._logger.error(f"Failed to write liveness sentinel and disabling it: {e}")
            self._last_liveness_check_time = False

    def _check_for_long_running_reconcile(self, user_code_launcher):
        """Detect from the main thread if the background reconcile thread is running behind or has gotten stuck."""
        in_progress_reconcile_start_time = user_code_launcher.in_progress_reconcile_start_time

        reconcile_start_time_warning = int(
            os.getenv("DAGSTER_CLOUD_AGENT_RECONCILE_START_TIME_WARNING", "3600")
        )

        if (
            in_progress_reconcile_start_time is not None
            and (time.time() - in_progress_reconcile_start_time) >= reconcile_start_time_warning
        ):
            if not self._warned_about_long_in_progress_reconcile:
                self._logger.warning(
                    f"Agent has been redeploying code servers for more than {reconcile_start_time_warning} seconds. This may indicate the background thread that performs the redeploys is stuck."
                )
                self._warned_about_long_in_progress_reconcile = True
        else:
            self._warned_about_long_in_progress_reconcile = False

    def _check_update_workspace(self, user_code_launcher, upload_outdated):
        curr_time = get_current_datetime()

        if (
            self._last_workspace_check_time
            and (curr_time - self._last_workspace_check_time).total_seconds()
            < CHECK_WORKSPACE_INTERVAL_SECONDS
        ):
            return

        self._last_workspace_check_time = curr_time
        self._query_for_workspace_updates(user_code_launcher, upload_outdated=upload_outdated)

    def _check_add_heartbeat(
        self,
        agent_uuid,
        heartbeat_interval_seconds,
    ):
        curr_time = get_current_datetime()

        if (
            self._last_heartbeat_time
            and (curr_time - self._last_heartbeat_time).total_seconds() < heartbeat_interval_seconds
        ):
            return

        errors = [
            TimestampedError(
                timestamp=timestamp.timestamp(),
                error=error,
            )
            for (error, timestamp) in self._errors
            if timestamp.timestamp() > curr_time.timestamp() - 60 * 60 * 24
        ]

        run_worker_statuses_dict = self._instance.user_code_launcher.get_cloud_run_worker_statuses(
            self._active_deployment_names
        )

        code_server_heartbeats_dict = self._instance.user_code_launcher.get_grpc_server_heartbeats()

        agent_image_tag = os.getenv("DAGSTER_CLOUD_AGENT_IMAGE_TAG")
        if self._instance.user_code_launcher.agent_metrics_enabled:
            num_running_requests = self._utilization_metrics["request_utilization"][
                "num_running_requests"
            ]
            max_concurrent_requests = self._utilization_metrics["request_utilization"][
                "max_concurrent_requests"
            ]
            self._logger.info(
                f"Current agent threadpool utilization: {num_running_requests}/{max_concurrent_requests} threads"
            )

        self._last_heartbeat_time = curr_time

        heartbeats = {
            deployment_name: AgentHeartbeat(
                timestamp=curr_time.timestamp(),
                agent_id=agent_uuid,
                agent_label=self._instance.dagster_cloud_api_agent_label,
                agent_type=(
                    type(self._instance.user_code_launcher).__name__
                    if self._instance.user_code_launcher
                    else None
                ),
                metadata=merge_dicts(
                    {AGENT_VERSION_LABEL: __version__},
                    {"image_tag": agent_image_tag} if agent_image_tag else {},
                    {
                        "utilization_metrics": self._utilization_metrics
                        if self._instance.user_code_launcher.agent_metrics_enabled
                        else {}
                    },
                    {
                        "allowed_full_deployment_locations": self._instance.allowed_full_deployment_locations
                        if self._instance.allowed_full_deployment_locations
                        else {},
                    },
                    {
                        "allowed_branch_deployment_locations": self._instance.allowed_branch_deployment_locations
                        if self._instance.allowed_branch_deployment_locations
                        else [],
                    },
                ),
                run_worker_statuses=run_worker_statuses_dict[deployment_name],
                code_server_heartbeats=code_server_heartbeats_dict.get(deployment_name, []),
                agent_queues_config=self._instance.agent_queues_config,
            )
            for deployment_name in self._active_deployment_names
        }

        serialized_agent_heartbeats = [
            {
                "deploymentName": deployment_name,
                "serializedAgentHeartbeat": serialize_value(heartbeat),
            }
            for deployment_name, heartbeat in heartbeats.items()
        ]

        serialized_errors = [serialize_value(error) for error in errors]
        try:
            self._instance.organization_scoped_graphql_client().execute(
                ADD_AGENT_HEARTBEATS_MUTATION,
                variable_values={
                    "serializedAgentHeartbeats": serialized_agent_heartbeats,
                    "serializedErrors": serialized_errors,
                },
                idempotent_mutation=True,
            )
        except DagsterCloudHTTPError as e:
            if e.response.status_code == 413:
                heartbeats_size = sum([len(heartbeat) for heartbeat in serialized_agent_heartbeats])
                errors_size = sum([len(error) for error in serialized_errors])

                error_message = f"Request with {heartbeats_size} heartbeat bytes and {errors_size} error bytes was too large, submitting a smaller heartbeat without messages and stack traces."
                self._logger.exception(error_message)

                serialized_agent_heartbeats = [
                    {
                        "deploymentName": deployment_name,
                        "serializedAgentHeartbeat": serialize_value(
                            heartbeat.without_messages_and_errors()
                        ),
                    }
                    for deployment_name, heartbeat in heartbeats.items()
                ]

                self._instance.organization_scoped_graphql_client().execute(
                    ADD_AGENT_HEARTBEATS_MUTATION,
                    variable_values={
                        "serializedAgentHeartbeats": serialized_agent_heartbeats,
                        "serializedErrors": [
                            serialize_value(
                                TimestampedError(
                                    timestamp=curr_time.timestamp(),
                                    error=SerializableErrorInfo(
                                        error_message,
                                        stack=[],
                                        cls_name=None,
                                    ),
                                )
                            )
                        ],
                    },
                    idempotent_mutation=True,
                )
            else:
                raise

    @property
    def executor(self) -> ThreadPoolExecutor:
        return self._executor

    @property
    def request_ids_to_futures(self) -> dict[str, Future]:
        return self._request_ids_to_futures

    def _upload_outdated_workspace_entries(
        self,
        deployment_name: str,
        is_branch_deployment: bool,
        user_code_launcher: DagsterCloudUserCodeLauncher,
    ):
        result = self._instance.graphql_client_for_deployment(deployment_name).execute(
            WORKSPACE_ENTRIES_QUERY,
            variable_values={
                "deploymentNames": [deployment_name],
                "includeAllServerlessDeployments": False,
                "agentQueues": self._instance.agent_queues_config.queues,
            },
        )
        entries = result["data"]["deployments"][0]["workspaceEntries"]

        upload_metadata = {}
        control_plane_error_locations: set[tuple[str, str]] = set()
        control_plane_outdated_locations: set[tuple[str, str]] = set()

        for entry in entries:
            location_name = entry["locationName"]

            # Skip locations not in the allowed list if configured
            if not self._instance.is_location_allowed(
                deployment_name, location_name, is_branch_deployment
            ):
                deployment_type = (
                    "for branch deployments"
                    if is_branch_deployment
                    else f"in deployment {deployment_name}"
                )
                self._logger.error(
                    f"Skipping location {location_name} {deployment_type} - not in allowed locations list. "
                    "Either configure this location's dagster_cloud.yaml file to use a different queue, "
                    "or redeploy this agent with this location in the list of allowed locations."
                )
                continue

            location_key = (deployment_name, location_name)

            if entry["hasLoadError"]:
                control_plane_error_locations.add(location_key)
            if entry["hasOutdatedData"]:
                control_plane_outdated_locations.add(location_key)

            code_location_deploy_data = deserialize_value(
                entry["serializedDeploymentMetadata"], CodeLocationDeployData
            )
            if entry["hasOutdatedData"]:
                # Spin up a server for this location and upload its metadata to Cloud
                # (Bump the TTL counter as well to leave the server up - ensure that a slighty
                # different timestamp is chosen for each location to break ties)
                self._location_query_times[
                    (deployment_name, location_name, is_branch_deployment)
                ] = time.time()
                upload_metadata[location_key] = UserCodeLauncherEntry(
                    code_location_deploy_data=code_location_deploy_data,
                    update_timestamp=float(entry["metadataTimestamp"]),
                )

        user_code_launcher.add_upload_metadata_for_deployment(
            deployment_name,
            upload_metadata,
            control_plane_error_locations=control_plane_error_locations,
            control_plane_outdated_locations=control_plane_outdated_locations,
        )

    def _has_ttl(self, user_code_launcher, is_branch_deployment):
        # branch deployments always have TTLs, other deployments only if you asked for it specifically
        return is_branch_deployment or user_code_launcher.server_ttl_enabled_for_full_deployments

    def _get_ttl_seconds(self, is_branch_deployment):
        return (
            self._instance.user_code_launcher.branch_deployment_ttl_seconds
            if is_branch_deployment
            else self._instance.user_code_launcher.full_deployment_ttl_seconds
        )

    def _get_locations_with_ttl_to_query(self, user_code_launcher) -> list[tuple[str, str]]:
        now = time.time()

        # For the deployments with TTLs, decide which locations to consider
        # Include the location if:
        # - a) There's a pending request in the queue for it
        # - b) It's TTL hasn't expired since the last time somebody asked for it
        # Always include locations in a), and add locations from b) until you hit a limit
        location_candidates: set[tuple[str, str, float]] = {
            (deployment, location, -1.0)  # Score below 0 so that they're at the front of the list
            for deployment, location, is_branch_deployment in self._locations_with_pending_requests
            if self._has_ttl(user_code_launcher, is_branch_deployment)
        }

        num_locations_to_query = self._instance.user_code_launcher.server_ttl_max_servers

        if len(location_candidates) > num_locations_to_query:
            self._logger.warning(
                f"Temporarily keeping {len(location_candidates)} servers with pending requests "
                f"running, which is more than the configured {num_locations_to_query} servers."
            )
            return [(deployment, location) for deployment, location, _score in location_candidates]

        for location_entry, query_time in self._location_query_times.items():
            if location_entry in self._locations_with_pending_requests:
                # Skip locations that are already in location_candidates due to having
                # pending requests
                continue

            deployment_name, location, is_branch_deployment = location_entry

            if not self._has_ttl(user_code_launcher, is_branch_deployment):
                continue

            time_since_last_query = now - query_time

            if time_since_last_query >= self._get_ttl_seconds(is_branch_deployment):
                continue

            location_candidates.add((deployment_name, location, time_since_last_query))

        sorted_results = sorted(location_candidates, key=lambda x: x[2])

        # sort by time since last query asending and return the first N
        filtered_results = sorted_results[:num_locations_to_query]

        num_left_out = len(sorted_results) - num_locations_to_query

        if num_left_out > 0:
            self._logger.warning(
                f"{len(sorted_results)} locations have been queried within TTL, but "
                f"filtering out {num_left_out} to stay within {num_locations_to_query}"
            )

        return [(deployment, location) for deployment, location, _score in filtered_results]

    def _query_for_workspace_updates(
        self,
        user_code_launcher: DagsterCloudUserCodeLauncher,
        upload_outdated: bool,
    ):
        locations_with_ttl_to_query = self._get_locations_with_ttl_to_query(user_code_launcher)

        deployments_to_query = {key[0] for key in locations_with_ttl_to_query}

        if locations_with_ttl_to_query:
            locations_str = ", ".join(
                f"{deployment}:{location}" for deployment, location in locations_with_ttl_to_query
            )
            self._logger.debug(f"Querying for the following locations with TTL: {locations_str}")

        # If you have specified a non-branch deployment and no TTL, always consider it
        if self._instance.deployment_names:
            deployments_to_query = deployments_to_query.union(set(self._instance.deployment_names))

        # Create mapping of
        # - location name => deployment metadata
        deployment_map: dict[tuple[str, str], UserCodeLauncherEntry] = {}
        all_locations: set[tuple[str, str]] = set()

        self._active_deployments = set()
        control_plane_error_locations: set[tuple[str, str]] = set()
        control_plane_outdated_locations: set[tuple[str, str]] = set()

        if deployments_to_query or self._instance.include_all_serverless_deployments:
            result = self._instance.organization_scoped_graphql_client().execute(
                WORKSPACE_ENTRIES_QUERY,
                variable_values={
                    "deploymentNames": list(deployments_to_query),
                    "includeAllServerlessDeployments": self._instance.include_all_serverless_deployments,
                    "agentQueues": self._instance.agent_queues_config.queues,
                },
            )

            for deployment_result in result["data"]["deployments"]:
                deployment_name = deployment_result["deploymentName"]
                is_branch_deployment = deployment_result["isBranchDeployment"]

                self._active_deployments.add((deployment_name, is_branch_deployment))

                entries = deployment_result["workspaceEntries"]

                for entry in entries:
                    location_name = entry["locationName"]

                    # Skip locations not in the allowed list if configured
                    if not self._instance.is_location_allowed(
                        deployment_name, location_name, is_branch_deployment
                    ):
                        deployment_type = (
                            "for branch deployments"
                            if is_branch_deployment
                            else f"in deployment {deployment_name}"
                        )
                        self._logger.error(
                            f"Skipping location {location_name} {deployment_type} - not in allowed locations list. "
                            "Either configure this location's dagster_cloud.yaml file to use a different queue, "
                            "or redeploy this agent with this location in the list of allowed locations."
                        )
                        continue

                    location_key = (deployment_name, location_name)

                    all_locations.add(location_key)

                    if entry["hasLoadError"]:
                        control_plane_error_locations.add(location_key)
                    if entry["hasOutdatedData"]:
                        control_plane_outdated_locations.add(location_key)

                    code_location_deploy_data = deserialize_value(
                        entry["serializedDeploymentMetadata"], CodeLocationDeployData
                    )

                    # The GraphQL can return a mix of deployments with TTLs (for example, all
                    # branch deployments, and also full deployments if you have that configured)
                    # and locations without TTLs (for example, full deployments). Deployments
                    # without TTLs always include all of their locations. Deployments with TTLs
                    # only include the locations within locations_with_ttl_to_query.
                    if not self._has_ttl(
                        user_code_launcher, is_branch_deployment
                    ) or location_key in cast("set[tuple[str, str]]", locations_with_ttl_to_query):
                        deployment_map[location_key] = UserCodeLauncherEntry(
                            code_location_deploy_data=code_location_deploy_data,
                            update_timestamp=float(entry["metadataTimestamp"]),
                        )

        if len(deployment_map):
            update_str = ", ".join(
                f"{deployment}:{location}" for deployment, location in deployment_map.keys()
            )
            self._logger.debug(f"Reconciling with the following locations: {update_str}")
        else:
            self._logger.debug("Reconciling with no locations")

        tracked_error_locations = control_plane_error_locations.intersection(deployment_map.keys())
        tracked_outdated_locations = control_plane_outdated_locations.intersection(
            deployment_map.keys()
        )

        user_code_launcher.update_grpc_metadata(
            deployment_map,
            control_plane_error_locations=tracked_error_locations,
            control_plane_outdated_locations=tracked_outdated_locations,
            upload_outdated=upload_outdated,
        )

        # Tell run worker monitoring which deployments it should care about
        user_code_launcher.update_run_worker_monitoring_deployments(self._active_deployment_names)

        # In the rare event that there are pending requests that are no longer in the workspace at
        # all (if, say, a location is removed while requests are enqueued), they should be forcibly
        # moved to ready so that they don't stay pending forever - callsites will get an error
        # about the location not existing, but that's preferable to slowly timing out
        pending_requests_copy = self._pending_requests.copy()
        self._pending_requests = []
        for json_request in pending_requests_copy:
            location_name = self._get_location_from_request(json_request)
            deployment_name = json_request["deploymentName"]
            if (deployment_name, location_name) not in all_locations:
                self._ready_requests.append(json_request)
            else:
                self._pending_requests.append(json_request)

    def _get_grpc_client(
        self,
        user_code_launcher: DagsterCloudUserCodeLauncher,
        deployment_name: str,
        location_name: str,
    ) -> DagsterGrpcClient:
        endpoint = user_code_launcher.get_grpc_endpoint(deployment_name, location_name)
        return endpoint.create_client()

    def _get_location_origin_from_request(
        self,
        request: DagsterCloudApiRequest,
    ) -> CodeLocationOrigin | None:
        """Derive the location from the specific argument passed in to a dagster_cloud_api call."""
        api_name = request.request_api
        if api_name in {
            DagsterCloudApi.GET_EXTERNAL_EXECUTION_PLAN,
            DagsterCloudApi.GET_SUBSET_EXTERNAL_PIPELINE_RESULT,
        }:
            external_pipeline_origin = request.request_args.job_origin
            return external_pipeline_origin.repository_origin.code_location_origin
        elif api_name in {
            DagsterCloudApi.GET_EXTERNAL_PARTITION_CONFIG,
            DagsterCloudApi.GET_EXTERNAL_PARTITION_TAGS,
            DagsterCloudApi.GET_EXTERNAL_PARTITION_NAMES,
            DagsterCloudApi.GET_EXTERNAL_PARTITION_SET_EXECUTION_PARAM_DATA,
            DagsterCloudApi.GET_EXTERNAL_SCHEDULE_EXECUTION_DATA,
            DagsterCloudApi.GET_EXTERNAL_SENSOR_EXECUTION_DATA,
        }:
            return request.request_args.repository_origin.code_location_origin
        elif api_name == DagsterCloudApi.GET_EXTERNAL_NOTEBOOK_DATA:
            return request.request_args.code_location_origin
        elif api_name == DagsterCloudApi.PING_LOCATION:
            return RegisteredCodeLocationOrigin(request.request_args.location_name)
        else:
            return None

    @cached_method
    def _get_user_code_instance_ref(self, deployment_name: str):
        return get_instance_ref_for_user_code(self._instance.ref_for_deployment(deployment_name))

    def _handle_api_request(
        self,
        request: DagsterCloudApiRequest,
        deployment_name: str,
        is_branch_deployment: bool,
        user_code_launcher: DagsterCloudUserCodeLauncher,
    ) -> DagsterCloudApiSuccess | DagsterCloudApiGrpcResponse:
        api_name = request.request_api

        code_location_origin = self._get_location_origin_from_request(request)
        location_name = code_location_origin.location_name if code_location_origin else None

        # Validate that the location is in the allowed list if configured
        if location_name and not self._instance.is_location_allowed(
            deployment_name, location_name, is_branch_deployment
        ):
            deployment_type = (
                "for branch deployments"
                if is_branch_deployment
                else f"in deployment '{deployment_name}'"
            )
            raise Exception(
                f"Agent is not allowed to serve location '{location_name}' {deployment_type}. "
                f"Location is not in the allowed locations list configured for this agent. "
                "Either configure this location's dagster_cloud.yaml file to use a different queue, "
                "or redeploy this agent with this location in the list of allowed locations."
            )

        if api_name == DagsterCloudApi.PING_LOCATION:
            # Do nothing - this request only exists to bump TTL for the location
            return DagsterCloudApiSuccess()
        elif api_name == DagsterCloudApi.CHECK_FOR_WORKSPACE_UPDATES:
            # Dagster Cloud has requested that we upload new metadata for any out of date locations in
            # the workspace
            self._upload_outdated_workspace_entries(
                deployment_name, is_branch_deployment, user_code_launcher
            )
            return DagsterCloudApiSuccess()
        elif api_name == DagsterCloudApi.GET_EXTERNAL_EXECUTION_PLAN:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            serialized_snapshot_or_error = client.execution_plan_snapshot(
                execution_plan_snapshot_args=replace(
                    request.request_args,
                    instance_ref=self._get_user_code_instance_ref(deployment_name),
                )
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_snapshot_or_error
            )

        elif api_name == DagsterCloudApi.GET_SUBSET_EXTERNAL_PIPELINE_RESULT:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )

            serialized_subset_result_or_error = client.external_pipeline_subset(
                pipeline_subset_snapshot_args=request.request_args
            )

            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_subset_result_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_PARTITION_CONFIG:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            serialized_partition_config_or_error = client.external_partition_config(
                partition_args=request.request_args,
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_partition_config_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_PARTITION_TAGS:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            serialized_partition_tags_or_error = client.external_partition_tags(
                partition_args=request.request_args,
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_partition_tags_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_PARTITION_NAMES:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            serialized_partition_names_or_error = client.external_partition_names(
                partition_names_args=request.request_args,
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_partition_names_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_PARTITION_SET_EXECUTION_PARAM_DATA:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            serialized_partition_execution_params_or_error = (
                client.external_partition_set_execution_params(
                    partition_set_execution_param_args=request.request_args
                )
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_partition_execution_params_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_SCHEDULE_EXECUTION_DATA:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )

            args = replace(
                request.request_args,
                instance_ref=self._get_user_code_instance_ref(deployment_name),
            )

            serialized_schedule_data_or_error = client.external_schedule_execution(
                external_schedule_execution_args=args,
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_schedule_data_or_error
            )

        elif api_name == DagsterCloudApi.GET_EXTERNAL_SENSOR_EXECUTION_DATA:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )

            args = replace(
                request.request_args,
                instance_ref=self._get_user_code_instance_ref(deployment_name),
            )

            serialized_sensor_data_or_error = client.external_sensor_execution(
                sensor_execution_args=args,
            )
            return DagsterCloudApiGrpcResponse(
                serialized_response_or_error=serialized_sensor_data_or_error
            )
        elif api_name == DagsterCloudApi.GET_EXTERNAL_NOTEBOOK_DATA:
            client = self._get_grpc_client(
                user_code_launcher, deployment_name, cast("str", location_name)
            )
            response = client.external_notebook_data(request.request_args.notebook_path)
            return DagsterCloudApiGrpcResponse(serialized_response_or_error=response.decode())
        elif api_name == DagsterCloudApi.LAUNCH_RUN:
            run = request.request_args.dagster_run

            with DagsterInstance.from_ref(
                self._get_user_code_instance_ref(deployment_name)
            ) as scoped_instance:
                scoped_instance.report_engine_event(
                    f"{self._instance.agent_display_name} is launching run {run.run_id}",
                    run,
                    cls=self.__class__,
                )

                scoped_instance.add_run_tags(
                    run.run_id,
                    merge_dicts(
                        (
                            {"dagster/agent_label": self._instance.dagster_cloud_api_agent_label}
                            if self._instance.dagster_cloud_api_agent_label
                            else {}
                        ),
                        {"dagster/agent_id": self._instance.instance_uuid},
                    ),
                )

                launcher = scoped_instance.get_run_launcher_for_run(run)  # type: ignore  # (instance subclass)

                if is_isolated_run(run):
                    launcher.launch_run(LaunchRunContext(dagster_run=run, workspace=None))
                else:
                    scoped_instance.report_engine_event(
                        f"Launching {run.run_id} without an isolated run environment.",
                        run,
                        cls=self.__class__,
                    )

                    run_location_name = cast(
                        "str",
                        run.remote_job_origin.repository_origin.code_location_origin.location_name,
                    )

                    server = user_code_launcher.get_grpc_server(deployment_name, run_location_name)

                    # Record the server handle that we launched it on to for run monitoring
                    scoped_instance.add_run_tags(
                        run.run_id, new_tags={SERVER_HANDLE_TAG: str(server.server_handle)}
                    )

                    launcher.launch_run_from_grpc_client(
                        scoped_instance, run, server.server_endpoint.create_client()
                    )

                return DagsterCloudApiSuccess()
        elif api_name == DagsterCloudApi.TERMINATE_RUN:
            # With isolated agents enabled:
            # Run workers now poll for run status. We don't use the run launcher to terminate.
            # Once min agent version is bumped, we can deprecate this command.
            # For backcompat, we use the run launcher to terminate unless the user opts in.
            run = request.request_args.dagster_run

            with DagsterInstance.from_ref(
                self._instance.ref_for_deployment(deployment_name)
            ) as scoped_instance:
                if self._instance.is_using_isolated_agents:
                    scoped_instance.report_engine_event(
                        f"{self._instance.agent_display_name} received request to mark run as canceling",
                        run,
                        cls=self.__class__,
                    )
                    scoped_instance.report_run_canceling(run)
                else:
                    scoped_instance.report_engine_event(
                        f"{self._instance.agent_display_name} received request to terminate run",
                        run,
                        cls=self.__class__,
                    )
                    if is_isolated_run(run):
                        launcher = scoped_instance.get_run_launcher_for_run(run)  # type: ignore  # (instance subclass)
                        launcher.terminate(run.run_id)
                    else:
                        run_location_name = cast(
                            "str",
                            run.remote_job_origin.repository_origin.code_location_origin.location_name,
                        )

                        server = user_code_launcher.get_grpc_server(
                            deployment_name, run_location_name
                        )
                        client = server.server_endpoint.create_client()

                        scoped_instance.report_run_canceling(run)
                        client.cancel_execution(CancelExecutionRequest(run_id=run.run_id))

            return DagsterCloudApiSuccess()
        elif api_name in (
            DagsterCloudApi.CHECK_STEP_HEALTH,
            DagsterCloudApi.TERMINATE_STEP,
            DagsterCloudApi.LAUNCH_STEP,
            DagsterCloudApi.CHECK_RUN_HEALTH,
            DagsterCloudApi.LOAD_REPOSITORIES,
        ):
            check.failed(f"Unexpected deprecated request type {api_name}")
        else:
            check.assert_never(api_name)

    def _process_api_request(
        self,
        json_request: dict,
        user_code_launcher: DagsterCloudUserCodeLauncher,
        submitted_to_executor_timestamp: float,
    ) -> SerializableErrorInfo | None:
        thread_start_run_timestamp = get_current_timestamp()
        api_result: DagsterCloudApiResponse | None = None
        error_info: SerializableErrorInfo | None = None

        request_id = json_request["requestId"]
        request_api = json_request["requestApi"]
        request_body = json_request["requestBody"]
        deployment_name = json_request["deploymentName"]
        is_branch_deployment = json_request["isBranchDeployment"]

        request: str | DagsterCloudApiRequest = DagsterCloudApiRequest.format_request(
            request_id, request_api
        )

        if request_api not in DagsterCloudApi.__members__:
            api_result = DagsterCloudApiUnknownCommandResponse(request_api=request_api)
            self._logger.warning(
                f"Ignoring request {json_request}: Unknown command. This is likely due to running an "
                "older version of the agent."
            )
        else:
            try:
                request = deserialize_value(request_body, DagsterCloudApiRequest)
                self._logger.info(f"Received request {request}.")
                api_result = self._handle_api_request(
                    request, deployment_name, is_branch_deployment, user_code_launcher
                )
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                api_result = DagsterCloudApiErrorResponse(error_infos=[error_info])

                self._logger.error(f"Error serving request {json_request}: {error_info}")

        self._logger.info(f"Finished processing request {request}.")

        thread_finished_request_time = get_current_timestamp()
        thread_telemetry = DagsterCloudApiThreadTelemetry(
            submitted_to_executor_timestamp=submitted_to_executor_timestamp,
            thread_start_run_timestamp=thread_start_run_timestamp,
            thread_end_handle_api_request_timestamp=thread_finished_request_time,
        )

        api_result = api_result.with_thread_telemetry(thread_telemetry)

        assert api_result

        upload_response = DagsterCloudUploadApiResponse(
            request_id=request_id,
            request_api=request_api,
            response=api_result,
        )

        self._logger.info(f"Uploading response for request {request}.")

        if UPLOAD_API_RESPONSE_BATCHING_ENABLED():
            self._batcher[deployment_name].submit((deployment_name, upload_response))
        else:
            upload_api_response(self._instance, deployment_name, upload_response)

        self._logger.info(f"Finished uploading response for request {request}.")

        return error_info

    def _batch_upload_api_response(
        self, upload_response_batch: list[tuple[str, DagsterCloudUploadApiResponse]]
    ) -> list[None]:
        deployment_names = set(deployment_name for deployment_name, _ in upload_response_batch)
        assert len(deployment_names) == 1
        batch_upload_api_response(
            self._instance,
            next(iter(deployment_names)),
            [resp for _, resp in upload_response_batch],
        )
        return [None for _ in upload_response_batch]

    def _get_location_from_request(self, json_request: dict[str, Any]) -> str | None:
        request_api = json_request["requestApi"]
        request_body = json_request["requestBody"]
        if request_api not in DagsterCloudApi.__members__:
            return None

        request = deserialize_value(request_body, DagsterCloudApiRequest)
        location_origin = self._get_location_origin_from_request(request)
        if not location_origin:
            return None

        return location_origin.location_name

    def run_iteration(
        self, user_code_launcher: DagsterCloudUserCodeLauncher
    ) -> Iterator[SerializableErrorInfo | None]:
        if not user_code_launcher.ready_to_serve_requests:
            return

        num_pending_requests = len(self._pending_requests)

        if num_pending_requests < self._pending_requests_limit:
            # limit (implicit default 10) applied separately for requests to branch deployments, and for each full deployment
            result = self._instance.organization_scoped_graphql_client().execute(
                GET_USER_CLOUD_REQUESTS_QUERY,
                {
                    "forBranchDeployments": self._instance.includes_branch_deployments,
                    "forFullDeployments": self._active_full_deployment_names,
                    "agentQueues": self._instance.agent_queues_config.queues,
                },
            )
            json_requests = result["data"]["userCloudAgent"]["popUserCloudAgentRequests"]

            self._logger.debug(
                f"Iteration #{self._iteration}: Adding {len(json_requests)} requests to be"
                f" processed. Currently {num_pending_requests} waiting for server to be ready"
            )
            self._pending_requests.extend(json_requests)

        else:
            self._logger.warning(
                f"Iteration #{self._iteration}: Waiting to pull requests from the queue since there are"
                f" already {len(self._pending_requests)} in the queue"
            )

        invalid_requests = []
        self._locations_with_pending_requests = set()

        # Determine which pending requests are now ready (their locations have been loaded, or the
        # request does not correspond to a particular location)
        for json_request in self._pending_requests:
            deployment_name = json_request["deploymentName"]
            is_branch_deployment = json_request["isBranchDeployment"]
            location_name = self._get_location_from_request(json_request)
            if location_name:
                self._location_query_times[
                    (deployment_name, location_name, is_branch_deployment)
                ] = time.time()

                if self._instance.is_location_allowed(
                    deployment_name, location_name, is_branch_deployment
                ) and not user_code_launcher.has_grpc_endpoint(deployment_name, location_name):
                    # Next completed periodic workspace update will make the location up to date
                    # - keep this in the queue until then
                    invalid_requests.append(json_request)
                    self._locations_with_pending_requests.add(
                        (deployment_name, location_name, is_branch_deployment)
                    )
                    continue

            self._ready_requests.append(json_request)

        # Any invalid requests go back in the pending queue - the next workspace update will
        # ensure that the usercodelauncher spins up locations for those requests
        self._pending_requests = invalid_requests

        # send all ready requests to the threadpool
        for json_request in self._ready_requests:
            request_id = json_request["requestId"]
            submitted_to_executor_timestamp = get_current_timestamp()
            future = self._executor.submit(
                self._process_api_request,
                json_request,
                user_code_launcher,
                submitted_to_executor_timestamp,
            )

            self._request_ids_to_futures[request_id] = future

        self._ready_requests = []

        # Process futures that are done
        # Create a shallow copy of the futures dict to modify it while iterating
        for request_id, future in self._request_ids_to_futures.copy().items():
            if future.done():
                response: SerializableErrorInfo | None = None

                try:
                    response = future.result(timeout=0)
                except:
                    response = serializable_error_info_from_exc_info(sys.exc_info())

                # Do not process a request again once we have its result
                del self._request_ids_to_futures[request_id]

                # Yield the error information from the future
                if response:
                    yield response

        if self._instance.user_code_launcher.agent_metrics_enabled and (
            self._utilization_metrics["container_utilization"]["measurement_timestamp"] is None
            or (
                get_current_timestamp()
                - self._utilization_metrics["container_utilization"]["measurement_timestamp"]
                > AGENT_UTILIZATION_METRICS_INTERVAL_SECONDS
            )
        ):
            self._update_utilization_metrics(user_code_launcher)
        self._iteration += 1

        yield None


def batch_upload_api_response(
    instance: DagsterCloudAgentInstance,
    deployment_name: str,
    batch: list[DagsterCloudUploadApiResponse],
):
    with compressed_namedtuple_upload_file(BatchDagsterCloudUploadApiResponse(batch=batch)) as f:
        resp = instance.requests_managed_retries_session.put(
            instance.dagster_cloud_upload_api_response_url,
            headers=instance.headers_for_deployment(deployment_name),
            files={"api_response_batch.tmp": f},
            timeout=instance.dagster_cloud_api_timeout,
            proxies=instance.dagster_cloud_api_proxies,
        )
        raise_http_error(resp)


def upload_api_response(
    instance: DagsterCloudAgentInstance,
    deployment_name: str,
    upload_response: DagsterCloudUploadApiResponse,
):
    with compressed_namedtuple_upload_file(upload_response) as f:
        resp = instance.requests_managed_retries_session.put(
            instance.dagster_cloud_upload_api_response_url,
            headers=instance.headers_for_deployment(deployment_name),
            files={"api_response.tmp": f},
            timeout=instance.dagster_cloud_api_timeout,
            proxies=instance.dagster_cloud_api_proxies,
        )
        raise_http_error(resp)
