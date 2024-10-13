import os
from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple, Optional, Sequence

import tomli

from dagster._core.remote_representation.origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.workspace.load import (
    location_origin_from_module_name,
    location_origin_from_package_name,
    location_origin_from_python_file,
    location_origins_from_yaml_paths,
)


class WorkspaceLoadTarget(ABC):
    @abstractmethod
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        """Reloads the CodeLocationOrigins for this workspace."""


class CompositeTarget(
    NamedTuple("CompositeTarget", [("targets", Sequence[WorkspaceLoadTarget])]),
    WorkspaceLoadTarget,
):
    def create_origins(self):
        origins = []
        for target in self.targets:
            origins += target.create_origins()
        return origins


class WorkspaceFileTarget(
    NamedTuple("WorkspaceFileTarget", [("paths", Sequence[str])]), WorkspaceLoadTarget
):
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return location_origins_from_yaml_paths(self.paths)


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


def is_valid_modules_list(modules: List[Dict[str, str]]) -> bool:
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


def get_origins_from_toml(
    path: str,
) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
    with open(path, "rb") as f:
        data = tomli.load(f)
        if not isinstance(data, dict):
            return []

        dagster_block = data.get("tool", {}).get("dagster", {})

        if "module_name" in dagster_block or "modules" in dagster_block:
            assert validate_dagster_block_for_module_name_or_modules(dagster_block) is True

        if "module_name" in dagster_block:
            return ModuleTarget(
                module_name=dagster_block.get("module_name"),
                attribute=None,
                working_directory=os.getcwd(),
                location_name=dagster_block.get("code_location_name"),
            ).create_origins()
        elif "modules" in dagster_block and is_valid_modules_list(dagster_block.get("modules")):
            origins = []
            for module in dagster_block.get("modules"):
                if module.get("type") == "module":
                    origins.extend(
                        ModuleTarget(
                            module_name=module.get("name"),
                            attribute=None,
                            working_directory=os.getcwd(),
                            location_name=dagster_block.get("code_location_name"),
                        ).create_origins()
                    )
            return origins
        else:
            return []


class PyProjectFileTarget(NamedTuple("PyProjectFileTarget", [("path", str)]), WorkspaceLoadTarget):
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return get_origins_from_toml(self.path)


class PythonFileTarget(
    NamedTuple(
        "PythonFileTarget",
        [
            ("python_file", str),
            ("attribute", Optional[str]),
            ("working_directory", Optional[str]),
            ("location_name", Optional[str]),
        ],
    ),
    WorkspaceLoadTarget,
):
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_python_file(
                python_file=self.python_file,
                attribute=self.attribute,
                working_directory=self.working_directory,
                location_name=self.location_name,
            )
        ]


class ModuleTarget(
    NamedTuple(
        "ModuleTarget",
        [
            ("module_name", str),
            ("attribute", Optional[str]),
            ("working_directory", Optional[str]),
            ("location_name", Optional[str]),
        ],
    ),
    WorkspaceLoadTarget,
):
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_module_name(
                self.module_name,
                self.attribute,
                self.working_directory,
                location_name=self.location_name,
            )
        ]


class PackageTarget(
    NamedTuple(
        "ModuleTarget",
        [
            ("package_name", str),
            ("attribute", Optional[str]),
            ("working_directory", Optional[str]),
            ("location_name", Optional[str]),
        ],
    ),
    WorkspaceLoadTarget,
):
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return [
            location_origin_from_package_name(
                self.package_name,
                self.attribute,
                self.working_directory,
                location_name=self.location_name,
            )
        ]


class GrpcServerTarget(
    NamedTuple(
        "ModuleTarget",
        [
            ("host", str),
            ("port", Optional[int]),
            ("socket", Optional[str]),
            ("location_name", Optional[str]),
        ],
    ),
    WorkspaceLoadTarget,
):
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
class EmptyWorkspaceTarget(NamedTuple("EmptyWorkspaceTarget", []), WorkspaceLoadTarget):
    def create_origins(self) -> Sequence[CodeLocationOrigin]:
        return []
