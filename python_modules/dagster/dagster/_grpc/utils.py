import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.definitions.reconstruct import (
    load_def_in_module,
    load_def_in_package,
    load_def_in_python_file,
)

if TYPE_CHECKING:
    from dagster._core.workspace.autodiscovery import LoadableTarget

_DEFAULT_GRPC_TIMEOUT_IF_NO_ENV_VAR_SET = 60
_DEFAULT_REPOSITORY_TIMEOUT_IF_NO_ENV_VAR_SET = 180


def get_loadable_targets(
    *,
    python_file: Optional[str],
    module_name: Optional[str],
    package_name: Optional[str],
    autoload_defs_module_name: Optional[str],
    working_directory: Optional[str],
    attribute: Optional[str],
) -> Sequence["LoadableTarget"]:
    from dagster._core.workspace.autodiscovery import (
        LoadableTarget,
        autodefs_module_target,
        loadable_targets_from_python_file,
        loadable_targets_from_python_module,
        loadable_targets_from_python_package,
    )

    if python_file:
        return (
            [
                LoadableTarget(
                    attribute, load_def_in_python_file(python_file, attribute, working_directory)
                )
            ]
            if attribute
            else loadable_targets_from_python_file(python_file, working_directory)
        )
    elif module_name:
        return (
            [
                LoadableTarget(
                    attribute, load_def_in_module(module_name, attribute, working_directory)
                )
            ]
            if attribute
            else loadable_targets_from_python_module(module_name, working_directory)
        )
    elif package_name:
        return (
            [
                LoadableTarget(
                    attribute, load_def_in_package(package_name, attribute, working_directory)
                )
            ]
            if attribute
            else loadable_targets_from_python_package(package_name, working_directory)
        )
    elif autoload_defs_module_name:
        return [autodefs_module_target(autoload_defs_module_name, working_directory)]
    else:
        check.failed("invalid")


def max_rx_bytes() -> int:
    env_set = os.getenv("DAGSTER_GRPC_MAX_RX_BYTES")
    if env_set:
        return int(env_set)

    # default 100 MB
    return 100 * (10**6)


def max_send_bytes() -> int:
    env_set = os.getenv("DAGSTER_GRPC_MAX_SEND_BYTES")
    if env_set:
        return int(env_set)

    # default 100 MB
    return 100 * (10**6)


def default_grpc_timeout() -> int:
    env_set = os.getenv("DAGSTER_GRPC_TIMEOUT_SECONDS")
    if env_set:
        return int(env_set)

    return _DEFAULT_GRPC_TIMEOUT_IF_NO_ENV_VAR_SET


def default_repository_grpc_timeout() -> int:
    env_set = os.getenv("DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS")
    if env_set:
        return int(env_set)

    return max(_DEFAULT_REPOSITORY_TIMEOUT_IF_NO_ENV_VAR_SET, default_grpc_timeout())


def default_schedule_grpc_timeout() -> int:
    env_set = os.getenv("DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS")
    if env_set:
        return int(env_set)

    return default_grpc_timeout()


def default_sensor_grpc_timeout() -> int:
    env_set = os.getenv("DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS")
    if env_set:
        return int(env_set)

    return default_grpc_timeout()


def default_grpc_server_shutdown_grace_period():
    # Time to wait for calls to finish before shutting down the server
    # Defaults to the same as default_grpc_timeout() unless
    # DAGSTER_GRPC_SHUTDOWN_GRACE_PERIOD is set
    # default_repository_grpc_timeout(0) is omitted since that call is only
    # made during startup and is unlikely to need to be cleanly completed
    # in order to avoid downtime

    env_set = os.getenv("DAGSTER_GRPC_SHUTDOWN_GRACE_PERIOD")
    if env_set:
        return int(env_set)

    return max(
        default_grpc_timeout(), default_schedule_grpc_timeout(), default_sensor_grpc_timeout()
    )
