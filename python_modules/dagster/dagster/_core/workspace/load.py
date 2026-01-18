import os
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union, cast

from dagster_shared.yaml_utils import load_yaml_from_path

import dagster._check as check
from dagster._core.code_pointer import rebase_file
from dagster._core.instance import DagsterInstance
from dagster._core.remote_origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.config_schema import ensure_workspace_config

if TYPE_CHECKING:
    from dagster._core.workspace.context import WorkspaceProcessContext


def load_workspace_process_context_from_yaml_paths(
    instance: DagsterInstance, yaml_paths: Sequence[str], version: str = ""
) -> "WorkspaceProcessContext":
    from dagster._core.workspace.context import WorkspaceProcessContext
    from dagster._core.workspace.load_target import WorkspaceFileTarget

    return WorkspaceProcessContext(instance, WorkspaceFileTarget(paths=yaml_paths), version=version)


def location_origins_from_yaml_paths(
    yaml_paths: Sequence[str],
) -> Sequence[CodeLocationOrigin]:
    check.sequence_param(yaml_paths, "yaml_paths", str)

    workspace_configs = [load_yaml_from_path(yaml_path) for yaml_path in yaml_paths]
    origins_by_name: dict[str, CodeLocationOrigin] = OrderedDict()
    for workspace_config, yaml_path in zip(workspace_configs, yaml_paths):
        check.invariant(
            workspace_config is not None,
            (
                f"Could not parse a workspace config from the yaml file at {os.path.abspath(yaml_path)}. Check that "
                "the file contains valid yaml."
            ),
        )

        origins_by_name.update(
            location_origins_from_config(cast("dict", workspace_config), yaml_path)
        )

    return list(origins_by_name.values())


def location_origins_from_config(
    workspace_config: Mapping[str, object], yaml_path: str
) -> Mapping[str, CodeLocationOrigin]:
    workspace_config = ensure_workspace_config(workspace_config, yaml_path)
    location_configs = check.list_elem(workspace_config, "load_from", of_type=dict)
    location_origins: dict[str, CodeLocationOrigin] = OrderedDict()
    for location_config in location_configs:
        origin = _location_origin_from_location_config(location_config, yaml_path)
        check.invariant(
            location_origins.get(origin.location_name) is None,
            f'Cannot have multiple locations with the same name, got multiple "{origin.location_name}"',
        )

        location_origins[origin.location_name] = origin

    return location_origins


def _location_origin_from_module_config(
    python_module_config: Union[str, Mapping[str, str]],
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    (
        module_name,
        attribute,
        working_directory,
        location_name,
        executable_path,
    ) = _get_module_config_data(python_module_config)
    return location_origin_from_module_name(
        module_name, attribute, working_directory, location_name, executable_path
    )


def _get_module_config_data(
    python_module_config: Union[str, Mapping[str, str]],
) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    return (
        (python_module_config, None, None, None, None)
        if isinstance(python_module_config, str)
        else (
            python_module_config["module_name"],
            python_module_config.get("attribute"),
            python_module_config.get("working_directory"),
            python_module_config.get("location_name"),
            _get_executable_path(python_module_config.get("executable_path")),
        )
    )


def _location_origin_from_autoload_config(
    python_module_config: Union[str, Mapping[str, str]],
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    (
        module_name,
        _,
        working_directory,
        location_name,
        executable_path,
    ) = _get_module_config_data(python_module_config)

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        autoload_defs_module_name=module_name,
        working_directory=working_directory,
        attribute=None,
        package_name=None,
    )

    return _create_python_env_location_origin(loadable_target_origin, location_name)


def _create_python_env_location_origin(
    loadable_target_origin: LoadableTargetOrigin, location_name: Optional[str]
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    return ManagedGrpcPythonEnvCodeLocationOrigin(loadable_target_origin, location_name)


def location_origin_from_module_name(
    module_name: str,
    attribute: Optional[str],
    working_directory: Optional[str],
    location_name: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    check.str_param(module_name, "module_name")
    check.opt_str_param(attribute, "attribute")
    check.opt_str_param(working_directory, "working_directory")
    check.opt_str_param(location_name, "location_name")

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        module_name=module_name,
        working_directory=working_directory,
        attribute=attribute,
        package_name=None,
    )

    return _create_python_env_location_origin(loadable_target_origin, location_name)


def location_origin_from_autoload_defs_module_name(
    autoload_defs_module_name: str,
    working_directory: Optional[str],
    location_name: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        module_name=None,
        working_directory=working_directory,
        attribute=None,
        package_name=None,
        autoload_defs_module_name=autoload_defs_module_name,
    )

    return _create_python_env_location_origin(loadable_target_origin, location_name)


def _location_origin_from_package_config(
    python_package_config: Union[str, Mapping[str, str]],
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    (
        module_name,
        attribute,
        working_directory,
        location_name,
        executable_path,
    ) = _get_package_config_data(python_package_config)
    return location_origin_from_package_name(
        module_name, attribute, working_directory, location_name, executable_path
    )


def _get_package_config_data(
    python_package_config: Union[str, Mapping[str, str]],
) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    return (
        (python_package_config, None, None, None, None)
        if isinstance(python_package_config, str)
        else (
            python_package_config["package_name"],
            python_package_config.get("attribute"),
            python_package_config.get("working_directory"),
            python_package_config.get("location_name"),
            _get_executable_path(python_package_config.get("executable_path")),
        )
    )


def location_origin_from_package_name(
    package_name: str,
    attribute: Optional[str],
    working_directory: Optional[str],
    location_name: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    check.str_param(package_name, "package_name")
    check.opt_str_param(attribute, "attribute")
    check.opt_str_param(working_directory, "working_directory")
    check.opt_str_param(location_name, "location_name")

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=executable_path,
        python_file=None,
        module_name=None,
        working_directory=working_directory,
        attribute=attribute,
        package_name=package_name,
    )
    return _create_python_env_location_origin(
        loadable_target_origin,
        location_name,
    )


def _location_origin_from_python_file_config(
    python_file_config: Union[str, Mapping],
    yaml_path: str,
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    check.str_param(yaml_path, "yaml_path")

    (
        absolute_path,
        attribute,
        location_name,
        working_directory,
        executable_path,
    ) = _get_python_file_config_data(python_file_config, yaml_path)

    return location_origin_from_python_file(
        absolute_path,
        attribute,
        working_directory,
        location_name,
        executable_path,
    )


def _get_python_file_config_data(
    python_file_config: Union[str, Mapping], yaml_path: str
) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    return (
        (rebase_file(python_file_config, yaml_path), None, None, None, None)
        if isinstance(python_file_config, str)
        else (
            rebase_file(python_file_config["relative_path"], yaml_path),
            python_file_config.get("attribute"),
            python_file_config.get("location_name"),
            (
                rebase_file(python_file_config["working_directory"], yaml_path)
                if python_file_config.get("working_directory")
                else rebase_file(os.path.dirname(yaml_path), yaml_path)
            ),
            _get_executable_path(python_file_config.get("executable_path")),
        )
    )


def location_origin_from_python_file(
    python_file: str,
    attribute: Optional[str],
    working_directory: Optional[str],
    location_name: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
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


def _location_origin_from_grpc_server_config(
    grpc_server_config: Mapping, yaml_path: str
) -> GrpcServerCodeLocationOrigin:
    check.mapping_param(grpc_server_config, "grpc_server_config")
    check.str_param(yaml_path, "yaml_path")

    port, socket, host, location_name, use_ssl, additional_metadata = (
        grpc_server_config.get("port"),
        grpc_server_config.get("socket"),
        grpc_server_config.get("host"),
        grpc_server_config.get("location_name"),
        grpc_server_config.get("ssl"),
        grpc_server_config.get("additional_metadata"),
    )

    check.invariant(
        (socket or port) and not (socket and port), "must supply either a socket or a port"
    )

    if not host:
        host = "localhost"

    return GrpcServerCodeLocationOrigin(
        port=port,
        socket=socket,
        host=host,
        location_name=location_name,
        use_ssl=use_ssl,
        additional_metadata=additional_metadata,
    )


def _get_executable_path(executable_path: Optional[str]) -> Optional[str]:
    # do shell expansion on path
    return os.path.expanduser(executable_path) if executable_path else None


def _location_origin_from_location_config(
    location_config: Mapping, yaml_path: str
) -> CodeLocationOrigin:
    check.mapping_param(location_config, "location_config")
    check.str_param(yaml_path, "yaml_path")

    if is_target_config(location_config):
        return _location_origin_from_target_config(location_config, yaml_path)

    elif "grpc_server" in location_config:
        return _location_origin_from_grpc_server_config(location_config["grpc_server"], yaml_path)

    else:
        check.not_implemented(f"Unsupported location config: {location_config}")


def is_target_config(potential_target_config: object) -> bool:
    return isinstance(potential_target_config, dict) and bool(
        potential_target_config.get("python_file")
        or potential_target_config.get("python_module")
        or potential_target_config.get("python_package")
        or potential_target_config.get("autoload_defs_module")
    )


def _location_origin_from_target_config(
    target_config: Mapping[str, object], yaml_path: str
) -> ManagedGrpcPythonEnvCodeLocationOrigin:
    check.mapping_param(target_config, "target_config", key_type=str)
    check.param_invariant(is_target_config(target_config), "target_config")
    check.str_param(yaml_path, "yaml_path")

    if "python_file" in target_config:
        python_file_config = cast("Union[str, dict]", target_config["python_file"])
        return _location_origin_from_python_file_config(python_file_config, yaml_path)

    elif "python_module" in target_config:
        python_module_config = cast("Union[str, dict]", target_config["python_module"])
        return _location_origin_from_module_config(python_module_config)

    elif "python_package" in target_config:
        python_package_config = cast("Union[str, dict]", target_config["python_package"])
        return _location_origin_from_package_config(python_package_config)

    elif "autoload_defs_module" in target_config:
        autoload_cfg = cast("Union[str, dict]", target_config["autoload_defs_module"])
        return _location_origin_from_autoload_config(autoload_cfg)

    else:
        check.failed("invalid target_config")
