import logging
import os
import tempfile
from contextlib import contextmanager
from typing import Iterator, Optional

from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.instance.config import is_dagster_home_set
from dagster._core.secrets.env_file import get_env_var_dict
from dagster._utils.env import environ


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


@contextmanager
def _get_temporary_instance(cli_command: str, logger: logging.Logger) -> Iterator[DagsterInstance]:
    # make the temp dir in the cwd since default temp dir roots
    # have issues with FS notify-based event log watching
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tempdir:
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
    instance_ref: Optional[InstanceRef] = None,
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
    instance_ref: Optional[InstanceRef] = None,
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
