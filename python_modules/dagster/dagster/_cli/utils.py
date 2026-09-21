import logging
import os
import tempfile
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar

import click

import dagster._check as check
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.instance.config import is_dagster_home_set
from dagster._core.secrets.env_file import get_env_var_dict
from dagster._utils.env import environ

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])

if TYPE_CHECKING:
    from dagster._core.remote_representation.external import RemoteRepository


def has_pyproject_dagster_block(path: str) -> bool:
    import tomli  # defer for perf

    if not os.path.exists(path):
        return False
    with open(path, "rb") as f:
        data = tomli.load(f)
        if not isinstance(data, dict):
            return False

        return "dagster" in data.get("tool", {}) or "dg" in data.get("tool", {})


@contextmanager
def _inject_local_env_file(logger: logging.Logger) -> Iterator[None]:
    dotenv_file_path = os.getcwd()

    env_var_dict = get_env_var_dict(dotenv_file_path)

    with environ(env_var_dict):
        if len(env_var_dict):
            logger.info(
                "Loaded environment variables from .env file: "
                + ",".join([env_var for env_var in env_var_dict]),
            )
        yield


TMP_DAGSTER_HOME_PREFIX = ".tmp_dagster_home_"


@contextmanager
def _get_temporary_instance(cli_command: str, logger: logging.Logger) -> Iterator[DagsterInstance]:
    # make the temp dir in the cwd since default temp dir roots
    # have issues with FS notify-based event log watching
    # use a fixed prefix so that consumer projects can reliably manage,
    # e.g., add to .gitignore
    with tempfile.TemporaryDirectory(prefix=TMP_DAGSTER_HOME_PREFIX, dir=os.getcwd()) as tempdir:
        logger.info(
            f"Using temporary directory {tempdir} for storage. This will be removed when"
            f" {cli_command} exits."
        )
        logger.info(
            "To persist information across sessions, set the environment variable DAGSTER_HOME"
            " to a directory to use."
        )

        with DagsterInstance.from_ref(
            InstanceRef.from_dir(tempdir, config_dir=os.getcwd())
        ) as instance:
            yield instance


@contextmanager
def get_temporary_instance_for_cli(
    cli_command: str = "this command",
    logger: logging.Logger = logging.getLogger("dagster"),
) -> Iterator[DagsterInstance]:
    with _inject_local_env_file(logger):
        with _get_temporary_instance(cli_command, logger) as instance:
            yield instance


@contextmanager
def get_possibly_temporary_instance_for_cli(
    cli_command: str = "this command",
    instance_ref: InstanceRef | None = None,
    logger: logging.Logger = logging.getLogger("dagster"),
) -> Iterator[DagsterInstance]:
    """Create an instance at the entrypoint for a dagster CLI command. Handles loading
    any environment variables from a local .env file and finding the right path to load
    the instance from. If DAGSTER_HOME is not set and an instance_ref is not passed in, will
    create a temporary dagster.yaml file under the cwd.

    Parameters:
    cli_command: The name of the command - optional, used for logging messages.
    instance_ref: For commands that delegate to other commands, they can pass in
        a serialized instance_ref object rather than loading it from a dagster.yaml file.
    logger: Customize any log messages emitted while creating the instance.
    """
    with _inject_local_env_file(logger):
        if instance_ref:
            with DagsterInstance.from_ref(instance_ref) as instance:
                yield instance
        elif is_dagster_home_set():
            with DagsterInstance.get() as instance:
                yield instance
        else:
            with _get_temporary_instance(cli_command, logger) as instance:
                yield instance


@contextmanager
def get_instance_for_cli(
    instance_ref: InstanceRef | None = None,
    logger: logging.Logger = logging.getLogger("dagster"),
) -> Iterator[DagsterInstance]:
    """Create an instance at the entrypoint for a dagster CLI command. Handles loading
    any environment variables from a local .env file and finding the right path to load
    the instance from. Requires DAGSTER_HOME to be set or instance_ref to be passed in.

    Parameters:
    cli_command: The name of the command - optional, used for logging messages.
    instance_ref: For commands that delegate to other commands, they can pass in
        a serialized instance_ref object rather than loading it from a dagster.yaml file.
    logger: Customize any log messages emitted while creating the instance.
    """
    with _inject_local_env_file(logger):
        if instance_ref:
            with DagsterInstance.from_ref(instance_ref) as instance:
                yield instance
        else:
            with DagsterInstance.get() as instance:
                yield instance


def assert_no_remaining_opts(opts: Mapping[str, object]) -> None:
    if opts:
        check.failed(
            f"Unexpected options remaining: {list(opts.keys())}. Ensure that all options are extracted."
        )


def serialize_sorted_quoted(strings: Iterable[str]) -> str:
    return "[" + ", ".join([f"'{s}'" for s in sorted(list(strings))]) + "]"


def validate_dagster_home_is_set() -> None:
    if not is_dagster_home_set():
        raise click.UsageError(
            "The environment variable $DAGSTER_HOME is not set. Dagster requires this "
            "environment variable to be set to an existing directory in your filesystem "
            "that contains your dagster instance configuration file (dagster.yaml).\n"
            "You can resolve this error by exporting the environment variable."
            "For example, you can run the following command in your shell or "
            "include it in your shell configuration file:\n"
            '\texport DAGSTER_HOME="~/dagster_home"'
            "\n\n"
        )


def validate_repo_has_defined_sensors(repo: "RemoteRepository") -> None:
    if not repo.get_sensors():
        raise click.UsageError(f"There are no sensors defined for repository {repo.name}.")


def validate_repo_has_defined_schedules(repo: "RemoteRepository") -> None:
    if not repo.get_schedules():
        raise click.UsageError(f"There are no schedules defined for repository {repo.name}.")


DEFS_STATE_INFO_OVERRIDE_PATH_ENV = "DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH"


def resolve_serialized_defs_state_info(
    serialized_arg: str | None,
    logger: logging.Logger,
) -> str | None:
    """Return the serialized DefsStateInfo to use at server boot.

    If DAGSTER_DEFS_STATE_INFO_OVERRIDE_PATH is set and the file at that path
    is readable, its contents are authoritative and win over the
    --defs-state-info CLI arg — including when the file is empty, which means
    "explicitly no pin." The CLI arg is only used when the env var is unset or
    the file is unreadable/missing.

    Empty must mean "no pin" rather than "fall back to the arg": the launcher
    that writes the file may have moved the pin from some value to None after
    the pod spec was created, and the spec args still carry the old value. A
    restart that fell back to the arg would silently revive the stale pin.

    This lets a launcher (e.g. K8sUserCodeLauncher) update the pin via a
    ConfigMap-mounted file without rewriting the pod's spec args — which
    would otherwise trigger a rolling restart and defeat in-place reload.
    Reads at boot only; live updates flow through the gRPC ReloadCodeWithState
    RPC, not the file.
    """
    override_path = os.environ.get(DEFS_STATE_INFO_OVERRIDE_PATH_ENV)
    if not override_path:
        return serialized_arg
    try:
        with open(override_path, encoding="utf-8") as f:
            content = f.read().strip()
    except FileNotFoundError:
        logger.info(
            "%s set to %s but file not found; falling back to --defs-state-info arg.",
            DEFS_STATE_INFO_OVERRIDE_PATH_ENV,
            override_path,
        )
        return serialized_arg
    except OSError as e:
        logger.warning(
            "Could not read defs_state_info override at %s: %s; "
            "falling back to --defs-state-info arg.",
            override_path,
            e,
        )
        return serialized_arg
    if not content:
        logger.info(
            "Defs state override file %s present but empty; booting with no defs_state_info pin.",
            override_path,
        )
        return None
    logger.info(
        "Loaded defs_state_info from override file %s (len=%d).",
        override_path,
        len(content),
    )
    return content
