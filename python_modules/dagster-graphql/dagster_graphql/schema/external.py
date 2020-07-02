from __future__ import absolute_import

from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids

from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    PythonEnvRepositoryLocationHandle,
    RepositoryLocation,
)
from dagster.core.origin import RepositoryPythonOrigin


class DauphinRepository(dauphin.ObjectType):
    class Meta(object):
        name = 'Repository'

    def __init__(self, repository, repository_location):
        self._repository = check.inst_param(repository, 'repository', ExternalRepository)
        self._repository_location = check.inst_param(
            repository_location, 'repository_location', RepositoryLocation
        )
        super(DauphinRepository, self).__init__(name=repository.name)

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    location = dauphin.NonNull('RepositoryLocation')
    pipelines = dauphin.non_null_list('Pipeline')
    usedSolids = dauphin.Field(dauphin.non_null_list('UsedSolid'))
    usedSolid = dauphin.Field('UsedSolid', name=dauphin.NonNull(dauphin.String))
    origin = dauphin.NonNull('RepositoryOrigin')

    def resolve_id(self, _graphene_info):
        return self._repository.get_origin_id()

    def resolve_origin(self, graphene_info):
        return graphene_info.schema.type_named('RepositoryOrigin')(self._repository.get_origin())

    def resolve_location(self, graphene_info):
        return graphene_info.schema.type_named('RepositoryLocation')(self._repository_location)

    def resolve_pipelines(self, graphene_info):
        return sorted(
            [
                graphene_info.schema.type_named('Pipeline')(pipeline)
                for pipeline in self._repository.get_all_external_pipelines()
            ],
            key=lambda pipeline: pipeline.name,
        )

    def resolve_usedSolid(self, _graphene_info, name):
        return get_solid(self._repository, name)

    def resolve_usedSolids(self, _graphene_info):
        return get_solids(self._repository)


class DauphinRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = 'RepositoryOrigin'

    executable_path = dauphin.NonNull(dauphin.String)
    code_pointer_description = dauphin.NonNull(dauphin.String)

    def __init__(self, origin):
        self._origin = check.inst_param(origin, 'origin', RepositoryPythonOrigin)

    def resolve_executable_path(self, _graphene_info):
        return self._origin.executable_path

    def resolve_code_pointer_description(self, _graphene_info):
        return self._origin.code_pointer.describe()


class DauphinRepositoryLocation(dauphin.ObjectType):
    class Meta(object):
        name = 'RepositoryLocation'

    name = dauphin.NonNull(dauphin.String)
    is_reload_supported = dauphin.NonNull(dauphin.Boolean)
    environment_path = dauphin.String()
    repositories = dauphin.non_null_list('Repository')

    def __init__(self, location):
        self._location = check.inst_param(location, 'location', RepositoryLocation)
        environment_path = (
            location.location_handle.executable_path
            if isinstance(location.location_handle, PythonEnvRepositoryLocationHandle)
            else None
        )

        check.invariant(location.name is not None)

        super(DauphinRepositoryLocation, self).__init__(
            name=location.name,
            environment_path=environment_path,
            is_reload_supported=location.is_reload_supported,
        )

    def resolve_repositories(self, graphene_info):
        return [
            graphene_info.schema.type_named('Repository')(repository, self._location)
            for repository in self._location.get_repositories().values()
        ]


class DauphinRepositoryConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'RepositoryConnection'

    nodes = dauphin.non_null_list('Repository')
