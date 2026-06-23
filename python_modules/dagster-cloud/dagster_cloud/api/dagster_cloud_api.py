import enum
from collections.abc import Mapping, Sequence
from datetime import timedelta
from enum import Enum
from typing import Any, TypeAlias, TypedDict

from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.selector import JobSelector
from dagster._core.events.log import EventLogEntry
from dagster._core.remote_origin import CodeLocationOrigin
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.utils import RequestUtilizationMetrics
from dagster._record import IHaveNew, copy, record, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils.container import ContainerUtilizationMetrics
from dagster._utils.error import SerializableErrorInfo
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from typing_extensions import NotRequired

from dagster_cloud.agent import AgentQueuesConfig
from dagster_cloud.execution.monitoring import (
    CloudCodeServerHeartbeat,
    CloudContainerResourceLimits,
    CloudRunWorkerStatuses,
)
from dagster_cloud.util import keys_not_none

DEFAULT_EXPIRATION_MILLISECONDS = 10 * 60 * 1000


@whitelist_for_serdes
@record
class DagsterCloudUploadRepositoryData:
    """Serialized object uploaded by the Dagster Cloud agent with information pulled
    from a gRPC server about an individual repository - the data field is serialized since the
    agent may be running older code that doesn't know how to deserialize it, so it passes
    it serialized up to the host cloud, which is always up to date.
    """

    repository_name: str
    code_pointer: CodePointer
    serialized_repository_data: str


@whitelist_for_serdes
@record
class DagsterCloudUploadLocationData:
    """Serialized object uploaded by the Dagster Cloud agent with information pulled
    about a successfully loaded repository location, including information about
    each repository as well as shared metadata like the image to use when launching
    runs in this location.
    """

    upload_repository_datas: list[DagsterCloudUploadRepositoryData]
    container_image: str | None
    executable_path: str | None
    dagster_library_versions: Mapping[str, str] | None = None


@whitelist_for_serdes(storage_field_names={"code_location_deploy_data": "deployment_metadata"})
@record
class DagsterCloudUploadWorkspaceEntry:
    """Serialized object uploaded by the Dagster Cloud agent with information about
    a repository location - either the serialized DagsterCloudUploadLocationData
    if the location loaded succesfully, or a SerializableErrorInfo describing the
    error if it was not.
    """

    location_name: str
    code_location_deploy_data: CodeLocationDeployData
    upload_location_data: DagsterCloudUploadLocationData | None
    serialized_error_info: SerializableErrorInfo | None


@whitelist_for_serdes
@record
class DagsterCloudUploadWorkspaceResponse:
    updated: bool
    message: str
    missing_job_snapshots: Sequence[JobSelector] | None


@whitelist_for_serdes
class DagsterCloudApi(Enum):
    CHECK_FOR_WORKSPACE_UPDATES = "CHECK_FOR_WORKSPACE_UPDATES"
    GET_EXTERNAL_EXECUTION_PLAN = "GET_EXTERNAL_EXECUTION_PLAN"
    GET_SUBSET_EXTERNAL_PIPELINE_RESULT = "GET_SUBSET_EXTERNAL_PIPELINE_RESULT"
    GET_EXTERNAL_PARTITION_CONFIG = "GET_EXTERNAL_PARTITION_CONFIG"
    GET_EXTERNAL_PARTITION_TAGS = "GET_EXTERNAL_PARTITION_TAGS"
    GET_EXTERNAL_PARTITION_NAMES = "GET_EXTERNAL_PARTITION_NAMES"
    GET_EXTERNAL_PARTITION_SET_EXECUTION_PARAM_DATA = (
        "GET_EXTERNAL_PARTITION_SET_EXECUTION_PARAM_DATA"
    )
    GET_EXTERNAL_SCHEDULE_EXECUTION_DATA = "GET_EXTERNAL_SCHEDULE_EXECUTION_DATA"
    GET_EXTERNAL_SENSOR_EXECUTION_DATA = "GET_EXTERNAL_SENSOR_EXECUTION_DATA"
    GET_EXTERNAL_NOTEBOOK_DATA = "GET_EXTERNAL_NOTEBOOK_DATA"

    LAUNCH_RUN = "LAUNCH_RUN"
    TERMINATE_RUN = "TERMINATE_RUN"

    PING_LOCATION = "PING_LOCATION"  # Signal that a location is in use and should keep servers up

    CHECK_RUN_HEALTH = "CHECK_RUN_HEALTH"  # deprecated, agents now surface this in heartbeats
    LAUNCH_STEP = "LAUNCH_STEP"  # deprecated with cloud executor
    CHECK_STEP_HEALTH = "CHECK_STEP_HEALTH"  # deprecated with cloud executor
    TERMINATE_STEP = "TERMINATE_STEP"  # deprecated with cloud executor
    LOAD_REPOSITORIES = "LOAD_REPOSITORIES"  # deprecated

    def __structlog__(self):
        return self.name


@whitelist_for_serdes
@record
class DagsterCloudApiThreadTelemetry:
    submitted_to_executor_timestamp: float
    thread_start_run_timestamp: float
    thread_end_handle_api_request_timestamp: float

    @property
    def time_to_thread_initialization_seconds(self) -> float:
        return self.thread_start_run_timestamp - self.submitted_to_executor_timestamp

    @property
    def time_to_handle_api_request_seconds(self) -> float:
        return self.thread_end_handle_api_request_timestamp - self.thread_start_run_timestamp


@whitelist_for_serdes(old_storage_names={"CheckForCodeLocationUpdatesRequest"})
@record
class DagsterCloudApiSuccess:
    thread_telemetry: DagsterCloudApiThreadTelemetry | None = None

    def with_thread_telemetry(self, thread_telemetry: DagsterCloudApiThreadTelemetry):
        return copy(self, thread_telemetry=thread_telemetry)


@whitelist_for_serdes
@record
class DagsterCloudApiUnknownCommandResponse:
    request_api: str
    thread_telemetry: DagsterCloudApiThreadTelemetry | None = None

    def with_thread_telemetry(self, thread_telemetry: DagsterCloudApiThreadTelemetry):
        return copy(self, thread_telemetry=thread_telemetry)


@whitelist_for_serdes
@record
class DagsterCloudApiErrorResponse:
    error_infos: list[SerializableErrorInfo]
    thread_telemetry: DagsterCloudApiThreadTelemetry | None = None

    def with_thread_telemetry(self, thread_telemetry: DagsterCloudApiThreadTelemetry):
        return copy(self, thread_telemetry=thread_telemetry)


@whitelist_for_serdes
@record
class DagsterCloudApiGrpcResponse:
    # Class that DagsterCloudApi methods can use to pass along the result of
    # a gRPC call against the user code server. The field here is passed in
    # serialized as a string, because we can't guarantee that the agent code will
    # be up-to-date enough to know how to deserialize it (but the host cloud always
    # should, since it will always be up to date).
    serialized_response_or_error: str
    thread_telemetry: DagsterCloudApiThreadTelemetry | None = None

    def with_thread_telemetry(self, thread_telemetry: DagsterCloudApiThreadTelemetry):
        return copy(self, thread_telemetry=thread_telemetry)


@whitelist_for_serdes
@record
class LoadRepositoriesArgs:
    location_origin: CodeLocationOrigin


@whitelist_for_serdes
@record
class DagsterCloudRepositoryData:
    repo_name: str
    code_pointer: CodePointer
    external_repository_data: RepositorySnap


@whitelist_for_serdes(storage_field_names={"code_location_deploy_data": "code_deployment_metadata"})
@record
class LoadRepositoriesResponse:
    repository_datas: Sequence[DagsterCloudRepositoryData]
    container_image: str | None
    executable_path: str | None
    code_location_deploy_data: CodeLocationDeployData | None = None
    dagster_library_versions: Mapping[str, str] | None = None


@whitelist_for_serdes
@record
class PingLocationArgs:
    location_name: str


@whitelist_for_serdes(storage_field_names={"dagster_run": "pipeline_run"})
@record
class LaunchRunArgs:
    dagster_run: DagsterRun


@whitelist_for_serdes(storage_field_names={"dagster_run": "pipeline_run"})
@record
class TerminateRunArgs:
    dagster_run: DagsterRun


@whitelist_for_serdes
@record_custom
class DagsterCloudApiRequest(IHaveNew):
    request_id: str
    request_api: DagsterCloudApi
    request_args: Any
    deployment_name: str
    expire_at: float
    is_branch_deployment: bool

    def __new__(
        cls,
        request_id: str,
        request_api: DagsterCloudApi,
        request_args: Any,
        deployment_name: str,
        expire_at: float | None = None,
        is_branch_deployment: bool | None = None,
    ):
        return super().__new__(
            cls,
            request_id=request_id,
            request_api=request_api,
            request_args=request_args,
            deployment_name=deployment_name,
            expire_at=expire_at
            if expire_at is not None
            else (
                get_current_datetime() + timedelta(milliseconds=DEFAULT_EXPIRATION_MILLISECONDS)
            ).timestamp(),
            is_branch_deployment=False if is_branch_deployment is None else is_branch_deployment,
        )

    @property
    def is_expired(self) -> bool:
        return get_current_timestamp() > self.expire_at

    @staticmethod
    def format_request(request_id: str, request_api: str | DagsterCloudApi) -> str:
        return f"[{request_id}: {request_api}]"

    def __str__(self) -> str:
        return DagsterCloudApiRequest.format_request(self.request_id, self.request_api)


DagsterCloudApiResponse: TypeAlias = (
    DagsterCloudApiSuccess
    | DagsterCloudApiGrpcResponse
    | DagsterCloudApiErrorResponse
    | DagsterCloudApiUnknownCommandResponse
)

DagsterCloudApiResponseTypesTuple = (
    DagsterCloudApiSuccess,
    DagsterCloudApiGrpcResponse,
    DagsterCloudApiErrorResponse,
    DagsterCloudApiUnknownCommandResponse,
)


@whitelist_for_serdes
@record
class StoreEventBatchRequest:
    event_log_entries: Sequence[EventLogEntry]


@whitelist_for_serdes
@record
class DagsterCloudUploadApiResponse:
    request_id: str
    request_api: str
    response: DagsterCloudApiResponse


@whitelist_for_serdes
@record
class BatchDagsterCloudUploadApiResponse:
    batch: list[DagsterCloudUploadApiResponse]


@whitelist_for_serdes
@record
class TimestampedError:
    timestamp: float | None
    error: SerializableErrorInfo


class UserCodeDeploymentType(enum.Enum):
    SERVERLESS = "serverless"
    ECS = "ecs"
    K8S = "k8s"
    DOCKER = "docker"
    PROCESS = "process"
    UNKNOWN = "unknown"

    @property
    def supports_utilization_metrics(self) -> bool:
        return self in [
            UserCodeDeploymentType.ECS,
            UserCodeDeploymentType.K8S,
            UserCodeDeploymentType.SERVERLESS,
        ]


class AgentUtilizationMetrics(TypedDict):
    container_utilization: ContainerUtilizationMetrics
    request_utilization: RequestUtilizationMetrics
    resource_limits: CloudContainerResourceLimits


class AgentHeartbeatMetadata(TypedDict):
    utilization_metrics: NotRequired[AgentUtilizationMetrics]
    version: NotRequired[str]
    image_tag: NotRequired[str]
    type: NotRequired[str]
    queues: NotRequired[list[str]]


@whitelist_for_serdes
@record_custom
class AgentHeartbeat(IHaveNew):
    timestamp: float
    agent_id: str
    agent_label: str | None
    agent_type: str | None
    errors: Sequence[TimestampedError] | None
    metadata: AgentHeartbeatMetadata
    run_worker_statuses: CloudRunWorkerStatuses | None
    code_server_heartbeats: Sequence[CloudCodeServerHeartbeat]
    agent_queues_config: AgentQueuesConfig

    def __new__(
        cls,
        timestamp: float,
        agent_id: str,
        agent_label: str | None,
        agent_type: str | None,
        errors: Sequence[TimestampedError] | None = None,
        metadata: Mapping[str, Any] | None = None,
        run_worker_statuses: CloudRunWorkerStatuses | None = None,
        code_server_heartbeats: Sequence[CloudCodeServerHeartbeat] | None = None,
        agent_queues_config: AgentQueuesConfig | None = None,
    ):
        return super().__new__(
            cls,
            timestamp=timestamp,
            agent_id=agent_id,
            agent_label=agent_label,
            agent_type=agent_type,
            errors=errors,
            metadata=metadata or {},
            run_worker_statuses=run_worker_statuses,
            code_server_heartbeats=code_server_heartbeats or [],
            agent_queues_config=agent_queues_config or AgentQueuesConfig(),
        )

    def without_messages_and_errors(self) -> "AgentHeartbeat":
        return copy(
            self,
            errors=[],
            run_worker_statuses=self.run_worker_statuses.without_messages_and_errors()
            if self.run_worker_statuses
            else None,
            code_server_heartbeats=[
                heartbeat.without_messages_and_errors() for heartbeat in self.code_server_heartbeats
            ],
            metadata={
                key: val for key, val in self.metadata.items() if key != "utilization_metrics"
            },
        )

    def get_agent_utilization_metrics(self) -> AgentUtilizationMetrics | None:
        metrics = self.metadata.get("utilization_metrics")
        if metrics and keys_not_none(["container_utilization", "request_utilization"], metrics):
            return metrics
        return None


class FileFormat:
    JSON = "json"
    GZIPPED_JSON = "json.gz"


class SnapshotType:
    ERROR = "error"
    JOB = "job"
    REPOSITORY = "repository"


@whitelist_for_serdes
@record
class StoredSnapshot:
    sha1: str
    format: str
    uri: str
    decompressed_size: int


@whitelist_for_serdes
@record
class SnapshotUploadData:
    sha1: str
    format: str
    uri: str
    presigned_put_url: str
    id: str
    type: str


@whitelist_for_serdes
@record
class CheckSnapshotResult:
    stored_snapshot: StoredSnapshot | None
    upload_data: SnapshotUploadData | None


@whitelist_for_serdes
@record
class ConfirmUploadResult:
    stored_snapshot: StoredSnapshot


@whitelist_for_serdes
@record
class DagsterCloudRepositoryManifest:
    name: str
    code_pointer: CodePointer
    stored_snapshot: StoredSnapshot


@whitelist_for_serdes
@record
class DagsterCloudCodeLocationManifest:
    repositories: Sequence[DagsterCloudRepositoryManifest]
    container_image: str | None
    executable_path: str | None
    dagster_library_versions: Mapping[str, str] | None
    code_location_deploy_data: CodeLocationDeployData


@whitelist_for_serdes
@record
class DagsterCloudCodeLocationUpdateResult:
    location_name: str
    manifest: DagsterCloudCodeLocationManifest | None
    error_snapshot: StoredSnapshot | None


@whitelist_for_serdes
@record
class DagsterCloudCodeLocationUpdateResponse:
    updated: bool
    message: str
    missing_job_snapshots: Sequence[JobSelector] | None
