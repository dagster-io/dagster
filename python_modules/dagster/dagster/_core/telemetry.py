"""As an open source project, we collect usage statistics to inform development priorities.
For more information, check out the docs at https://docs.dagster.io/about/telemetry'.

To see the logs we send, inspect $DAGSTER_HOME/logs/ if $DAGSTER_HOME is set or ~/.dagster/logs/

See class TelemetryEntry for logged fields.

For local development:
  Spin up local telemetry server and set the environment variable DAGSTER_TELEMETRY_URL = 'http://localhost:3000/actions'
  To test RotatingFileHandler, can set MAX_BYTES = 500
"""

import datetime
import hashlib
import inspect
import os
import uuid
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, Union, overload

from dagster_shared.telemetry import (
    DAGSTER_HOME_FALLBACK,
    TelemetryEntry,
    TelemetrySettings,
    dagster_home_if_set,
    get_or_set_instance_id,
    log_telemetry_action,
    write_telemetry_log_line,
)
from typing_extensions import ParamSpec

import dagster._check as check
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicyType
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.definitions.job_base import IJob
from dagster._core.definitions.reconstruct import (
    ReconstructableJob,
    ReconstructableRepository,
    get_ephemeral_repository_name,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.plan.objects import StepSuccessData
from dagster._core.instance import DagsterInstance
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.remote_representation.external import (
        RemoteJob,
        RemoteRepository,
        RemoteResource,
    )
    from dagster._core.workspace.context import IWorkspaceProcessContext

TELEMETRY_STR = ".telemetry"
INSTANCE_ID_STR = "instance_id"
ENABLED_STR = "enabled"
UPDATE_REPO_STATS = "update_repo_stats"
# 'dagit' name is deprecated but we keep the same telemetry action name to avoid data disruption
START_DAGSTER_WEBSERVER = "start_dagit_webserver"
DAEMON_ALIVE = "daemon_alive"
SCHEDULED_RUN_CREATED = "scheduled_run_created"
SENSOR_RUN_CREATED = "sensor_run_created"
BACKFILL_RUN_CREATED = "backfill_run_created"
STEP_START_EVENT = "step_start_event"
STEP_SUCCESS_EVENT = "step_success_event"
STEP_FAILURE_EVENT = "step_failure_event"


TELEMETRY_WHITELISTED_FUNCTIONS = {
    "_logged_execute_job",
    "execute_execute_command",
    "execute_launch_command",
    "_daemon_run_command",
    "execute_materialize_command",
}


P = ParamSpec("P")
T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


@overload
def telemetry_wrapper(target_fn: T_Callable) -> T_Callable: ...


@overload
def telemetry_wrapper(
    *,
    metadata: Optional[Mapping[str, str]],
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def telemetry_wrapper(
    target_fn: Optional[T_Callable] = None, *, metadata: Optional[Mapping[str, str]] = None
) -> Union[T_Callable, Callable[[Callable[P, T]], Callable[P, T]]]:
    """Wrapper around functions that are logged. Will log the function_name, client_time, and
    elapsed_time, and success.

    Wrapped function must be in the list of whitelisted function, and must have a DagsterInstance
    parameter named 'instance' in the signature.
    """
    if target_fn is not None:
        return _telemetry_wrapper(target_fn)

    def _wraps(f: Callable[P, T]) -> Callable[P, T]:
        return _telemetry_wrapper(f, metadata)

    return _wraps


def _telemetry_wrapper(
    f: Callable[P, T], metadata: Optional[Mapping[str, str]] = None
) -> Callable[P, T]:
    metadata = check.opt_mapping_param(metadata, "metadata", key_type=str, value_type=str)

    if f.__name__ not in TELEMETRY_WHITELISTED_FUNCTIONS:
        raise DagsterInvariantViolationError(
            f"Attempted to log telemetry for function {f.__name__} that is not in telemetry whitelisted "
            f"functions list: {TELEMETRY_WHITELISTED_FUNCTIONS}."
        )
    sig = inspect.signature(f)
    instance_index = None
    for i, name in enumerate(sig.parameters):
        if name == "instance":
            instance_index = i
            break

    if instance_index is None:
        raise DagsterInvariantViolationError(
            "Attempted to log telemetry for function {name} that does not take a DagsterInstance "
            "in a parameter called 'instance'"
        )

    @wraps(f)
    def wrap(*args: P.args, **kwargs: P.kwargs) -> T:
        instance = _check_telemetry_instance_param(args, kwargs, instance_index)
        start_time = datetime.datetime.now()
        log_action(
            instance=instance,
            action=f.__name__ + "_started",
            client_time=start_time,
            metadata=metadata,
        )
        result = f(*args, **kwargs)
        end_time = datetime.datetime.now()
        success_metadata = {"success": getattr(result, "success", None)}
        log_action(
            instance=instance,
            action=f.__name__ + "_ended",
            client_time=end_time,
            elapsed_time=end_time - start_time,
            metadata=merge_dicts(success_metadata, metadata),
        )
        return result

    return wrap


def get_log_queue_dir() -> str:
    """Get the directory where we store log queue files, creating the directory if needed.

    The log queue directory is used to temporarily store logs during upload. This is to prevent
    dropping events or double-sending events that occur during the upload process.

    If $DAGSTER_HOME is set, return $DAGSTER_HOME/.logs_queue/
    Otherwise, return ~/.dagster/.logs_queue/
    """
    dagster_home_path = dagster_home_if_set()
    if dagster_home_path is None:
        dagster_home_path = os.path.expanduser(DAGSTER_HOME_FALLBACK)

    dagster_home_logs_queue_path = dagster_home_path + "/.logs_queue/"
    if not os.path.exists(dagster_home_logs_queue_path):
        os.makedirs(dagster_home_logs_queue_path)

    return dagster_home_logs_queue_path


def _check_telemetry_instance_param(
    args: Sequence[object], kwargs: Mapping[str, object], instance_index: int
) -> DagsterInstance:
    if "instance" in kwargs:
        return check.inst_param(
            kwargs["instance"],  # type: ignore
            "instance",
            DagsterInstance,
            "'instance' parameter passed as keyword argument must be a DagsterInstance",
        )
    else:
        check.invariant(len(args) > instance_index)
        return check.inst_param(
            args[instance_index],  # type: ignore
            "instance",
            DagsterInstance,
            f"'instance' argument at position {instance_index} must be a DagsterInstance",
        )


def _get_instance_telemetry_info(
    instance: DagsterInstance,
) -> TelemetrySettings:
    from dagster._core.storage.runs import SqlRunStorage

    check.inst_param(instance, "instance", DagsterInstance)
    dagster_telemetry_enabled = _get_instance_telemetry_enabled(instance)
    instance_id = None
    run_storage_id = None
    if dagster_telemetry_enabled:
        instance_id = get_or_set_instance_id()
        if isinstance(instance.run_storage, SqlRunStorage):
            run_storage_id = instance.run_storage.get_run_storage_id()

    return TelemetrySettings(
        dagster_telemetry_enabled=dagster_telemetry_enabled,
        instance_id=instance_id,
        run_storage_id=run_storage_id,
    )


def _get_instance_telemetry_enabled(instance: DagsterInstance) -> bool:
    return instance.telemetry_enabled


def hash_name(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def get_stats_from_remote_repo(remote_repo: "RemoteRepository") -> Mapping[str, str]:
    from dagster._core.definitions.partitions.snap import DynamicPartitionsSnap, MultiPartitionsSnap

    num_pipelines_in_repo = len(remote_repo.get_all_jobs())
    num_schedules_in_repo = len(remote_repo.get_schedules())
    num_sensors_in_repo = len(remote_repo.get_sensors())
    asset_node_snaps = remote_repo.get_asset_node_snaps()
    num_assets_in_repo = len(asset_node_snaps)
    remote_resources = remote_repo.get_resources()

    num_checks = len(remote_repo.repository_snap.asset_check_nodes or [])
    num_assets_with_checks = len(
        {c.asset_key for c in remote_repo.repository_snap.asset_check_nodes or []}
    )

    num_partitioned_assets_in_repo = 0
    num_multi_partitioned_assets_in_repo = 0
    num_dynamic_partitioned_assets_in_repo = 0
    num_assets_with_freshness_policies_in_repo = 0
    num_assets_with_eager_auto_materialize_policies_in_repo = 0
    num_assets_with_lazy_auto_materialize_policies_in_repo = 0
    num_assets_with_single_run_backfill_policies_in_repo = 0
    num_assets_with_multi_run_backfill_policies_in_repo = 0
    num_source_assets_in_repo = 0
    num_observable_source_assets_in_repo = 0
    num_dbt_assets_in_repo = 0
    num_assets_with_code_versions_in_repo = 0

    for asset in asset_node_snaps:
        if asset.partitions:
            num_partitioned_assets_in_repo += 1

            if isinstance(asset.partitions, DynamicPartitionsSnap):
                num_dynamic_partitioned_assets_in_repo += 1

            if isinstance(asset.partitions, MultiPartitionsSnap):
                num_multi_partitioned_assets_in_repo += 1

        if asset.legacy_freshness_policy is not None:
            num_assets_with_freshness_policies_in_repo += 1

        if asset.auto_materialize_policy is not None:
            if asset.auto_materialize_policy.policy_type == AutoMaterializePolicyType.EAGER:
                num_assets_with_eager_auto_materialize_policies_in_repo += 1
            else:
                num_assets_with_lazy_auto_materialize_policies_in_repo += 1

        if asset.backfill_policy is not None:
            if asset.backfill_policy.policy_type == BackfillPolicyType.SINGLE_RUN:
                num_assets_with_single_run_backfill_policies_in_repo += 1
            else:
                num_assets_with_multi_run_backfill_policies_in_repo += 1

        if asset.is_source:
            num_source_assets_in_repo += 1

            if asset.is_observable:
                num_observable_source_assets_in_repo += 1

        if asset.code_version is not None:
            num_assets_with_code_versions_in_repo += 1

        if asset.compute_kind == "dbt":
            num_dbt_assets_in_repo += 1

    num_asset_reconciliation_sensors_in_repo = sum(
        1 for sensor in remote_repo.get_sensors() if sensor.name == "asset_reconciliation_sensor"
    )

    return {
        **get_resource_stats(remote_resources=list(remote_resources)),
        "num_pipelines_in_repo": str(num_pipelines_in_repo),
        "num_schedules_in_repo": str(num_schedules_in_repo),
        "num_sensors_in_repo": str(num_sensors_in_repo),
        "num_assets_in_repo": str(num_assets_in_repo),
        "num_source_assets_in_repo": str(num_source_assets_in_repo),
        "num_partitioned_assets_in_repo": str(num_partitioned_assets_in_repo),
        "num_dynamic_partitioned_assets_in_repo": str(num_dynamic_partitioned_assets_in_repo),
        "num_multi_partitioned_assets_in_repo": str(num_multi_partitioned_assets_in_repo),
        "num_assets_with_freshness_policies_in_repo": str(
            num_assets_with_freshness_policies_in_repo
        ),
        "num_assets_with_eager_auto_materialize_policies_in_repo": str(
            num_assets_with_eager_auto_materialize_policies_in_repo
        ),
        "num_assets_with_lazy_auto_materialize_policies_in_repo": str(
            num_assets_with_lazy_auto_materialize_policies_in_repo
        ),
        "num_assets_with_single_run_backfill_policies_in_repo": str(
            num_assets_with_single_run_backfill_policies_in_repo
        ),
        "num_assets_with_multi_run_backfill_policies_in_repo": str(
            num_assets_with_multi_run_backfill_policies_in_repo
        ),
        "num_observable_source_assets_in_repo": str(num_observable_source_assets_in_repo),
        "num_dbt_assets_in_repo": str(num_dbt_assets_in_repo),
        "num_assets_with_code_versions_in_repo": str(num_assets_with_code_versions_in_repo),
        "num_asset_reconciliation_sensors_in_repo": str(num_asset_reconciliation_sensors_in_repo),
        "num_asset_checks": str(num_checks),
        "num_assets_with_checks": str(num_assets_with_checks),
    }


def get_resource_stats(remote_resources: Sequence["RemoteResource"]) -> Mapping[str, Any]:
    used_dagster_resources = []
    used_custom_resources = False

    for resource in remote_resources:
        resource_type = resource.resource_type
        split_resource_type = resource_type.split(".")
        module_name = split_resource_type[0]
        class_name = split_resource_type[-1]

        if resource.is_dagster_maintained:
            used_dagster_resources.append({"module_name": module_name, "class_name": class_name})
        else:
            used_custom_resources = True

    return {
        "dagster_resources": used_dagster_resources,
        "has_custom_resources": str(used_custom_resources),
    }


def log_remote_repo_stats(
    instance: DagsterInstance,
    source: str,
    remote_repo: "RemoteRepository",
    remote_job: Optional["RemoteJob"] = None,
):
    from dagster._core.remote_representation.external import RemoteJob, RemoteRepository

    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(source, "source")
    check.inst_param(remote_repo, "remote_repo", RemoteRepository)
    check.opt_inst_param(remote_job, "remote_job", RemoteJob)

    if _get_instance_telemetry_enabled(instance):
        instance_id = get_or_set_instance_id()

        job_name_hash = hash_name(remote_job.name) if remote_job else ""
        repo_hash = hash_name(remote_repo.name)
        location_name_hash = hash_name(remote_repo.handle.location_name)

        write_telemetry_log_line(
            TelemetryEntry(
                action=UPDATE_REPO_STATS,
                client_time=str(datetime.datetime.now()),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata={
                    **get_stats_from_remote_repo(remote_repo),
                    "source": source,
                    "pipeline_name_hash": job_name_hash,
                    "repo_hash": repo_hash,
                    "location_name_hash": location_name_hash,
                },
            )._asdict()
        )


def log_repo_stats(
    instance: DagsterInstance,
    source: str,
    job: Optional[IJob] = None,
    repo: Optional[ReconstructableRepository] = None,
) -> None:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition

    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(source, "source")
    check.opt_inst_param(job, "job", IJob)
    check.opt_inst_param(repo, "repo", ReconstructableRepository)

    def _get_num_dynamic_partitioned_assets(asset_defs: Sequence[AssetsDefinition]) -> int:
        return sum(
            1
            for asset in asset_defs
            if asset.partitions_def
            and isinstance(asset.partitions_def, DynamicPartitionsDefinition)
        )

    if _get_instance_telemetry_enabled(instance):
        instance_id = get_or_set_instance_id()

        if isinstance(job, ReconstructableJob):
            job_name_hash = hash_name(job.get_definition().name)
            repository = job.get_reconstructable_repository().get_definition()
            repo_hash = hash_name(repository.name)
            num_jobs_in_repo = len(repository.job_names)
            num_schedules_in_repo = len(repository.schedule_defs)
            num_sensors_in_repo = len(repository.sensor_defs)
            all_assets = list(repository.assets_defs_by_key.values())
            num_assets_in_repo = len(all_assets)
            num_dynamic_partitioned_assets_in_repo = _get_num_dynamic_partitioned_assets(all_assets)
        elif isinstance(repo, ReconstructableRepository):
            job_name_hash = ""
            repository = repo.get_definition()
            repo_hash = hash_name(repository.name)
            num_jobs_in_repo = len(repository.job_names)
            num_schedules_in_repo = len(repository.schedule_defs)
            num_sensors_in_repo = len(repository.sensor_defs)
            all_assets = list(repository.assets_defs_by_key.values())
            num_assets_in_repo = len(all_assets)
            num_dynamic_partitioned_assets_in_repo = _get_num_dynamic_partitioned_assets(all_assets)
        else:
            job_name_hash = hash_name(job.get_definition().name)  # type: ignore
            repo_hash = hash_name(get_ephemeral_repository_name(job.get_definition().name))  # type: ignore
            num_jobs_in_repo = 1
            num_schedules_in_repo = 0
            num_sensors_in_repo = 0
            num_assets_in_repo = 0
            num_dynamic_partitioned_assets_in_repo = 0

        write_telemetry_log_line(
            TelemetryEntry(
                action=UPDATE_REPO_STATS,
                client_time=str(datetime.datetime.now()),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata={
                    "source": source,
                    "pipeline_name_hash": job_name_hash,
                    "num_pipelines_in_repo": str(num_jobs_in_repo),
                    "num_schedules_in_repo": str(num_schedules_in_repo),
                    "num_sensors_in_repo": str(num_sensors_in_repo),
                    "num_assets_in_repo": str(num_assets_in_repo),
                    "repo_hash": repo_hash,
                    "num_dynamic_partitioned_assets_in_repo": str(
                        num_dynamic_partitioned_assets_in_repo
                    ),
                },
            )._asdict()
        )


def log_workspace_stats(
    instance: DagsterInstance, workspace_process_context: "IWorkspaceProcessContext"
) -> None:
    from dagster._core.workspace.context import IWorkspaceProcessContext

    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(
        workspace_process_context, "workspace_process_context", IWorkspaceProcessContext
    )

    request_context = workspace_process_context.create_request_context()

    for code_location in request_context.code_locations:
        for repo in code_location.get_repositories().values():
            log_remote_repo_stats(instance, source="dagit", remote_repo=repo)


def log_action(
    instance: DagsterInstance,
    action: str,
    client_time: Optional[datetime.datetime] = None,
    elapsed_time: Optional[datetime.timedelta] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> None:
    log_telemetry_action(
        lambda: _get_instance_telemetry_info(instance),
        action,
        client_time,
        elapsed_time,
        metadata,
    )


def log_dagster_event(event: DagsterEvent, job_context: PlanOrchestrationContext) -> None:
    if not any((event.is_step_start, event.is_step_success, event.is_step_failure)):
        return

    metadata = {
        "run_id_hash": hash_name(job_context.run_id),
        "step_key_hash": hash_name(event.step_key),  # type: ignore
    }

    if event.is_step_start:
        action = STEP_START_EVENT
    elif event.is_step_success:
        action = STEP_SUCCESS_EVENT
        if isinstance(event.event_specific_data, StepSuccessData):  # make mypy happy
            metadata["duration_ms"] = event.event_specific_data.duration_ms  # type: ignore
    else:  # event.is_step_failure
        action = STEP_FAILURE_EVENT

    log_action(
        instance=job_context.instance,
        action=action,
        client_time=datetime.datetime.now(),
        metadata=metadata,
    )
