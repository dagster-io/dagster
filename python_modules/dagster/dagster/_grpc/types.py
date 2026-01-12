import base64
import zlib
from collections.abc import Mapping, Sequence
from typing import AbstractSet, Any, Optional  # noqa: UP035

from dagster_shared.record import IHaveNew, copy, record, record_custom
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_shared.serdes.serdes import SetToSequenceFieldSerializer

import dagster._check as check
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.instance.ref import InstanceRef
from dagster._core.origin import JobPythonOrigin, get_python_environment_entry_point
from dagster._core.remote_origin import CodeLocationOrigin, RemoteJobOrigin, RemoteRepositoryOrigin
from dagster._core.remote_representation.external_data import (
    DEFAULT_MODE_NAME,
    job_name_for_partition_set_snap_name,
)
from dagster._serdes import serialize_value, whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo


@whitelist_for_serdes(
    storage_field_names={
        "job_origin": "pipeline_origin",
        "job_snapshot_id": "pipeline_snapshot_id",
        "op_selection": "solid_selection",
    }
)
@record
class ExecutionPlanSnapshotArgs:
    job_origin: RemoteJobOrigin
    op_selection: Sequence[str]
    run_config: Mapping[str, object]
    step_keys_to_execute: Optional[Sequence[str]]
    job_snapshot_id: str
    known_state: Optional[KnownExecutionState] = None
    instance_ref: Optional[InstanceRef] = None
    asset_selection: Optional[AbstractSet[AssetKey]] = None
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None
    mode: str = DEFAULT_MODE_NAME


def _get_entry_point(origin: JobPythonOrigin):
    return (
        origin.repository_origin.entry_point
        if origin.repository_origin.entry_point
        else get_python_environment_entry_point(origin.executable_path)
    )


@whitelist_for_serdes(
    storage_field_names={
        "job_origin": "pipeline_origin",
        "run_id": "pipeline_run_id",
    }
)
@record_custom
class ExecuteRunArgs(IHaveNew):
    # Deprecated, only needed for back-compat since it can be pulled from the PipelineRun
    job_origin: JobPythonOrigin
    run_id: str
    instance_ref: Optional[InstanceRef]
    set_exit_code_on_failure: Optional[bool]

    def __new__(
        cls,
        job_origin: JobPythonOrigin,
        run_id: str,
        instance_ref: Optional[InstanceRef],
        set_exit_code_on_failure: Optional[bool] = None,
    ):
        return super().__new__(
            cls,
            job_origin=job_origin,
            run_id=run_id,
            instance_ref=instance_ref,
            # for back-compat: only True or None allowed
            set_exit_code_on_failure=True if set_exit_code_on_failure is True else None,
        )

    def get_command_args(self) -> Sequence[str]:
        return [
            *_get_entry_point(self.job_origin),
            "api",
            "execute_run",
            serialize_value(self),
        ]


@whitelist_for_serdes(
    storage_field_names={
        "job_origin": "pipeline_origin",
        "run_id": "pipeline_run_id",
    }
)
@record_custom
class ResumeRunArgs(IHaveNew):
    # Deprecated, only needed for back-compat since it can be pulled from the DagsterRun
    job_origin: JobPythonOrigin
    run_id: str
    instance_ref: Optional[InstanceRef]
    set_exit_code_on_failure: Optional[bool]

    def __new__(
        cls,
        job_origin: JobPythonOrigin,
        run_id: str,
        instance_ref: Optional[InstanceRef],
        set_exit_code_on_failure: Optional[bool] = None,
    ):
        return super().__new__(
            cls,
            job_origin=job_origin,
            run_id=run_id,
            instance_ref=instance_ref,
            # for back-compat: only True or None allowed
            set_exit_code_on_failure=True if set_exit_code_on_failure is True else None,
        )

    def get_command_args(self) -> Sequence[str]:
        return [
            *_get_entry_point(self.job_origin),
            "api",
            "resume_run",
            serialize_value(self),
        ]


@whitelist_for_serdes(
    storage_name="ExecuteExternalPipelineArgs",
    storage_field_names={
        "job_origin": "pipeline_origin",
        "run_id": "pipeline_run_id",
    },
)
@record
class ExecuteExternalJobArgs:
    job_origin: RemoteJobOrigin
    run_id: str
    instance_ref: Optional[InstanceRef]


@whitelist_for_serdes(
    storage_field_names={
        "job_origin": "pipeline_origin",
        "run_id": "pipeline_run_id",
    }
)
@record_custom
class ExecuteStepArgs(IHaveNew):
    # Deprecated, only needed for back-compat since it can be pulled from the DagsterRun
    job_origin: JobPythonOrigin
    run_id: str
    step_keys_to_execute: Optional[Sequence[str]]
    instance_ref: Optional[InstanceRef]
    retry_mode: Optional[RetryMode]
    known_state: Optional[KnownExecutionState]
    should_verify_step: Optional[bool]
    print_serialized_events: bool

    def __new__(
        cls,
        job_origin: JobPythonOrigin,
        run_id: str,
        step_keys_to_execute: Optional[Sequence[str]],
        instance_ref: Optional[InstanceRef] = None,
        retry_mode: Optional[RetryMode] = None,
        known_state: Optional[KnownExecutionState] = None,
        should_verify_step: Optional[bool] = None,
        print_serialized_events: Optional[bool] = None,
    ):
        return super().__new__(
            cls,
            job_origin=job_origin,
            run_id=run_id,
            step_keys_to_execute=step_keys_to_execute,
            instance_ref=instance_ref,
            retry_mode=retry_mode,
            known_state=known_state,
            should_verify_step=should_verify_step if should_verify_step is not None else False,
            print_serialized_events=(
                print_serialized_events if print_serialized_events is not None else False
            ),
        )

    def _get_compressed_args(self) -> str:
        # Compress, then base64 encode so we can pass it around as a str
        return base64.b64encode(zlib.compress(serialize_value(self).encode())).decode()

    def get_command_args(self, skip_serialized_namedtuple: bool = False) -> Sequence[str]:
        """Get the command args to run this step. If skip_serialized_namedtuple is True, then get_command_env should
        be used to pass the args to Click using an env var.
        """
        return [
            *_get_entry_point(self.job_origin),
            "api",
            "execute_step",
            *(
                ["--compressed-input-json", self._get_compressed_args()]
                if not skip_serialized_namedtuple
                else []
            ),
        ]

    def get_command_env(self) -> Sequence[Mapping[str, str]]:
        """Get the env vars for overriding the Click args of this step. Used in conjuction with
        get_command_args(skip_serialized_namedtuple=True).
        """
        return [
            {"name": "DAGSTER_COMPRESSED_EXECUTE_STEP_ARGS", "value": self._get_compressed_args()},
        ]


@whitelist_for_serdes
@record
class LoadableRepositorySymbol:
    repository_name: str
    attribute: str


@whitelist_for_serdes
@record_custom
class ListRepositoriesResponse(IHaveNew):
    repository_symbols: Sequence[LoadableRepositorySymbol]
    executable_path: Optional[str]
    repository_code_pointer_dict: Mapping[str, CodePointer]
    entry_point: Optional[Sequence[str]]
    container_image: Optional[str]
    container_context: Optional[Mapping[str, Any]]
    dagster_library_versions: Optional[Mapping[str, str]]
    defs_state_info: Optional[DefsStateInfo]

    def __new__(
        cls,
        repository_symbols: Sequence[LoadableRepositorySymbol],
        executable_path: Optional[str] = None,
        repository_code_pointer_dict: Optional[Mapping[str, CodePointer]] = None,
        entry_point: Optional[Sequence[str]] = None,
        container_image: Optional[str] = None,
        container_context: Optional[Mapping[str, Any]] = None,
        dagster_library_versions: Optional[Mapping[str, str]] = None,
        defs_state_info: Optional[DefsStateInfo] = None,
    ):
        return super().__new__(
            cls,
            repository_symbols=repository_symbols,
            executable_path=executable_path,
            repository_code_pointer_dict=(
                repository_code_pointer_dict if repository_code_pointer_dict is not None else {}
            ),
            entry_point=entry_point,
            container_image=container_image,
            container_context=container_context,
            dagster_library_versions=dagster_library_versions,
            defs_state_info=defs_state_info,
        )


@whitelist_for_serdes
@record_custom
class ListRepositoriesInput(IHaveNew):
    module_name: Optional[str]
    python_file: Optional[str]
    working_directory: Optional[str]
    attribute: Optional[str]

    def __new__(
        cls,
        module_name: Optional[str],
        python_file: Optional[str],
        working_directory: Optional[str],
        attribute: Optional[str],
    ):
        check.invariant(not (module_name and python_file), "Must set only one")
        check.invariant(module_name or python_file, "Must set at least one")
        return super().__new__(
            cls,
            module_name=module_name,
            python_file=python_file,
            working_directory=working_directory,
            attribute=attribute,
        )


@whitelist_for_serdes
@record
class PartitionArgs:
    repository_origin: RemoteRepositoryOrigin
    # This is here for backcompat. it's expected to always be f"{job_name}_partition_set".
    partition_set_name: str
    partition_name: str
    job_name: Optional[str] = None
    instance_ref: Optional[InstanceRef] = None

    def get_job_name(self) -> str:
        if self.job_name:
            return self.job_name
        else:
            return job_name_for_partition_set_snap_name(self.partition_set_name)


@whitelist_for_serdes
@record
class PartitionNamesArgs:
    repository_origin: RemoteRepositoryOrigin
    # This is here for backcompat. it's expected to always be f"{job_name}_partition_set".
    partition_set_name: str
    # This is introduced in the same release that we're making it possible for an asset job
    # to target assets with different PartitionsDefinitions. Prior user code versions can
    # (and do) safely ignore this parameter, because, in those versions, the job name on its
    # own is enough to specify which PartitionsDefinition to use.
    job_name: Optional[str] = None

    def get_job_name(self) -> str:
        if self.job_name:
            return self.job_name
        else:
            return job_name_for_partition_set_snap_name(self.partition_set_name)


@whitelist_for_serdes
@record
class PartitionSetExecutionParamArgs:
    repository_origin: RemoteRepositoryOrigin
    partition_set_name: str
    partition_names: Sequence[str]
    instance_ref: Optional[InstanceRef] = None


@whitelist_for_serdes(
    storage_name="PipelineSubsetSnapshotArgs",
    storage_field_names={
        "job_origin": "pipeline_origin",
        "op_selection": "solid_selection",
    },
    # asset_selection previously was erroneously represented as a sequence
    field_serializers={"asset_selection": SetToSequenceFieldSerializer},
)
@record_custom
class JobSubsetSnapshotArgs(IHaveNew):
    job_origin: RemoteJobOrigin
    op_selection: Optional[Sequence[str]]
    asset_selection: Optional[AbstractSet[AssetKey]]
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]]
    include_parent_snapshot: bool

    def __new__(
        cls,
        job_origin: RemoteJobOrigin,
        op_selection: Optional[Sequence[str]],
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
        include_parent_snapshot: Optional[bool] = None,
    ):
        return super().__new__(
            cls,
            job_origin=job_origin,
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            include_parent_snapshot=(
                include_parent_snapshot if include_parent_snapshot is not None else True
            ),
        )


# Different storage field name for backcompat
@whitelist_for_serdes(storage_field_names={"code_location_origin": "repository_location_origin"})
@record
class NotebookPathArgs:
    code_location_origin: CodeLocationOrigin
    notebook_path: str


@whitelist_for_serdes
@record_custom
class ExternalScheduleExecutionArgs(IHaveNew):
    repository_origin: RemoteRepositoryOrigin
    instance_ref: Optional[InstanceRef]
    schedule_name: str
    scheduled_execution_timestamp: Optional[float]
    scheduled_execution_timezone: Optional[str]
    log_key: Sequence[str]
    timeout: Optional[int]

    def __new__(
        cls,
        repository_origin: RemoteRepositoryOrigin,
        instance_ref: Optional[InstanceRef],
        schedule_name: str,
        scheduled_execution_timestamp: Optional[float] = None,
        scheduled_execution_timezone: Optional[str] = None,
        log_key: Optional[Sequence[str]] = None,
        timeout: Optional[int] = None,
    ):
        return super().__new__(
            cls,
            repository_origin=repository_origin,
            instance_ref=instance_ref,
            schedule_name=schedule_name,
            scheduled_execution_timestamp=scheduled_execution_timestamp,
            scheduled_execution_timezone=scheduled_execution_timezone,
            log_key=log_key if log_key is not None else [],
            timeout=timeout,
        )


@whitelist_for_serdes
@record_custom
class SensorExecutionArgs(IHaveNew):
    repository_origin: RemoteRepositoryOrigin
    instance_ref: Optional[InstanceRef]
    sensor_name: str
    last_tick_completion_time: Optional[float]
    last_run_key: Optional[str]
    cursor: Optional[str]
    log_key: Sequence[str]
    timeout: Optional[int]
    last_sensor_start_time: Optional[float]
    # deprecated
    last_completion_time: Optional[float]

    def __new__(
        cls,
        repository_origin: RemoteRepositoryOrigin,
        instance_ref: Optional[InstanceRef],
        sensor_name: str,
        last_tick_completion_time: Optional[float] = None,
        last_run_key: Optional[str] = None,
        cursor: Optional[str] = None,
        log_key: Optional[Sequence[str]] = None,
        timeout: Optional[int] = None,
        last_sensor_start_time: Optional[float] = None,
        # deprecated param
        last_completion_time: Optional[float] = None,
    ):
        # populate both last_tick_completion_time and last_completion_time for backcompat, so that
        # older versions can still construct the correct context object.  We manually create the
        # normalized value here instead of using normalize_renamed_param so that we can avoid the
        # check.invariant that would be triggered by setting both values.
        normalized_last_tick_completion_time = (
            last_tick_completion_time if last_tick_completion_time else last_completion_time
        )
        return super().__new__(
            cls,
            repository_origin=repository_origin,
            instance_ref=instance_ref,
            sensor_name=sensor_name,
            last_tick_completion_time=normalized_last_tick_completion_time,
            last_run_key=last_run_key,
            cursor=cursor,
            log_key=log_key if log_key is not None else [],
            timeout=timeout,
            last_sensor_start_time=last_sensor_start_time,
            last_completion_time=normalized_last_tick_completion_time,
        )

    def with_default_timeout(self, timeout: int) -> "SensorExecutionArgs":
        """If the timeout is not explicitly set, provides a default timeout which is used for the sensor execution."""
        if self.timeout is None:
            return copy(self, timeout=timeout)
        return self


@whitelist_for_serdes
@record
class ExternalJobArgs:
    repository_origin: RemoteRepositoryOrigin
    instance_ref: InstanceRef
    name: str


@whitelist_for_serdes
@record
class ShutdownServerResult:
    success: bool
    serializable_error_info: Optional[SerializableErrorInfo]


@whitelist_for_serdes
@record
class CancelExecutionRequest:
    run_id: str


@whitelist_for_serdes
@record
class CancelExecutionResult:
    success: bool
    message: Optional[str]
    serializable_error_info: Optional[SerializableErrorInfo]


@whitelist_for_serdes
@record
class CanCancelExecutionRequest:
    run_id: str


@whitelist_for_serdes
@record
class CanCancelExecutionResult:
    can_cancel: bool


@whitelist_for_serdes
@record
class StartRunResult:
    success: bool
    message: Optional[str]
    serializable_error_info: Optional[SerializableErrorInfo]


@whitelist_for_serdes
@record
class GetCurrentImageResult:
    current_image: Optional[str]
    serializable_error_info: Optional[SerializableErrorInfo]


@whitelist_for_serdes
@record
class GetCurrentRunsResult:
    current_runs: Sequence[str]
    serializable_error_info: Optional[SerializableErrorInfo]
