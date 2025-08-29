import os
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional, Union, cast

from dagster_shared.record import record

from dagster._core.remote_origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    InProcessCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.workspace.load import (
    location_origin_from_autoload_defs_module_name,
    location_origin_from_module_name,
    location_origin_from_package_name,
    location_origin_from_python_file,
    location_origins_from_yaml_paths,
)


class WorkspaceLoadTarget(ABC):
    @abstractmethod
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        """Reloads the CodeLocationOrigins for this workspace."""


@record(kw_only=False)
class CompositeTarget(WorkspaceLoadTarget):
    targets: Sequence[WorkspaceLoadTarget]

    def create_origins(self):
        origins = []
        for target in self.targets:
            origins += target.create_origins()
        return origins


@record(kw_only=False)
class WorkspaceFileTarget(WorkspaceLoadTarget):
    paths: Sequence[str]

    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return location_origins_from_yaml_paths(self.paths)


class InProcessWorkspaceLoadTarget(WorkspaceLoadTarget):
    """A workspace load target that is in-process and does not spin up a gRPC server."""

    def __init__(
        self, origin: Union[InProcessCodeLocationOrigin, Sequence[InProcessCodeLocationOrigin]]
    ):
        self._origins = cast(
            "Sequence[InProcessCodeLocationOrigin]",
            origin if isinstance(origin, list) else [origin],
        )

    def create_origins(self) -> Sequence[InProcessCodeLocationOrigin]:
        return self._origins


def validate_dagster_block_for_module_name_or_modules(dagster_block):
    module_name_present = "module_name" in dagster_block and isinstance(
        dagster_block.get("module_name"), str
    )
    modules_present = "modules" in dagster_block and isinstance(dagster_block.get("modules"), list)

    if module_name_present and modules_present:
        # Here we have the check only for list; to be a bit more forgiving in comparison to 'is_valid_modules_list' in case it's an empty list next to 'module_name' existance
        if len(dagster_block["modules"]) > 0:
            raise ValueError(
                "Only one of 'module_name' or 'modules' should be specified, not both."
            )

    if modules_present and len(dagster_block.get("modules")) == 0:
        raise ValueError("'modules' list should not be empty if specified.")

    return True


def is_valid_modules_list(modules: list[dict[str, str]]) -> bool:
    # Could be skipped theorectically, but double check maybe useful, if this functions finds it's way elsewhere
    if not isinstance(modules, list):
        raise ValueError("Modules should be a list.")

    for index, item in enumerate(modules):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {index} is not a dictionary.")
        if "type" not in item:
            raise ValueError(f"Dictionary at index {index} does not contain the key 'type'.")
        if not isinstance(item["type"], str):
            raise ValueError(f"The 'type' value in dictionary at index {index} is not a string.")
        if "name" not in item:
            raise ValueError(f"Dictionary at index {index} does not contain the key 'name'.")
        if not isinstance(item["name"], str):
            raise ValueError(f"The 'name' value in dictionary at index {index} is not a string.")

    return True


def get_target_from_toml_data(
    data: dict,
) -> Union["ModuleTarget", "AutoloadDefsModuleTarget", list["ModuleTarget"], None]:
    dagster_block = data.get("tool", {}).get("dagster", {})

    if "module_name" in dagster_block or "modules" in dagster_block:
        assert validate_dagster_block_for_module_name_or_modules(dagster_block) is True

    if "module_name" in dagster_block:
        return ModuleTarget(
            module_name=dagster_block.get("module_name"),
            attribute=None,
            working_directory=os.getcwd(),
            location_name=dagster_block.get("code_location_name"),
        )
    elif "modules" in dagster_block and is_valid_modules_list(dagster_block.get("modules")):
        return [
            ModuleTarget(
                module_name=module.get("name"),
                attribute=None,
                working_directory=os.getcwd(),
                location_name=dagster_block.get("code_location_name"),
            )
            for module in dagster_block.get("modules")
            if module.get("type") == "module"
        ]

    # This allows `dagster dev` to work with projects scaffolded by the new `dg` CLI
    # without the need to include a `tool.dagster` section.
    dg_block = data.get("tool", {}).get("dg", {}).get("project", {})
    if dg_block:
        if dg_block.get("autoload_defs"):
            default_autoload_defs_module_name = f"{dg_block['root_module']}.defs"
            autoload_defs_module_name = dg_block.get(
                "defs_module", default_autoload_defs_module_name
            )
            return AutoloadDefsModuleTarget(
                autoload_defs_module_name=autoload_defs_module_name,
                working_directory=os.getcwd(),
                location_name=dg_block.get("code_location_name"),
            )

        default_module_name = f"{dg_block['root_module']}.definitions"
        module_name = dg_block.get("code_location_target_module", default_module_name)

        return ModuleTarget(
            module_name=module_name,
            attribute=None,
            working_directory=os.getcwd(),
            location_name=dg_block.get("code_location_name"),
        )

    return None


def get_origins_from_toml(
    path: str,
) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
    import tomli  # defer for perf

    with open(path, "rb") as f:
        data = tomli.load(f)
        if not isinstance(data, dict):
            return []
        target = get_target_from_toml_data(data)
        if isinstance(target, ModuleTarget):
            return target.create_origins()
        elif isinstance(target, AutoloadDefsModuleTarget):
            return target.create_origins()
        elif isinstance(target, list):
            return [origin for target in target for origin in target.create_origins()]
        else:
            return []


@record(kw_only=False)
class PyProjectFileTarget(WorkspaceLoadTarget):
    path: str

    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return get_origins_from_toml(self.path)


@record(kw_only=False)
class PythonFileTarget(WorkspaceLoadTarget):
    python_file: str
    attribute: Optional[str]
    working_directory: Optional[str]
    location_name: Optional[str]

    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_python_file(
                python_file=self.python_file,
                attribute=self.attribute,
                working_directory=self.working_directory,
                location_name=self.location_name,
            )
        ]


@record(kw_only=False)
class ModuleTarget(WorkspaceLoadTarget):
    module_name: str
    attribute: Optional[str]
    working_directory: Optional[str]
    location_name: Optional[str]

    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_module_name(
                self.module_name,
                self.attribute,
                self.working_directory,
                location_name=self.location_name,
            )
        ]


@record(kw_only=False)
class PackageTarget(WorkspaceLoadTarget):
    package_name: str
    attribute: Optional[str]
    working_directory: Optional[str]
    location_name: Optional[str]

    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_package_name(
                self.package_name,
                self.attribute,
                self.working_directory,
                location_name=self.location_name,
            )
        ]


@record(kw_only=False)
class GrpcServerTarget(WorkspaceLoadTarget):
    host: str
    port: Optional[int]
    socket: Optional[str]
    location_name: Optional[str]

    def create_origins(self) -> Sequence[GrpcServerCodeLocationOrigin]:
        return [
            GrpcServerCodeLocationOrigin(
                port=self.port,
                socket=self.socket,
                host=self.host,
                location_name=self.location_name,
            )
        ]


#  Utility target for graphql commands that do not require a workspace, e.g. downloading schema
@record
class EmptyWorkspaceTarget(WorkspaceLoadTarget):
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return []


@record(kw_only=False)
class AutoloadDefsModuleTarget(WorkspaceLoadTarget):
    autoload_defs_module_name: str
    working_directory: Optional[str]
    location_name: Optional[str]

    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_autoload_defs_module_name(
                self.autoload_defs_module_name,
                self.working_directory,
                location_name=self.location_name,
            )
        ]
