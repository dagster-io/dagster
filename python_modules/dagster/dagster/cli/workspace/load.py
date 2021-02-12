import os
import sys
import warnings
from collections import OrderedDict

from dagster import check
from dagster.core.code_pointer import rebase_file
from dagster.core.host_representation import (
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.utils import load_yaml_from_path, merge_dicts

from .config_schema import ensure_workspace_config
from .workspace import Workspace


def load_workspace_from_yaml_paths(yaml_paths):
    return Workspace(location_origins_from_yaml_paths(yaml_paths))


def location_origins_from_yaml_paths(yaml_paths):
    check.list_param(yaml_paths, "yaml_paths", str)

    workspace_configs = [load_yaml_from_path(yaml_path) for yaml_path in yaml_paths]
    origins_by_name = OrderedDict()
    for workspace_config, yaml_path in zip(workspace_configs, yaml_paths):
        check.invariant(
            workspace_config is not None,
            (
                "Could not parse a workspace config from the yaml file at {yaml_path}. Check that "
                "the file contains valid yaml."
            ).format(yaml_path=os.path.abspath(yaml_path)),
        )

        origins_by_name = merge_dicts(
            origins_by_name,
            location_origins_from_config(workspace_config, yaml_path),
        )

    return list(origins_by_name.values())


def load_workspace_from_config(workspace_config, yaml_path):
    return Workspace(
        list(
            location_origins_from_config(
                workspace_config,
                yaml_path,
            ).values()
        ),
    )


def location_origins_from_config(workspace_config, yaml_path):
    workspace_config = ensure_workspace_config(workspace_config, yaml_path)

    location_origins = OrderedDict()
    for location_config in workspace_config["load_from"]:
        origin = _location_origin_from_location_config(location_config, yaml_path)
        check.invariant(
            location_origins.get(origin.location_name) is None,
            'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                name=origin.location_name,
            ),
        )

        location_origins[origin.location_name] = origin

    return location_origins


def _location_origin_from_module_config(
    python_module_config, default_executable_path=sys.executable
):
    module_name, attribute, location_name, executable_path = _get_module_config_data(
        python_module_config, default_executable_path
    )
    return location_origin_from_module_name(module_name, attribute, location_name, executable_path)


def _get_module_config_data(python_module_config, default_executable_path):
    return (
        (python_module_config, None, None, default_executable_path)
        if isinstance(python_module_config, str)
        else (
            python_module_config["module_name"],
            python_module_config.get("attribute"),
            python_module_config.get("location_name"),
            _get_executable_path(
                python_module_config.get("executable_path"), default_executable_path
            ),
        )
    )


def _create_python_env_location_origin(loadable_target_origin, location_name):
    return ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)


def location_origin_from_module_name(
    module_name, attribute, location_name=None, executable_path=sys.executable
):
    check.str_param(module_name, "module_name")
    check.opt_str_param(attribute, "attribute")
    check.opt_str_param(location_name, "location_name")

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        module_name=module_name,
        working_directory=None,
        attribute=attribute,
        package_name=None,
    )

    return _create_python_env_location_origin(loadable_target_origin, location_name)


def _location_origin_from_package_config(
    python_package_config, default_executable_path=sys.executable
):
    module_name, attribute, location_name, executable_path = _get_package_config_data(
        python_package_config, default_executable_path
    )
    return location_origin_from_package_name(module_name, attribute, location_name, executable_path)


def _get_package_config_data(python_package_config, default_executable_path):
    return (
        (python_package_config, None, None, default_executable_path)
        if isinstance(python_package_config, str)
        else (
            python_package_config["package_name"],
            python_package_config.get("attribute"),
            python_package_config.get("location_name"),
            _get_executable_path(
                python_package_config.get("executable_path"), default_executable_path
            ),
        )
    )


def location_origin_from_package_name(
    package_name, attribute, location_name=None, executable_path=sys.executable
):
    check.str_param(package_name, "package_name")
    check.opt_str_param(attribute, "attribute")
    check.opt_str_param(location_name, "location_name")

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute=attribute,
        package_name=package_name,
    )
    return _create_python_env_location_origin(
        loadable_target_origin,
        location_name,
    )


def _location_origin_from_python_file_config(
    python_file_config,
    yaml_path,
    default_executable_path=sys.executable,
):
    check.str_param(yaml_path, "yaml_path")

    (
        absolute_path,
        attribute,
        location_name,
        working_directory,
        executable_path,
    ) = _get_python_file_config_data(python_file_config, yaml_path, default_executable_path)

    return location_origin_from_python_file(
        absolute_path,
        attribute,
        working_directory,
        location_name,
        executable_path,
    )


def _get_python_file_config_data(python_file_config, yaml_path, default_executable_path):
    return (
        (rebase_file(python_file_config, yaml_path), None, None, None, default_executable_path)
        if isinstance(python_file_config, str)
        else (
            rebase_file(python_file_config["relative_path"], yaml_path),
            python_file_config.get("attribute"),
            python_file_config.get("location_name"),
            rebase_file(python_file_config.get("working_directory"), yaml_path)
            if python_file_config.get("working_directory")
            else rebase_file(os.path.dirname(yaml_path), yaml_path),
            _get_executable_path(
                python_file_config.get("executable_path"), default_executable_path
            ),
        )
    )


def location_origin_from_python_file(
    python_file,
    attribute,
    working_directory,
    location_name=None,
    executable_path=sys.executable,
):
    check.str_param(python_file, "python_file")
    check.opt_str_param(attribute, "attribute")
    check.opt_str_param(working_directory, "working_directory")
    check.opt_str_param(location_name, "location_name")

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=python_file,
        module_name=None,
        working_directory=working_directory,
        attribute=attribute,
    )

    return _create_python_env_location_origin(
        loadable_target_origin,
        location_name,
    )


def _location_origin_from_grpc_server_config(grpc_server_config, yaml_path):
    check.dict_param(grpc_server_config, "grpc_server_config")
    check.str_param(yaml_path, "yaml_path")

    port, socket, host, location_name = (
        grpc_server_config.get("port"),
        grpc_server_config.get("socket"),
        grpc_server_config.get("host"),
        grpc_server_config.get("location_name"),
    )

    check.invariant(
        (socket or port) and not (socket and port), "must supply either a socket or a port"
    )

    if not host:
        host = "localhost"

    return GrpcServerRepositoryLocationOrigin(
        port=port,
        socket=socket,
        host=host,
        location_name=location_name,
    )


def _get_executable_path(executable_path, default):
    # do shell expansion on path
    return os.path.expanduser(executable_path) if executable_path else default


def _location_origin_from_python_environment_config(python_environment_config, yaml_path):
    check.dict_param(python_environment_config, "python_environment_config")
    check.str_param(yaml_path, "yaml_path")

    executable_path, target_config = (
        _get_executable_path(python_environment_config["executable_path"], None),
        python_environment_config["target"],
    )

    check.invariant(is_target_config(target_config))

    python_file_config, python_module_config, python_package_config = (
        target_config.get("python_file"),
        target_config.get("python_module"),
        target_config.get("python_package"),
    )

    if python_file_config:
        return _location_origin_from_python_file_config(
            python_file_config, yaml_path, executable_path
        )
    elif python_module_config:
        return _location_origin_from_module_config(python_module_config, executable_path)
    else:
        check.invariant(python_package_config)
        return _location_origin_from_package_config(python_package_config, executable_path)


def _location_origin_from_location_config(location_config, yaml_path):
    check.dict_param(location_config, "location_config")
    check.str_param(yaml_path, "yaml_path")

    if is_target_config(location_config):
        return _location_origin_from_target_config(location_config, yaml_path)

    elif "grpc_server" in location_config:
        return _location_origin_from_grpc_server_config(location_config["grpc_server"], yaml_path)

    elif "python_environment" in location_config:
        warnings.warn(
            "The `python_environment` key is deprecated. Use `python_file`, `python_package`, or "
            "`python_module` with the `executable_path` attribute set if you want to load a "
            "repository in a different python environment."
        )
        return _location_origin_from_python_environment_config(
            location_config["python_environment"], yaml_path
        )
    else:
        check.not_implemented("Unsupported location config: {}".format(location_config))


def is_target_config(potential_target_config):
    return isinstance(potential_target_config, dict) and (
        potential_target_config.get("python_file")
        or potential_target_config.get("python_module")
        or potential_target_config.get("python_package")
    )


def _location_origin_from_target_config(target_config, yaml_path):
    check.dict_param(target_config, "target_config")
    check.param_invariant(is_target_config(target_config), "target_config")
    check.str_param(yaml_path, "yaml_path")

    if "python_file" in target_config:
        return _location_origin_from_python_file_config(target_config["python_file"], yaml_path)

    elif "python_module" in target_config:
        return _location_origin_from_module_config(target_config["python_module"])

    elif "python_package" in target_config:
        return _location_origin_from_package_config(target_config["python_package"])

    else:
        check.failed("invalid target_config")
