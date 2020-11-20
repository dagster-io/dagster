from dagster import check
from dagster.core.host_representation import ExternalSensor
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster_graphql import dauphin
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinSensorNotFoundError,
)


class DauphinSensor(dauphin.ObjectType):
    class Meta:
        name = "Sensor"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    pipelineName = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)

    status = dauphin.NonNull("JobStatus")
    runs = dauphin.Field(dauphin.non_null_list("PipelineRun"), limit=dauphin.Int())
    runsCount = dauphin.NonNull(dauphin.Int)
    ticks = dauphin.Field(dauphin.non_null_list("JobTick"), limit=dauphin.Int())

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
            pipelineName=external_sensor.pipeline_name,
            solidSelection=external_sensor.solid_selection,
            mode=external_sensor.mode,
        )

    def resolve_status(self, _graphene_info):
        return self._sensor_state.status

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named("PipelineRun")(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter.for_sensor(self._external_sensor),
                limit=kwargs.get("limit"),
            )
        ]

    def resolve_runsCount(self, graphene_info):
        return graphene_info.context.instance.get_runs_count(
            filters=PipelineRunsFilter.for_sensor(self._external_sensor)
        )

    def resolve_ticks(self, graphene_info, limit=None):
        ticks = graphene_info.context.instance.get_job_ticks(
            self._external_sensor.get_external_origin_id()
        )

        if limit:
            ticks = ticks[:limit]

        return [graphene_info.schema.type_named("JobTick")(graphene_info, tick) for tick in ticks]


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
