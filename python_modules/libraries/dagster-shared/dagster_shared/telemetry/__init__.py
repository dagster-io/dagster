import datetime
import json
import logging
import os
import platform
import sys
import uuid
from collections.abc import Mapping
from logging.handlers import RotatingFileHandler
from typing import Callable, NamedTuple, Optional

import click
import yaml

OS_DESC = platform.platform()
OS_PLATFORM = platform.system()


MAX_BYTES = 10485760  # 10 MB = 10 * 1024 * 1024 bytes

DAGSTER_HOME_FALLBACK = "~/.dagster"
TELEMETRY_STR = ".telemetry"
INSTANCE_ID_STR = "instance_id"

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


def _get_dagster_module_version() -> Optional[str]:
    try:
        from dagster.version import __version__ as dagster_module_version

        return dagster_module_version
    except ImportError:
        return None


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


def dagster_home_if_set() -> Optional[str]:
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
    dagster_home_path = dagster_home_if_set()
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


class TelemetrySettings(NamedTuple):
    dagster_telemetry_enabled: bool
    instance_id: Optional[str]
    run_storage_id: Optional[str]


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


def write_telemetry_log_line(log_line: object) -> None:
    logger = _get_telemetry_logger()
    logger.info(json.dumps(log_line))


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
        return super().__new__(
            cls,
            action=action,
            client_time=client_time,
            elapsed_time=elapsed_time or "",
            event_id=event_id,
            instance_id=instance_id,
            python_version=get_python_version(),
            metadata=metadata or {},
            dagster_version=_get_dagster_module_version() or "None",
            os_desc=OS_DESC,
            os_platform=OS_PLATFORM,
            run_storage_id=run_storage_id or "",
            is_known_ci_env=get_is_known_ci_env(),
        )


def log_telemetry_action(
    get_telemetry_settings: Callable[[], TelemetrySettings],
    action: str,
    client_time: Optional[datetime.datetime] = None,
    elapsed_time: Optional[datetime.timedelta] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> None:
    if client_time is None:
        client_time = datetime.datetime.now()

    (dagster_telemetry_enabled, instance_id, run_storage_id) = get_telemetry_settings()

    if dagster_telemetry_enabled:
        if not instance_id:
            raise Exception("Instance ID must be set when telemetry is enabled")
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


def get_telemetry_enabled_from_dagster_yaml() -> bool:
    """Lightweight check to see if telemetry is enabled by checking $DAGSTER_HOME/dagster.yaml,
    without needing to load the entire Dagster instance.
    """
    dagster_home_path = dagster_home_if_set()
    if dagster_home_path is None:
        return True

    dagster_yaml_path = os.path.join(dagster_home_path, "dagster.yaml")
    if not os.path.exists(dagster_yaml_path):
        return True

    with open(dagster_yaml_path, encoding="utf8") as dagster_yaml_file:
        dagster_yaml_data = yaml.safe_load(dagster_yaml_file)
        if (
            dagster_yaml_data
            and "telemetry" in dagster_yaml_data
            and "enabled" in dagster_yaml_data["telemetry"]
        ):
            return dagster_yaml_data["telemetry"]["enabled"]
    return True


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

    with open(telemetry_id_path, encoding="utf8") as telemetry_id_file:
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


TELEMETRY_TEXT = """
  {telemetry}

  As an open-source project, we collect usage statistics to inform development priorities. For more
  information, read https://docs.dagster.io/about/telemetry.

  We will not see or store any data that is processed by your code.

  To opt-out, add the following to $DAGSTER_HOME/dagster.yaml, creating that file if necessary:

    telemetry:
      enabled: false
""".format(telemetry=click.style("Telemetry:", fg="blue", bold=True))

SLACK_PROMPT = """
  {welcome}

  If you have any questions or would like to engage with the Dagster team, please join us on Slack
  (https://bit.ly/39dvSsF).
""".format(welcome=click.style("Welcome to Dagster!", bold=True))
