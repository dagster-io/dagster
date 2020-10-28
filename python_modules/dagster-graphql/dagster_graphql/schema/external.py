from __future__ import absolute_import

from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocation,
)
from dagster.utils.error import SerializableErrorInfo
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids
from dagster_graphql.schema.errors import DauphinPythonError


class DauphinRepository(dauphin.ObjectType):
    class Meta(object):
        name = "Repository"

    def __init__(self, repository, repository_location):
        self._repository = check.inst_param(repository, "repository", ExternalRepository)
        self._repository_location = check.inst_param(
            repository_location, "repository_location", RepositoryLocation
        )
        super(DauphinRepository, self).__init__(name=repository.name)

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    location = dauphin.NonNull("RepositoryLocation")
    pipelines = dauphin.non_null_list("Pipeline")
    usedSolids = dauphin.Field(dauphin.non_null_list("UsedSolid"))
    usedSolid = dauphin.Field("UsedSolid", name=dauphin.NonNull(dauphin.String))
    origin = dauphin.NonNull("RepositoryOrigin")
    partitionSets = dauphin.non_null_list("PartitionSet")
    scheduleDefinitions = dauphin.non_null_list("ScheduleDefinition")

    def resolve_id(self, _graphene_info):
        return self._repository.get_external_origin_id()

    def resolve_origin(self, graphene_info):
        origin = self._repository.get_external_origin()
        if isinstance(origin.repository_location_origin, GrpcServerRepositoryLocationOrigin):
            return graphene_info.schema.type_named("GrpcRepositoryOrigin")(origin)
        else:
            return graphene_info.schema.type_named("PythonRepositoryOrigin")(origin)

    def resolve_location(self, graphene_info):
        return graphene_info.schema.type_named("RepositoryLocation")(self._repository_location)

    def resolve_scheduleDefinitions(self, graphene_info):

        schedules = self._repository.get_external_schedules()

        return sorted(
            [
                graphene_info.schema.type_named("ScheduleDefinition")(graphene_info, schedule)
                for schedule in schedules
            ],
            key=lambda schedule: schedule.name,
        )

    def resolve_pipelines(self, graphene_info):
        return sorted(
            [
                graphene_info.schema.type_named("Pipeline")(pipeline)
                for pipeline in self._repository.get_all_external_pipelines()
            ],
            key=lambda pipeline: pipeline.name,
        )

    def resolve_usedSolid(self, _graphene_info, name):
        return get_solid(self._repository, name)

    def resolve_usedSolids(self, _graphene_info):
        return get_solids(self._repository)

    def resolve_partitionSets(self, graphene_info):
        return (
            graphene_info.schema.type_named("PartitionSet")(self._repository.handle, partition_set)
            for partition_set in self._repository.get_external_partition_sets()
        )


class DauphinPythonRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = "PythonRepositoryOrigin"

    executable_path = dauphin.NonNull(dauphin.String)
    repository_metadata = dauphin.non_null_list("RepositoryMetadata")

    def __init__(self, origin):
        check.inst_param(
            origin.repository_location_origin,
            "origin",
            ManagedGrpcPythonEnvRepositoryLocationOrigin,
        )
        self._loadable_target_origin = origin.repository_location_origin.loadable_target_origin

    def resolve_executable_path(self, _graphene_info):
        return self._loadable_target_origin.executable_path

    def resolve_repository_metadata(self, graphene_info):
        metadata = {
            "python_file": self._loadable_target_origin.python_file,
            "module_name": self._loadable_target_origin.module_name,
            "working_directory": self._loadable_target_origin.working_directory,
            "attribute": self._loadable_target_origin.attribute,
            "package_name": self._loadable_target_origin.package_name,
        }
        return [
            graphene_info.schema.type_named("RepositoryMetadata")(key=key, value=value)
            for key, value in metadata.items()
            if value is not None
        ]


class DauphinRepositoryMetadata(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryMetadata"

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinGrpcRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = "GrpcRepositoryOrigin"

    grpc_url = dauphin.NonNull(dauphin.String)

    def __init__(self, origin):
        self._origin = check.inst_param(
            origin.repository_location_origin, "origin", GrpcServerRepositoryLocationOrigin
        )

    def resolve_grpc_url(self, _graphene_info):
        return "grpc:{host}:{socket_or_port}".format(
            host=self._origin.host,
            socket_or_port=(self._origin.socket if self._origin.socket else self._origin.port),
        )


class DauphinRepositoryOrigin(dauphin.Union):
    class Meta(object):
        name = "RepositoryOrigin"
        types = ("PythonRepositoryOrigin", "GrpcRepositoryOrigin")


class DauphinRepositoryLocationOrLoadFailure(dauphin.Union):
    class Meta(object):
        name = "RepositoryLocationOrLoadFailure"
        types = ("RepositoryLocation", "RepositoryLocationLoadFailure")


class DauphinRepositoryLocation(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocation"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    is_reload_supported = dauphin.NonNull(dauphin.Boolean)
    environment_path = dauphin.String()
    repositories = dauphin.non_null_list("Repository")

    def __init__(self, location):
        self._location = check.inst_param(location, "location", RepositoryLocation)
        environment_path = (
            location.location_handle.executable_path
            if isinstance(location.location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)
            else None
        )

        check.invariant(location.name is not None)

        super(DauphinRepositoryLocation, self).__init__(
            name=location.name,
            environment_path=environment_path,
            is_reload_supported=location.is_reload_supported,
        )

    def resolve_id(self, _):
        return self.name

    def resolve_repositories(self, graphene_info):
        return [
            graphene_info.schema.type_named("Repository")(repository, self._location)
            for repository in self._location.get_repositories().values()
        ]


class DauphinRepositoryLocationLoadFailure(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocationLoadFailure"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    error = dauphin.NonNull("PythonError")

    def __init__(self, name, error):
        check.str_param(name, "name")
        check.inst_param(error, "error", SerializableErrorInfo)
        super(DauphinRepositoryLocationLoadFailure, self).__init__(
            name=name, error=DauphinPythonError(error)
        )

    def resolve_id(self, _):
        return self.name


class DauphinRepositoryConnection(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryConnection"

    nodes = dauphin.non_null_list("Repository")


class DauphinRepositoryLocationConnection(dauphin.ObjectType):
    class Meta(object):
        name = "RepositoryLocationConnection"

    nodes = dauphin.non_null_list("RepositoryLocationOrLoadFailure")
