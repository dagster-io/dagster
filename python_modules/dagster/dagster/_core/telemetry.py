"""As an open source project, we collect usage statistics to inform development priorities.
For more information, check out the docs at https://docs.dagster.io/getting-started/telemetry'.

To see the logs we send, inspect $DAGSTER_HOME/logs/ if $DAGSTER_HOME is set or ~/.dagster/logs/

See class TelemetryEntry for logged fields.

For local development:
  Spin up local telemetry server and set the environment variable DAGSTER_TELEMETRY_URL = 'http://localhost:3000/actions'
  To test RotatingFileHandler, can set MAX_BYTES = 500
"""

import datetime
import hashlib
import json
import logging
import os
import platform
import sys
import uuid
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)

import click
import yaml
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
from dagster.version import __version__ as dagster_module_version

if TYPE_CHECKING:
    from dagster._core.host_representation.external import (
        ExternalJob,
        ExternalRepository,
        ExternalResource,
    )
    from dagster._core.workspace.context import IWorkspaceProcessContext

TELEMETRY_STR = ".telemetry"
INSTANCE_ID_STR = "instance_id"
ENABLED_STR = "enabled"
DAGSTER_HOME_FALLBACK = "~/.dagster"
MAX_BYTES = 10485760  # 10 MB = 10 * 1024 * 1024 bytes
UPDATE_REPO_STATS = "update_repo_stats"
START_DAGSTER_WEBSERVER = "start_dagit_webserver"
DAEMON_ALIVE = "daemon_alive"
SCHEDULED_RUN_CREATED = "scheduled_run_created"
SENSOR_RUN_CREATED = "sensor_run_created"
BACKFILL_RUN_CREATED = "backfill_run_created"
STEP_START_EVENT = "step_start_event"
STEP_SUCCESS_EVENT = "step_success_event"
STEP_FAILURE_EVENT = "step_failure_event"
OS_DESC = platform.platform()
OS_PLATFORM = platform.system()


TELEMETRY_WHITELISTED_FUNCTIONS = {
    "_logged_execute_job",
    "execute_execute_command",
    "execute_launch_command",
    "_daemon_run_command",
    "execute_materialize_command",
}

KNOWN_CI_ENV_VAR_KEYS = {
    "GITLAB_CI",  # https://docs.gitlab.com/ee/ci/variables/predefined_variables.html
    "GITHUB_ACTION",  # https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
    "BITBUCKET_BUILD_NUMBER",  # https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/
    "JENKINS_URL",  # https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables
    "CODEBUILD_BUILD_ID"  # https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-env-vars.html
    "CIRCLECI",  # https://circleci.com/docs/variables/#built-in-environment-variables
    "TRAVIS",  # https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
    "BUILDKITE",  # https://buildkite.com/docs/pipelines/environment-variables
}

P = ParamSpec("P")
T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


@overload
def telemetry_wrapper(target_fn: T_Callable) -> T_Callable:
    ...


@overload
def telemetry_wrapper(
    *, metadata: Optional[Mapping[str, str]]
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


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
            "Attempted to log telemetry for function {name} that is not in telemetry whitelisted "
            "functions list: {whitelist}.".format(
                name=f.__name__, whitelist=TELEMETRY_WHITELISTED_FUNCTIONS
            )
        )

    var_names = f.__code__.co_varnames
    try:
        instance_index = var_names.index("instance")
    except ValueError as e:
        raise DagsterInvariantViolationError(
            "Attempted to log telemetry for function {name} that does not take a DagsterInstance "
            "in a parameter called 'instance'"
        ) from e

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


def get_python_version() -> str:
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"


def get_is_known_ci_env() -> bool:
    # Many CI tools will use `CI` key which lets us know for sure it's a CI env
    if os.environ.get("CI") is True:
        return True

    # Otherwise looking for predefined env var keys of known CI tools
    for env_var_key in KNOWN_CI_ENV_VAR_KEYS:
        if env_var_key in os.environ:
            return True

    return False


class TelemetryEntry(
    NamedTuple(
        "_TelemetryEntry",
        [
            ("action", str),
            ("client_time", str),
            ("event_id", str),
            ("elapsed_time", str),
            ("instance_id", str),
            ("metadata", Mapping[str, str]),
            ("python_version", str),
            ("dagster_version", str),
            ("os_desc", str),
            ("os_platform", str),
            ("run_storage_id", str),
            ("is_known_ci_env", bool),
        ],
    )
):
    """Schema for telemetry logs.

    Currently, log entries are coerced to the same schema to enable storing all entries in one DB
    table with unified schema.

    action - Name of function called i.e. `execute_job_started` (see: fn telemetry_wrapper)
    client_time - Client time
    elapsed_time - Time elapsed between start of function and end of function call
    event_id - Unique id for the event
    instance_id - Unique id for dagster instance
    python_version - Python version
    metadata - More information i.e. pipeline success (boolean)
    version - Schema version
    dagster_version - Version of the project being used.
    os_desc - String describing OS in use
    os_platform - Terse string describing OS platform - linux, windows, darwin, etc.
    run_storage_id - Unique identifier of run storage database

    If $DAGSTER_HOME is set, then use $DAGSTER_HOME/logs/
    Otherwise, use ~/.dagster/logs/
    """

    def __new__(
        cls,
        action: str,
        client_time: str,
        event_id: str,
        instance_id: str,
        metadata: Optional[Mapping[str, str]] = None,
        elapsed_time: Optional[str] = None,
        run_storage_id: Optional[str] = None,
    ):
        action = check.str_param(action, "action")
        client_time = check.str_param(client_time, "action")
        elapsed_time = check.opt_str_param(elapsed_time, "elapsed_time", "")
        event_id = check.str_param(event_id, "event_id")
        instance_id = check.str_param(instance_id, "instance_id")
        metadata = check.opt_mapping_param(metadata, "metadata")
        run_storage_id = check.opt_str_param(run_storage_id, "run_storage_id", default="")

        return super(TelemetryEntry, cls).__new__(
            cls,
            action=action,
            client_time=client_time,
            elapsed_time=elapsed_time,
            event_id=event_id,
            instance_id=instance_id,
            python_version=get_python_version(),
            metadata=metadata,
            dagster_version=dagster_module_version,
            os_desc=OS_DESC,
            os_platform=OS_PLATFORM,
            run_storage_id=run_storage_id,
            is_known_ci_env=get_is_known_ci_env(),
        )


def _dagster_home_if_set() -> Optional[str]:
    dagster_home_path = os.getenv("DAGSTER_HOME")

    if not dagster_home_path:
        return None

    return os.path.expanduser(dagster_home_path)


def get_or_create_dir_from_dagster_home(target_dir: str) -> str:
    """If $DAGSTER_HOME is set, return $DAGSTER_HOME/<target_dir>/
    Otherwise, return ~/.dagster/<target_dir>/.

    The 'logs' directory is used to cache logs before upload

    The '.logs_queue' directory is used to temporarily store logs during upload. This is to prevent
    dropping events or double-sending events that occur during the upload process.

    The '.telemetry' directory is used to store the instance id.
    """
    dagster_home_path = _dagster_home_if_set()
    if dagster_home_path is None:
        dagster_home_path = os.path.expanduser(DAGSTER_HOME_FALLBACK)

    dagster_home_logs_path = os.path.join(dagster_home_path, target_dir)
    if not os.path.exists(dagster_home_logs_path):
        try:
            os.makedirs(dagster_home_logs_path)
        except FileExistsError:
            # let FileExistsError pass to avoid race condition when multiple places on the same
            # machine try to create this dir
            pass
    return dagster_home_logs_path


def get_log_queue_dir() -> str:
    """Get the directory where we store log queue files, creating the directory if needed.

    The log queue directory is used to temporarily store logs during upload. This is to prevent
    dropping events or double-sending events that occur during the upload process.

    If $DAGSTER_HOME is set, return $DAGSTER_HOME/.logs_queue/
    Otherwise, return ~/.dagster/.logs_queue/
    """
    dagster_home_path = _dagster_home_if_set()
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
            "'instance' argument at position {position} must be a DagsterInstance".format(
                position=instance_index
            ),
        )


def _get_telemetry_logger() -> logging.Logger:
    # If a concurrently running process deleted the logging directory since the
    # last action, we need to make sure to re-create the directory
    # (the logger does not do this itself.)
    dagster_home_path = get_or_create_dir_from_dagster_home("logs")

    logging_file_path = os.path.join(dagster_home_path, "event.log")
    logger = logging.getLogger("dagster_telemetry_logger")

    # If the file we were writing to has been overwritten, dump the existing logger and re-open the stream.
    if not os.path.exists(logging_file_path) and len(logger.handlers) > 0:
        handler = next(iter(logger.handlers))
        handler.close()
        logger.removeHandler(handler)

    if len(logger.handlers) == 0:
        handler = RotatingFileHandler(
            logging_file_path,
            maxBytes=MAX_BYTES,
            backupCount=10,
        )
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    return logger


# For use in test teardown
def cleanup_telemetry_logger() -> None:
    logger = logging.getLogger("dagster_telemetry_logger")
    if len(logger.handlers) == 0:
        return

    check.invariant(len(logger.handlers) == 1)
    handler = next(iter(logger.handlers))
    handler.close()
    logger.removeHandler(handler)


def write_telemetry_log_line(log_line: object) -> None:
    logger = _get_telemetry_logger()
    logger.info(json.dumps(log_line))


def _get_instance_telemetry_info(instance: DagsterInstance):
    from dagster._core.storage.runs import SqlRunStorage

    check.inst_param(instance, "instance", DagsterInstance)
    dagster_telemetry_enabled = _get_instance_telemetry_enabled(instance)
    instance_id = None
    if dagster_telemetry_enabled:
        instance_id = get_or_set_instance_id()

    run_storage_id = None
    if isinstance(instance.run_storage, SqlRunStorage):
        run_storage_id = instance.run_storage.get_run_storage_id()
    return (dagster_telemetry_enabled, instance_id, run_storage_id)


def _get_instance_telemetry_enabled(instance: DagsterInstance) -> bool:
    return instance.telemetry_enabled


def get_or_set_instance_id() -> str:
    instance_id = _get_telemetry_instance_id()
    if instance_id is None:
        instance_id = _set_telemetry_instance_id()
    return instance_id


# Gets the instance_id at $DAGSTER_HOME/.telemetry/id.yaml
def _get_telemetry_instance_id() -> Optional[str]:
    telemetry_id_path = os.path.join(get_or_create_dir_from_dagster_home(TELEMETRY_STR), "id.yaml")
    if not os.path.exists(telemetry_id_path):
        return

    with open(telemetry_id_path, "r", encoding="utf8") as telemetry_id_file:
        telemetry_id_yaml = yaml.safe_load(telemetry_id_file)
        if (
            telemetry_id_yaml
            and INSTANCE_ID_STR in telemetry_id_yaml
            and isinstance(telemetry_id_yaml[INSTANCE_ID_STR], str)
        ):
            return telemetry_id_yaml[INSTANCE_ID_STR]
    return None


# Sets the instance_id at $DAGSTER_HOME/.telemetry/id.yaml
def _set_telemetry_instance_id() -> str:
    click.secho(TELEMETRY_TEXT)
    click.secho(SLACK_PROMPT)

    telemetry_id_path = os.path.join(get_or_create_dir_from_dagster_home(TELEMETRY_STR), "id.yaml")
    instance_id = str(uuid.uuid4())

    try:  # In case we encounter an error while writing to user's file system
        with open(telemetry_id_path, "w", encoding="utf8") as telemetry_id_file:
            yaml.dump({INSTANCE_ID_STR: instance_id}, telemetry_id_file, default_flow_style=False)
        return instance_id
    except Exception:
        return "<<unable_to_write_instance_id>>"


def hash_name(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def get_stats_from_external_repo(external_repo: "ExternalRepository") -> Mapping[str, str]:
    from dagster._core.host_representation.external_data import (
        ExternalDynamicPartitionsDefinitionData,
        ExternalMultiPartitionsDefinitionData,
    )

    num_pipelines_in_repo = len(external_repo.get_all_external_jobs())
    num_schedules_in_repo = len(external_repo.get_external_schedules())
    num_sensors_in_repo = len(external_repo.get_external_sensors())
    external_asset_nodes = external_repo.get_external_asset_nodes()
    num_assets_in_repo = len(external_asset_nodes)
    external_resources = external_repo.get_external_resources()

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

    for asset in external_asset_nodes:
        if asset.partitions_def_data:
            num_partitioned_assets_in_repo += 1

            if isinstance(asset.partitions_def_data, ExternalDynamicPartitionsDefinitionData):
                num_dynamic_partitioned_assets_in_repo += 1

            if isinstance(asset.partitions_def_data, ExternalMultiPartitionsDefinitionData):
                num_multi_partitioned_assets_in_repo += 1

        if asset.freshness_policy is not None:
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
        1
        for external_sensor in external_repo.get_external_sensors()
        if external_sensor.name == "asset_reconciliation_sensor"
    )

    return {
        **get_resource_stats(external_resources=list(external_resources)),
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
    }


def get_resource_stats(external_resources: Sequence["ExternalResource"]) -> Mapping[str, Any]:
    used_dagster_resources = []
    used_custom_resources = False

    for resource in external_resources:
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


def log_external_repo_stats(
    instance: DagsterInstance,
    source: str,
    external_repo: "ExternalRepository",
    external_job: Optional["ExternalJob"] = None,
):
    from dagster._core.host_representation.external import ExternalJob, ExternalRepository

    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(source, "source")
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.opt_inst_param(external_job, "external_job", ExternalJob)

    if _get_instance_telemetry_enabled(instance):
        instance_id = get_or_set_instance_id()

        job_name_hash = hash_name(external_job.name) if external_job else ""
        repo_hash = hash_name(external_repo.name)
        location_name_hash = hash_name(external_repo.handle.location_name)

        write_telemetry_log_line(
            TelemetryEntry(
                action=UPDATE_REPO_STATS,
                client_time=str(datetime.datetime.now()),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata={
                    **get_stats_from_external_repo(external_repo),
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
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.partition import DynamicPartitionsDefinition

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
        for external_repo in code_location.get_repositories().values():
            log_external_repo_stats(instance, source="dagit", external_repo=external_repo)


def log_action(
    instance: DagsterInstance,
    action: str,
    client_time: Optional[datetime.datetime] = None,
    elapsed_time: Optional[datetime.timedelta] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> None:
    check.inst_param(instance, "instance", DagsterInstance)
    if client_time is None:
        client_time = datetime.datetime.now()

    (dagster_telemetry_enabled, instance_id, run_storage_id) = _get_instance_telemetry_info(
        instance
    )

    if dagster_telemetry_enabled:
        # Log general statistics
        write_telemetry_log_line(
            TelemetryEntry(
                action=action,
                client_time=str(client_time),
                elapsed_time=str(elapsed_time),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata=metadata,
                run_storage_id=run_storage_id,
            )._asdict()
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


TELEMETRY_TEXT = """
  %(telemetry)s

  As an open source project, we collect usage statistics to inform development priorities. For more
  information, read https://docs.dagster.io/getting-started/telemetry.

  We will not see or store solid definitions, pipeline definitions, modes, resources, context, or
  any data that is processed within solids and pipelines.

  To opt-out, add the following to $DAGSTER_HOME/dagster.yaml, creating that file if necessary:

    telemetry:
      enabled: false
""" % {
    "telemetry": click.style("Telemetry:", fg="blue", bold=True)
}

SLACK_PROMPT = """
  %(welcome)s

  If you have any questions or would like to engage with the Dagster team, please join us on Slack
  (https://bit.ly/39dvSsF).
""" % {
    "welcome": click.style("Welcome to Dagster!", bold=True)
}
