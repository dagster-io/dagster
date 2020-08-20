from __future__ import absolute_import

from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids

from dagster import check
from dagster.core.code_pointer import (
    CodePointer,
    FileCodePointer,
    ModuleCodePointer,
    PackageCodePointer,
)
from dagster.core.host_representation import (
    ExternalRepository,
    PythonEnvRepositoryLocationHandle,
    RepositoryLocation,
)
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryPythonOrigin


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
    partitionSets = dauphin.non_null_list('PartitionSet')

    def resolve_id(self, _graphene_info):
        return self._repository.get_origin_id()

    def resolve_origin(self, graphene_info):
        origin = self._repository.get_origin()
        if isinstance(origin, RepositoryGrpcServerOrigin):
            return graphene_info.schema.type_named('GrpcRepositoryOrigin')(origin)
        else:
            return graphene_info.schema.type_named('PythonRepositoryOrigin')(origin)

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

    def resolve_partitionSets(self, graphene_info):
        return (
            graphene_info.schema.type_named('PartitionSet')(self._repository.handle, partition_set)
            for partition_set in self._repository.get_external_partition_sets()
        )


class DauphinPythonRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = 'PythonRepositoryOrigin'

    executable_path = dauphin.NonNull(dauphin.String)
    code_pointer = dauphin.NonNull('CodePointer')

    def __init__(self, origin):
        self._origin = check.inst_param(origin, 'origin', RepositoryPythonOrigin)

    def resolve_executable_path(self, _graphene_info):
        return self._origin.executable_path

    def resolve_code_pointer(self, graphene_info):
        return graphene_info.schema.type_named('CodePointer')(self._origin.code_pointer)


class DauphinGrpcRepositoryOrigin(dauphin.ObjectType):
    class Meta(object):
        name = 'GrpcRepositoryOrigin'

    grpc_url = dauphin.NonNull(dauphin.String)

    def __init__(self, origin):
        self._origin = check.inst_param(origin, 'origin', RepositoryGrpcServerOrigin)

    def resolve_grpc_url(self, _graphene_info):
        return 'grpc:{host}:{socket_or_port}'.format(
            host=self._origin.host,
            socket_or_port=(self._origin.socket if self._origin.socket else self._origin.port),
        )


class DauphinRepositoryOrigin(dauphin.Union):
    class Meta(object):
        name = 'RepositoryOrigin'
        types = ('PythonRepositoryOrigin', 'GrpcRepositoryOrigin')


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


class DauphinCodePointer(dauphin.ObjectType):
    class Meta(object):
        name = 'CodePointer'

    description = dauphin.NonNull(dauphin.String)
    metadata = dauphin.non_null_list('CodePointerMetadata')

    def __init__(self, code_pointer):
        self._code_pointer = check.inst_param(code_pointer, 'code_pointer', CodePointer)

    def resolve_description(self, _graphene_info):
        return self._code_pointer.describe()

    def resolve_metadata(self, graphene_info):
        metadata = {}
        if isinstance(self._code_pointer, FileCodePointer):
            metadata['python_file'] = self._code_pointer.python_file
            metadata['attribute'] = self._code_pointer.fn_name
        if isinstance(self._code_pointer, ModuleCodePointer):
            metadata['python_module'] = self._code_pointer.module
            metadata['attribute'] = self._code_pointer.fn_name
        if isinstance(self._code_pointer, PackageCodePointer):
            metadata['python_package'] = self._code_pointer.module
            metadata['attribute'] = self._code_pointer.attribute

        return [
            graphene_info.schema.type_named('CodePointerMetadata')(key=key, value=value)
            for key, value in metadata.items()
        ]


class DauphinCodePointerMetadata(dauphin.ObjectType):
    class Meta(object):
        name = 'CodePointerMetadata'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinRepositoryConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'RepositoryConnection'

    nodes = dauphin.non_null_list('Repository')
