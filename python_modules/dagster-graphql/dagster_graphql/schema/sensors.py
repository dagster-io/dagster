from dagster import check
from dagster.core.host_representation import ExternalSensor, SensorSelector
from dagster.core.scheduler.job import JobState
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_sensors import (
    get_sensor_next_tick,
    start_sensor,
    stop_sensor,
)
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinSensorNotFoundError,
)


class DauphinSensor(dauphin.ObjectType):
    class Meta:
        name = "Sensor"

    id = dauphin.NonNull(dauphin.ID)
    jobOriginId = dauphin.NonNull(dauphin.String)
    name = dauphin.NonNull(dauphin.String)
    pipelineName = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    sensorState = dauphin.NonNull("JobState")
    nextTick = dauphin.Field("FutureJobTick")

    def resolve_id(self, _):
        return "%s:%s" % (self.name, self.pipelineName)

    def __init__(self, graphene_info, external_sensor):
        self._external_sensor = check.inst_param(external_sensor, "external_sensor", ExternalSensor)
        self._sensor_state = graphene_info.context.instance.get_job_state(
            self._external_sensor.get_external_origin_id()
        )

        if not self._sensor_state:
            # Also include a SensorState for a stopped sensor that may not
            # have a stored database row yet
            self._sensor_state = self._external_sensor.get_default_job_state()

        super(DauphinSensor, self).__init__(
            name=external_sensor.name,
            jobOriginId=external_sensor.get_external_origin_id(),
            pipelineName=external_sensor.pipeline_name,
            solidSelection=external_sensor.solid_selection,
            mode=external_sensor.mode,
        )

    def resolve_sensorState(self, graphene_info):
        return graphene_info.schema.type_named("JobState")(self._sensor_state)

    def resolve_nextTick(self, graphene_info):
        return get_sensor_next_tick(graphene_info, self._sensor_state)


class DauphinSensorOrError(dauphin.Union):
    class Meta:
        name = "SensorOrError"
        types = (
            "Sensor",
            DauphinSensorNotFoundError,
            DauphinPythonError,
        )


class DauphinSensors(dauphin.ObjectType):
    class Meta:
        name = "Sensors"

    results = dauphin.non_null_list("Sensor")


class DauphinSensorsOrError(dauphin.Union):
    class Meta:
        name = "SensorsOrError"
        types = (DauphinSensors, DauphinRepositoryNotFoundError, DauphinPythonError)


class DauphinStartSensorMutation(dauphin.Mutation):
    class Meta:
        name = "StartSensorMutation"

    class Arguments:
        sensor_selector = dauphin.NonNull("SensorSelector")

    Output = dauphin.NonNull("SensorOrError")

    def mutate(self, graphene_info, sensor_selector):
        return start_sensor(graphene_info, SensorSelector.from_graphql_input(sensor_selector))


class DauphinStopSensorMutation(dauphin.Mutation):
    class Meta:
        name = "StopSensorMutation"

    class Arguments:
        job_origin_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("StopSensorMutationResultOrError")

    def mutate(self, graphene_info, job_origin_id):
        return stop_sensor(graphene_info, job_origin_id)


class DauphinStopSensorMutationResult(dauphin.ObjectType):
    class Meta:
        name = "StopSensorMutationResult"

    jobState = dauphin.Field("JobState")

    def __init__(self, job_state):
        self._job_state = check.inst_param(job_state, "job_state", JobState)

    def resolve_jobState(self, graphene_info):
        if not self._job_state:
            return None

        return graphene_info.schema.type_named("JobState")(job_state=self._job_state)


class DauphinStopSensorMutationResultOrError(dauphin.Union):
    class Meta:
        name = "StopSensorMutationResultOrError"
        types = ("StopSensorMutationResult", "PythonError")
