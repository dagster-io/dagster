import graphene
from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    GrpcServerRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
    RepositoryLocation,
)
from dagster.utils.error import SerializableErrorInfo
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids

from .errors import GraphenePythonError, GrapheneRepositoryNotFoundError
from .partition_sets import GraphenePartitionSet
from .pipelines.pipeline import GraphenePipeline
from .repository_origin import GrapheneRepositoryOrigin
from .schedules import GrapheneSchedule
from .sensors import GrapheneSensor
from .used_solid import GrapheneUsedSolid
from .util import non_null_list


class GrapheneLocationStateChangeEventType(graphene.Enum):
    LOCATION_UPDATED = "LOCATION_UPDATED"
    LOCATION_DISCONNECTED = "LOCATION_DISCONNECTED"
    LOCATION_RECONNECTED = "LOCATION_RECONNECTED"
    LOCATION_ERROR = "LOCATION_ERROR"

    class Meta:
        name = "LocationStateChangeEventType"


class GrapheneRepositoryLocation(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    is_reload_supported = graphene.NonNull(graphene.Boolean)
    environment_path = graphene.String()
    repositories = non_null_list(lambda: GrapheneRepository)
    server_id = graphene.String()

    class Meta:
        name = "RepositoryLocation"

    def __init__(self, location):
        self._location = check.inst_param(location, "location", RepositoryLocation)
        environment_path = (
            location.location_handle.executable_path
            if isinstance(location.location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle)
            else None
        )

        server_id = (
            location.location_handle.server_id
            if isinstance(location.location_handle, GrpcServerRepositoryLocationHandle)
            else None
        )

        check.invariant(location.name is not None)

        super().__init__(
            name=location.name,
            environment_path=environment_path,
            is_reload_supported=location.is_reload_supported,
            server_id=server_id,
        )

    def resolve_id(self, _):
        return self.name

    def resolve_repositories(self, _graphene_info):
        return [
            GrapheneRepository(repository, self._location)
            for repository in self._location.get_repositories().values()
        ]


class GrapheneRepository(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    location = graphene.NonNull(GrapheneRepositoryLocation)
    pipelines = non_null_list(GraphenePipeline)
    usedSolids = graphene.Field(non_null_list(GrapheneUsedSolid))
    usedSolid = graphene.Field(GrapheneUsedSolid, name=graphene.NonNull(graphene.String))
    origin = graphene.NonNull(GrapheneRepositoryOrigin)
    partitionSets = non_null_list(GraphenePartitionSet)
    schedules = non_null_list(GrapheneSchedule)
    sensors = non_null_list(GrapheneSensor)

    class Meta:
        name = "Repository"

    def __init__(self, repository, repository_location):
        self._repository = check.inst_param(repository, "repository", ExternalRepository)
        self._repository_location = check.inst_param(
            repository_location, "repository_location", RepositoryLocation
        )
        super().__init__(name=repository.name)

    def resolve_id(self, _graphene_info):
        return self._repository.get_external_origin_id()

    def resolve_origin(self, _graphene_info):
        origin = self._repository.get_external_origin()
        return GrapheneRepositoryOrigin(origin)

    def resolve_location(self, _graphene_info):
        return GrapheneRepositoryLocation(self._repository_location)

    def resolve_schedules(self, graphene_info):

        schedules = self._repository.get_external_schedules()

        return sorted(
            [GrapheneSchedule(graphene_info, schedule) for schedule in schedules],
            key=lambda schedule: schedule.name,
        )

    def resolve_sensors(self, graphene_info):
        sensors = self._repository.get_external_sensors()
        return sorted(
            [GrapheneSensor(graphene_info, sensor) for sensor in sensors],
            key=lambda sensor: sensor.name,
        )

    def resolve_pipelines(self, _graphene_info):
        return [
            GraphenePipeline(pipeline)
            for pipeline in sorted(
                self._repository.get_all_external_pipelines(), key=lambda pipeline: pipeline.name
            )
        ]

    def resolve_usedSolid(self, _graphene_info, name):
        return get_solid(self._repository, name)

    def resolve_usedSolids(self, _graphene_info):
        return get_solids(self._repository)

    def resolve_partitionSets(self, _graphene_info):
        return (
            GraphenePartitionSet(self._repository.handle, partition_set)
            for partition_set in self._repository.get_external_partition_sets()
        )


class GrapheneRepositoryLocationLoadFailure(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    error = graphene.NonNull(GraphenePythonError)

    class Meta:
        name = "RepositoryLocationLoadFailure"

    def __init__(self, name, error):
        check.str_param(name, "name")
        check.inst_param(error, "error", SerializableErrorInfo)
        super().__init__(name=name, error=GraphenePythonError(error))

    def resolve_id(self, _):
        return self.name


class GrapheneRepositoryLocationOrLoadFailure(graphene.Union):
    class Meta:
        types = (GrapheneRepositoryLocation, GrapheneRepositoryLocationLoadFailure)
        name = "RepositoryLocationOrLoadFailure"


class GrapheneRepositoryConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneRepository)

    class Meta:
        name = "RepositoryConnection"


class GrapheneRepositoryLocationConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneRepositoryLocationOrLoadFailure)

    class Meta:
        name = "RepositoryLocationConnection"


class GrapheneLocationStateChangeEvent(graphene.ObjectType):
    event_type = graphene.NonNull(GrapheneLocationStateChangeEventType)
    message = graphene.NonNull(graphene.String)
    location_name = graphene.NonNull(graphene.String)
    server_id = graphene.Field(graphene.String)

    class Meta:
        name = "LocationStateChangeEvent"


class GrapheneLocationStateChangeSubscription(graphene.ObjectType):
    event = graphene.Field(graphene.NonNull(GrapheneLocationStateChangeEvent))

    class Meta:
        name = "LocationStateChangeSubscription"


def get_location_state_change_observable(graphene_info):

    # This observerable lives on the process context and is never modified/destroyed, so we can
    # access it directly
    context = graphene_info.context.process_context

    return context.location_state_events.map(
        lambda event: GrapheneLocationStateChangeSubscription(
            event=GrapheneLocationStateChangeEvent(
                event_type=event.event_type,
                location_name=event.location_name,
                message=event.message,
                server_id=event.server_id,
            ),
        )
    )


class GrapheneRepositoriesOrError(graphene.Union):
    class Meta:
        types = (GrapheneRepositoryConnection, GraphenePythonError)
        name = "RepositoriesOrError"


class GrapheneRepositoryLocationsOrError(graphene.Union):
    class Meta:
        types = (GrapheneRepositoryLocationConnection, GraphenePythonError)
        name = "RepositoryLocationsOrError"


class GrapheneRepositoryOrError(graphene.Union):
    class Meta:
        types = (GraphenePythonError, GrapheneRepository, GrapheneRepositoryNotFoundError)
        name = "RepositoryOrError"


types = [
    GrapheneLocationStateChangeEvent,
    GrapheneLocationStateChangeEventType,
    GrapheneLocationStateChangeSubscription,
    GrapheneRepositoriesOrError,
    GrapheneRepository,
    GrapheneRepositoryConnection,
    GrapheneRepositoryLocation,
    GrapheneRepositoryLocationConnection,
    GrapheneRepositoryLocationLoadFailure,
    GrapheneRepositoryLocationOrLoadFailure,
    GrapheneRepositoryLocationsOrError,
    GrapheneRepositoryOrError,
]
