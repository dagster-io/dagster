"""As an open source project, we collect usage statistics to inform development priorities.
For more information, check out the docs at https://docs.dagster.io/install#telemetry'

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
from typing import Dict, NamedTuple, Optional

import click
import yaml

import dagster._check as check
from dagster._core.definitions.pipeline_base import IPipeline
from dagster._core.definitions.reconstruct import (
    ReconstructablePipeline,
    ReconstructableRepository,
    get_ephemeral_repository_name,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._utils import merge_dicts
from dagster.version import __version__ as dagster_module_version

TELEMETRY_STR = ".telemetry"
INSTANCE_ID_STR = "instance_id"
ENABLED_STR = "enabled"
DAGSTER_HOME_FALLBACK = "~/.dagster"
MAX_BYTES = 10485760  # 10 MB = 10 * 1024 * 1024 bytes
UPDATE_REPO_STATS = "update_repo_stats"
START_DAGIT_WEBSERVER = "start_dagit_webserver"
DAEMON_ALIVE = "daemon_alive"
SCHEDULED_RUN_CREATED = "scheduled_run_created"
SENSOR_RUN_CREATED = "sensor_run_created"
BACKFILL_RUN_CREATED = "backfill_run_created"
OS_DESC = platform.platform()
OS_PLATFORM = platform.system()


TELEMETRY_WHITELISTED_FUNCTIONS = {
    "_logged_execute_pipeline",
    "execute_execute_command",
    "execute_launch_command",
    "_daemon_run_command",
}


def telemetry_wrapper(metadata):
    """
    Wrapper around functions that are logged. Will log the function_name, client_time, and
    elapsed_time, and success.

    Wrapped function must be in the list of whitelisted function, and must have a DagsterInstance
    parameter named 'instance' in the signature.
    """
    if callable(metadata):
        return _telemetry_wrapper(metadata)

    def _wraps(f):
        return _telemetry_wrapper(f, metadata)

    return _wraps


def _telemetry_wrapper(f, metadata=None):
    metadata = check.opt_dict_param(metadata, "metadata", key_type=str, value_type=str)

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
    def wrap(*args, **kwargs):
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


def get_python_version():
    version = sys.version_info
    return "{}.{}.{}".format(version.major, version.minor, version.micro)


class TelemetryEntry(
    NamedTuple(
        "_TelemetryEntry",
        [
            ("action", str),
            ("client_time", str),
            ("event_id", str),
            ("elapsed_time", str),
            ("instance_id", str),
            ("metadata", Dict[str, str]),
            ("python_version", str),
            ("dagster_version", str),
            ("os_desc", str),
            ("os_platform", str),
            ("run_storage_id", str),
        ],
    )
):
    """
    Schema for telemetry logs.

    Currently, log entries are coerced to the same schema to enable storing all entries in one DB
    table with unified schema.

    action - Name of function called i.e. `execute_pipeline_started` (see: fn telemetry_wrapper)
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
        metadata: Optional[Dict[str, str]] = None,
        elapsed_time: Optional[str] = None,
        run_storage_id: Optional[str] = None,
    ):
        action = check.str_param(action, "action")
        client_time = check.str_param(client_time, "action")
        elapsed_time = check.opt_str_param(elapsed_time, "elapsed_time", "")
        event_id = check.str_param(event_id, "event_id")
        instance_id = check.str_param(instance_id, "instance_id")
        metadata = check.opt_dict_param(metadata, "metadata")
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
        )


def _dagster_home_if_set():
    dagster_home_path = os.getenv("DAGSTER_HOME")

    if not dagster_home_path:
        return None

    return os.path.expanduser(dagster_home_path)


def get_or_create_dir_from_dagster_home(target_dir):
    """
    If $DAGSTER_HOME is set, return $DAGSTER_HOME/<target_dir>/
    Otherwise, return ~/.dagster/<target_dir>/

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
        os.makedirs(dagster_home_logs_path)
    return dagster_home_logs_path


def get_log_queue_dir():
    """
    Get the directory where we store log queue files, creating the directory if needed.

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


def _check_telemetry_instance_param(args, kwargs, instance_index):
    if "instance" in kwargs:
        return check.inst_param(
            kwargs["instance"],
            "instance",
            DagsterInstance,
            "'instance' parameter passed as keyword argument must be a DagsterInstance",
        )
    else:
        check.invariant(len(args) > instance_index)
        return check.inst_param(
            args[instance_index],
            "instance",
            DagsterInstance,
            "'instance' argument at position {position} must be a DagsterInstance".format(
                position=instance_index
            ),
        )


def _get_telemetry_logger():

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
def cleanup_telemetry_logger():
    logger = logging.getLogger("dagster_telemetry_logger")
    if len(logger.handlers) == 0:
        return

    check.invariant(len(logger.handlers) == 1)
    handler = next(iter(logger.handlers))
    handler.close()
    logger.removeHandler(handler)


def write_telemetry_log_line(log_line):
    logger = _get_telemetry_logger()
    logger.info(json.dumps(log_line))


def _get_instance_telemetry_info(instance):
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


def _get_instance_telemetry_enabled(instance):
    return instance.telemetry_enabled


def get_or_set_instance_id():
    instance_id = _get_telemetry_instance_id()
    if instance_id is None:
        instance_id = _set_telemetry_instance_id()
    return instance_id


# Gets the instance_id at $DAGSTER_HOME/.telemetry/id.yaml
def _get_telemetry_instance_id():
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
def _set_telemetry_instance_id():
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


def hash_name(name):
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def log_external_repo_stats(instance, source, external_repo, external_pipeline=None):
    from dagster._core.host_representation.external import ExternalPipeline, ExternalRepository

    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(source, "source")
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.opt_inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

    if _get_instance_telemetry_enabled(instance):
        instance_id = get_or_set_instance_id()

        pipeline_name_hash = hash_name(external_pipeline.name) if external_pipeline else ""
        repo_hash = hash_name(external_repo.name)
        num_pipelines_in_repo = len(external_repo.get_all_external_jobs())
        num_schedules_in_repo = len(external_repo.get_external_schedules())
        num_sensors_in_repo = len(external_repo.get_external_sensors())

        write_telemetry_log_line(
            TelemetryEntry(
                action=UPDATE_REPO_STATS,
                client_time=str(datetime.datetime.now()),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata={
                    "source": source,
                    "pipeline_name_hash": pipeline_name_hash,
                    "num_pipelines_in_repo": str(num_pipelines_in_repo),
                    "num_schedules_in_repo": str(num_schedules_in_repo),
                    "num_sensors_in_repo": str(num_sensors_in_repo),
                    "repo_hash": repo_hash,
                },
            )._asdict()
        )


def log_repo_stats(instance, source, pipeline=None, repo=None):
    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(source, "source")
    check.opt_inst_param(pipeline, "pipeline", IPipeline)
    check.opt_inst_param(repo, "repo", ReconstructableRepository)

    if _get_instance_telemetry_enabled(instance):
        instance_id = get_or_set_instance_id()

        if isinstance(pipeline, ReconstructablePipeline):
            pipeline_name_hash = hash_name(pipeline.get_definition().name)
            repository = pipeline.get_reconstructable_repository().get_definition()
            repo_hash = hash_name(repository.name)
            num_pipelines_in_repo = len(repository.pipeline_names)
            num_schedules_in_repo = len(repository.schedule_defs)
            num_sensors_in_repo = len(repository.sensor_defs)
        elif isinstance(repo, ReconstructableRepository):
            pipeline_name_hash = ""
            repository = repo.get_definition()
            repo_hash = hash_name(repository.name)
            num_pipelines_in_repo = len(repository.pipeline_names)
            num_schedules_in_repo = len(repository.schedule_defs)
            num_sensors_in_repo = len(repository.sensor_defs)
        else:
            pipeline_name_hash = hash_name(pipeline.get_definition().name)
            repo_hash = hash_name(get_ephemeral_repository_name(pipeline.get_definition().name))
            num_pipelines_in_repo = 1
            num_schedules_in_repo = 0
            num_sensors_in_repo = 0

        write_telemetry_log_line(
            TelemetryEntry(
                action=UPDATE_REPO_STATS,
                client_time=str(datetime.datetime.now()),
                event_id=str(uuid.uuid4()),
                instance_id=instance_id,
                metadata={
                    "source": source,
                    "pipeline_name_hash": pipeline_name_hash,
                    "num_pipelines_in_repo": str(num_pipelines_in_repo),
                    "num_schedules_in_repo": str(num_schedules_in_repo),
                    "num_sensors_in_repo": str(num_sensors_in_repo),
                    "repo_hash": repo_hash,
                },
            )._asdict()
        )


def log_workspace_stats(instance, workspace_process_context):
    from dagster._core.workspace.context import IWorkspaceProcessContext

    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(
        workspace_process_context, "workspace_process_context", IWorkspaceProcessContext
    )

    request_context = workspace_process_context.create_request_context()

    for repo_location in request_context.repository_locations:
        for external_repo in repo_location.get_repositories().values():
            log_external_repo_stats(instance, source="dagit", external_repo=external_repo)


def log_action(
    instance,
    action,
    client_time=None,
    elapsed_time=None,
    metadata=None,
):
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


TELEMETRY_TEXT = """
  %(telemetry)s

  As an open source project, we collect usage statistics to inform development priorities. For more
  information, read https://docs.dagster.io/install#telemetry.

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
