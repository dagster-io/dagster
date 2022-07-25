import graphene
from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.implementation.utils import capture_error, check_permission

import dagster._check as check
from dagster._core.host_representation import ExternalSensor, ExternalTargetData, SensorSelector
from dagster._core.scheduler.instigation import InstigatorState
from dagster._core.workspace.permissions import Permissions

from ..implementation.fetch_sensors import (
    get_sensor_next_tick,
    set_sensor_cursor,
    start_sensor,
    stop_sensor,
)
from .asset_key import GrapheneAssetKey
from .errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneSensorNotFoundError,
    GrapheneUnauthorizedError,
)
from .inputs import GrapheneSensorSelector
from .instigation import GrapheneFutureInstigationTick, GrapheneInstigationState
from .util import non_null_list


class GrapheneTarget(graphene.ObjectType):
    pipelineName = graphene.NonNull(graphene.String)
    mode = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))

    class Meta:
        name = "Target"

    def __init__(self, external_target):
        self._external_target = check.inst_param(
            external_target, "external_target", ExternalTargetData
        )
        super().__init__(
            pipelineName=external_target.pipeline_name,
            mode=external_target.mode,
            solidSelection=external_target.solid_selection,
        )


class GrapheneSensorMetadata(graphene.ObjectType):
    assetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "SensorMetadata"


class GrapheneSensor(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    jobOriginId = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    targets = graphene.List(graphene.NonNull(GrapheneTarget))
    sensorState = graphene.NonNull(GrapheneInstigationState)
    minIntervalSeconds = graphene.NonNull(graphene.Int)
    description = graphene.String()
    nextTick = graphene.Field(GrapheneFutureInstigationTick)
    metadata = graphene.NonNull(GrapheneSensorMetadata)

    class Meta:
        name = "Sensor"

    def __init__(self, external_sensor, sensor_state, batch_loader=None):
        self._external_sensor = check.inst_param(external_sensor, "external_sensor", ExternalSensor)

        # optional run loader, provided by a parent GrapheneRepository object that instantiates
        # multiple sensors
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )
        self._sensor_state = self._external_sensor.get_current_instigator_state(sensor_state)

        super().__init__(
            name=external_sensor.name,
            jobOriginId=external_sensor.get_external_origin_id(),
            minIntervalSeconds=external_sensor.min_interval_seconds,
            description=external_sensor.description,
            targets=[GrapheneTarget(target) for target in external_sensor.get_external_targets()],
            metadata=GrapheneSensorMetadata(
                assetKeys=external_sensor.metadata.asset_keys if external_sensor.metadata else None
            ),
        )

    def resolve_id(self, _):
        return self._external_sensor.get_external_origin_id()

    def resolve_sensorState(self, _graphene_info):
        # forward the batch run loader to the instigation state, which provides the sensor runs
        return GrapheneInstigationState(self._sensor_state, self._batch_loader)

    def resolve_nextTick(self, graphene_info):
        return get_sensor_next_tick(graphene_info, self._sensor_state)


class GrapheneSensorOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneSensor,
            GrapheneSensorNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "SensorOrError"


class GrapheneSensors(graphene.ObjectType):
    results = non_null_list(GrapheneSensor)

    class Meta:
        name = "Sensors"


class GrapheneSensorsOrError(graphene.Union):
    class Meta:
        types = (GrapheneSensors, GrapheneRepositoryNotFoundError, GraphenePythonError)
        name = "SensorsOrError"


class GrapheneStartSensorMutation(graphene.Mutation):
    """Enable a sensor to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)

    class Meta:
        name = "StartSensorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info, sensor_selector):
        return start_sensor(graphene_info, SensorSelector.from_graphql_input(sensor_selector))


class GrapheneStopSensorMutationResult(graphene.ObjectType):
    instigationState = graphene.Field(GrapheneInstigationState)

    class Meta:
        name = "StopSensorMutationResult"

    def __init__(self, instigator_state):
        super().__init__()
        self._instigator_state = check.inst_param(
            instigator_state, "instigator_state", InstigatorState
        )

    def resolve_instigationState(self, _graphene_info):
        return GrapheneInstigationState(instigator_state=self._instigator_state)


class GrapheneStopSensorMutationResultOrError(graphene.Union):
    class Meta:
        types = (GrapheneStopSensorMutationResult, GrapheneUnauthorizedError, GraphenePythonError)
        name = "StopSensorMutationResultOrError"


class GrapheneStopSensorMutation(graphene.Mutation):
    """Disable a sensor from launching runs for a job."""

    Output = graphene.NonNull(GrapheneStopSensorMutationResultOrError)

    class Arguments:
        job_origin_id = graphene.NonNull(graphene.String)
        job_selector_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "StopSensorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info, job_origin_id, job_selector_id):
        return stop_sensor(graphene_info, job_origin_id, job_selector_id)


class GrapheneSetSensorCursorMutation(graphene.Mutation):
    """Set a cursor for a sensor to track state across evaluations."""

    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)
        cursor = graphene.String()

    class Meta:
        name = "SetSensorCursorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info, sensor_selector, cursor=None):
        return set_sensor_cursor(
            graphene_info, SensorSelector.from_graphql_input(sensor_selector), cursor
        )


types = [
    GrapheneSensor,
    GrapheneSensorOrError,
    GrapheneSensors,
    GrapheneSensorsOrError,
    GrapheneStopSensorMutation,
    GrapheneStopSensorMutationResult,
    GrapheneStopSensorMutationResultOrError,
    GrapheneStopSensorMutation,
    GrapheneSetSensorCursorMutation,
]
