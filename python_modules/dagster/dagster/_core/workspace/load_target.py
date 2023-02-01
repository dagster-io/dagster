import os
from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Sequence

import tomli

from dagster._core.host_representation.origin import (
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocationOrigin,
)

from .load import (
    location_origin_from_module_name,
    location_origin_from_package_name,
    location_origin_from_python_file,
    location_origins_from_yaml_paths,
)


class WorkspaceLoadTarget(ABC):
    @abstractmethod
    def create_origins(self) -> Sequence[RepositoryLocationOrigin]:
        """Reloads the RepositoryLocationOrigins for this workspace."""


class CompositeTarget(
    NamedTuple("CompositeTarget", [("targets", Sequence[WorkspaceLoadTarget])]), WorkspaceLoadTarget
):
    def create_origins(self):
        origins = []
        for target in self.targets:
            origins += target.create_origins()
        return origins


class WorkspaceFileTarget(
    NamedTuple("WorkspaceFileTarget", [("paths", Sequence[str])]), WorkspaceLoadTarget
):
    def create_origins(self) -> Sequence[RepositoryLocationOrigin]:
        return location_origins_from_yaml_paths(self.paths)


def get_origins_from_toml(path: str) -> Sequence[ManagedGrpcPythonEnvRepositoryLocationOrigin]:
    with open(path, "rb") as f:
        data = tomli.load(f)
        if not isinstance(data, dict):
            return []

        dagster_block = data.get("tool", {}).get("dagster", {})
        if "module_name" in dagster_block:
            return ModuleTarget(
                module_name=dagster_block["module_name"],
                attribute=None,
                working_directory=os.getcwd(),
                location_name=None,
            ).create_origins()
        return []


class PyProjectFileTarget(NamedTuple("PyProjectFileTarget", [("path", str)]), WorkspaceLoadTarget):
    def create_origins(self) -> Sequence[RepositoryLocationOrigin]:
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
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvRepositoryLocationOrigin]:
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
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvRepositoryLocationOrigin]:
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
    def create_origins(self) -> Sequence[ManagedGrpcPythonEnvRepositoryLocationOrigin]:
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
    def create_origins(self) -> Sequence[GrpcServerRepositoryLocationOrigin]:
        return [
            GrpcServerRepositoryLocationOrigin(
                port=self.port,
                socket=self.socket,
                host=self.host,
                location_name=self.location_name,
            )
        ]


#  Utility target for graphql commands that do not require a workspace, e.g. downloading schema
class EmptyWorkspaceTarget(NamedTuple("EmptyWorkspaceTarget", []), WorkspaceLoadTarget):
    def create_origins(self) -> Sequence[RepositoryLocationOrigin]:
        return []
