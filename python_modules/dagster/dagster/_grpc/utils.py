import os
from typing import TYPE_CHECKING, Sequence

import dagster._check as check
from dagster.core.definitions.reconstruct import (
    load_def_in_module,
    load_def_in_package,
    load_def_in_python_file,
)

if TYPE_CHECKING:
    from dagster.core.workspace.autodiscovery import LoadableTarget


def get_loadable_targets(
    python_file, module_name, package_name, working_directory, attribute
) -> Sequence["LoadableTarget"]:
    from dagster.core.workspace.autodiscovery import (
        LoadableTarget,
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
    else:
        check.failed("invalid")


def max_rx_bytes():
    env_set = os.getenv("DAGSTER_GRPC_MAX_RX_BYTES")
    if env_set:
        return int(env_set)

    # default 50 MB
    return 50 * (10**6)


def max_send_bytes():
    env_set = os.getenv("DAGSTER_GRPC_MAX_SEND_BYTES")
    if env_set:
        return int(env_set)

    # default 50 MB
    return 50 * (10**6)
