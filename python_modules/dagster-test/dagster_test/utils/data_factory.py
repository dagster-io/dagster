from collections.abc import (
    Mapping,
    Sequence,
    Set as AbstractSet,
)
from datetime import datetime
from typing import Callable, Optional, Union
from uuid import uuid4

from dagster import (
    AssetCheckKey,
    AssetKey,
    DagsterEvent,
    DagsterEventType,
    DagsterRun,
    DagsterRunStatus,
    EventLogEntry,
)
from dagster._core.events import (
    EventSpecificData,
    NodeHandle,
    ResolvedFromDynamicStepHandle,
    StepHandle,
)
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import (
    JobDataSnap,
    JobRefSnap,
    RepositorySnap,
)
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.dagster_run import RunOpConcurrency
from dagster._grpc.types import JobPythonOrigin, RemoteJobOrigin, SerializableErrorInfo
from pydantic import UUID4


def event_log(
    error_info: Optional[SerializableErrorInfo] = None,  # No error info by default
    level: Union[str, int] = 1,  # Default to level `1`
    user_message: str = "test rate limit",  # A default user message
    run_id: str = "missing",  # Default to `missing` if no run ID is provided
    timestamp: float = datetime.now().timestamp(),  # Default to the current timestamp
    step_key: Optional[str] = None,  # No specific step key by default
    job_name: Optional[str] = None,  # No job name by default
    dagster_event: Optional[DagsterEvent] = None,  # No associated Dagster event by default
) -> EventLogEntry:
    return EventLogEntry(
        error_info=error_info,
        level=level,
        user_message=user_message,
        run_id=run_id,
        timestamp=timestamp,
        step_key=step_key,
        job_name=job_name,
        dagster_event=dagster_event,
    )


def dagster_event(
    event_type_value: str = DagsterEventType.ALERT_START.value,
    job_name: str = "default_job",
    step_handle: Optional[Union[StepHandle, ResolvedFromDynamicStepHandle]] = None,
    node_handle: Optional[NodeHandle] = None,
    step_kind_value: Optional[str] = None,
    logging_tags: Optional[Mapping[str, str]] = None,
    event_specific_data: Optional[EventSpecificData] = None,
    message: Optional[str] = None,
    pid: Optional[int] = None,
    step_key: Optional[str] = None,
) -> DagsterEvent:
    return DagsterEvent(
        event_type_value=event_type_value,
        job_name=job_name,
        step_handle=step_handle,
        node_handle=node_handle,
        step_kind_value=step_kind_value,
        logging_tags=logging_tags,
        event_specific_data=event_specific_data,
        message=message,
        pid=pid,
        step_key=step_key,
    )


def dagster_run(
    job_name: str = "test-job",
    run_id: Optional[Union[str, UUID4]] = None,
    run_config: Optional[Mapping[str, object]] = None,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    op_selection: Optional[Sequence[str]] = None,
    resolved_op_selection: Optional[AbstractSet[str]] = None,
    step_keys_to_execute: Optional[Sequence[str]] = None,
    status: DagsterRunStatus = DagsterRunStatus.NOT_STARTED,
    tags: Optional[Mapping[str, str]] = None,
    root_run_id: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    job_snapshot_id: Optional[str] = None,
    execution_plan_snapshot_id: Optional[str] = None,
    remote_job_origin: Optional[RemoteJobOrigin] = None,
    job_code_origin: Optional[JobPythonOrigin] = None,
    has_repository_load_data: bool = False,
    run_op_concurrency: Optional[RunOpConcurrency] = None,
):
    if run_id is None:
        run_id_str = str(uuid4())
    elif isinstance(run_id, str):
        run_id_str = run_id
    else:
        run_id_str = str(run_id)

    return DagsterRun(
        job_name=job_name,
        run_id=run_id_str,
        run_config=run_config or {},
        asset_selection=asset_selection,
        asset_check_selection=asset_check_selection,
        op_selection=op_selection,
        resolved_op_selection=resolved_op_selection,
        step_keys_to_execute=step_keys_to_execute,
        status=status,
        tags=tags or {},
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        job_snapshot_id=job_snapshot_id,
        execution_plan_snapshot_id=execution_plan_snapshot_id,
        remote_job_origin=remote_job_origin,
        job_code_origin=job_code_origin,
        has_repository_load_data=has_repository_load_data,
        run_op_concurrency=run_op_concurrency,
    )


def remote_repository(
    repository_snap: RepositorySnap,
    repository_handle: RepositoryHandle,
    auto_materialize_use_sensors: bool = True,
    ref_to_data_fn: Optional[Callable[[JobRefSnap], JobDataSnap]] = None,
):
    return RemoteRepository(
        repository_snap=repository_snap,
        repository_handle=repository_handle,
        auto_materialize_use_sensors=auto_materialize_use_sensors,
        ref_to_data_fn=ref_to_data_fn,
    )
