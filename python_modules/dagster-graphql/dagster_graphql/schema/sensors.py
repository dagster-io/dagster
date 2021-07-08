import graphene
from dagster import check
from dagster.core.host_representation import ExternalSensor, SensorSelector
from dagster.core.scheduler.job import JobState
from dagster_graphql.implementation.utils import capture_error, check_permission

from ..implementation.fetch_sensors import get_sensor_next_tick, start_sensor, stop_sensor
from .errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneSensorNotFoundError,
    GrapheneUnauthorizedError,
)
from .inputs import GrapheneSensorSelector
from .instigation import GrapheneFutureInstigationTick, GrapheneInstigationState
from .util import non_null_list


class GrapheneSensor(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    jobOriginId = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    pipelineName = graphene.String()
    solidSelection = graphene.List(graphene.String)
    mode = graphene.String()
    sensorState = graphene.NonNull(GrapheneInstigationState)
    minIntervalSeconds = graphene.NonNull(graphene.Int)
    description = graphene.String()
    nextTick = graphene.Field(GrapheneFutureInstigationTick)

    class Meta:
        name = "Sensor"

    def __init__(self, graphene_info, external_sensor):
        self._external_sensor = check.inst_param(external_sensor, "external_sensor", ExternalSensor)
        self._sensor_state = graphene_info.context.instance.get_job_state(
            self._external_sensor.get_external_origin_id()
        )

        if not self._sensor_state:
            # Also include a SensorState for a stopped sensor that may not
            # have a stored database row yet
            self._sensor_state = self._external_sensor.get_default_job_state(
                graphene_info.context.instance
            )

        super().__init__(
            name=external_sensor.name,
            jobOriginId=external_sensor.get_external_origin_id(),
            pipelineName=external_sensor.pipeline_name,
            solidSelection=external_sensor.solid_selection,
            mode=external_sensor.mode,
            minIntervalSeconds=external_sensor.min_interval_seconds,
            description=external_sensor.description,
        )

    def resolve_id(self, _):
        return self._external_sensor.get_external_origin_id()

    def resolve_sensorState(self, _graphene_info):
        return GrapheneInstigationState(self._sensor_state)

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
    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)

    class Meta:
        name = "StartSensorMutation"

    @capture_error
    @check_permission("start_sensor")
    def mutate(self, graphene_info, sensor_selector):
        return start_sensor(graphene_info, SensorSelector.from_graphql_input(sensor_selector))


class GrapheneStopSensorMutationResult(graphene.ObjectType):
    instigationState = graphene.Field(GrapheneInstigationState)

    class Meta:
        name = "StopSensorMutationResult"

    def __init__(self, job_state):
        super().__init__()
        self._job_state = check.inst_param(job_state, "job_state", JobState)

    def resolve_instigationState(self, _graphene_info):
        if not self._job_state:
            return None

        return GrapheneInstigationState(job_state=self._job_state)


class GrapheneStopSensorMutationResultOrError(graphene.Union):
    class Meta:
        types = (GrapheneStopSensorMutationResult, GrapheneUnauthorizedError, GraphenePythonError)
        name = "StopSensorMutationResultOrError"


class GrapheneStopSensorMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneStopSensorMutationResultOrError)

    class Arguments:
        job_origin_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "StopSensorMutation"

    @capture_error
    @check_permission("stop_sensor")
    def mutate(self, graphene_info, job_origin_id):
        return stop_sensor(graphene_info, job_origin_id)


types = [
    GrapheneSensor,
    GrapheneSensorOrError,
    GrapheneSensors,
    GrapheneSensorsOrError,
    GrapheneStopSensorMutation,
    GrapheneStopSensorMutationResult,
    GrapheneStopSensorMutationResultOrError,
    GrapheneStopSensorMutation,
]
