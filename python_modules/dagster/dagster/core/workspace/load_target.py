from abc import ABC, abstractmethod
from collections import namedtuple

from dagster.core.host_representation.origin import GrpcServerRepositoryLocationOrigin

from .load import (
    location_origin_from_module_name,
    location_origin_from_package_name,
    location_origin_from_python_file,
    location_origins_from_yaml_paths,
)


class WorkspaceLoadTarget(ABC):
    @abstractmethod
    def create_origins(self):
        """Reloads the RepositoryLocationOrigins for this workspace."""


class WorkspaceFileTarget(namedtuple("WorkspaceFileTarget", "paths"), WorkspaceLoadTarget):
    def create_origins(self):
        return location_origins_from_yaml_paths(self.paths)


class PythonFileTarget(
    namedtuple("PythonFileTarget", "python_file attribute working_directory location_name"),
    WorkspaceLoadTarget,
):
    def create_origins(self):
        return [
            location_origin_from_python_file(
                python_file=self.python_file,
                attribute=self.attribute,
                working_directory=self.working_directory,
                location_name=self.location_name,
            )
        ]


class ModuleTarget(
    namedtuple("ModuleTarget", "module_name attribute location_name"), WorkspaceLoadTarget
):
    def create_origins(self):
        return [
            location_origin_from_module_name(
                self.module_name,
                self.attribute,
                location_name=self.location_name,
            )
        ]


class PackageTarget(
    namedtuple("PackageTarget", "package_name attribute location_name"), WorkspaceLoadTarget
):
    def create_origins(self):
        return [
            location_origin_from_package_name(
                self.package_name,
                self.attribute,
                location_name=self.location_name,
            )
        ]


class GrpcServerTarget(
    namedtuple("GrpcServerTarget", "host port socket location_name"), WorkspaceLoadTarget
):
    def create_origins(self):
        return [
            GrpcServerRepositoryLocationOrigin(
                port=self.port,
                socket=self.socket,
                host=self.host,
                location_name=self.location_name,
            )
        ]


#  Utility target for graphql commands that do not require a workspace, e.g. downloading schema
class EmptyWorkspaceTarget(namedtuple("EmptyWorkspaceTarget", ""), WorkspaceLoadTarget):
    def create_origins(self):
        return []
