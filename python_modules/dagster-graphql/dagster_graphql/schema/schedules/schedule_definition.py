from dagster import check
from dagster.core.host_representation import ExternalSchedule
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import get_schedule_config
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinScheduleDefinitionNotFoundError,
)


class DapuphinScheduleDefinitionOrError(dauphin.Union):
    class Meta(object):
        name = "ScheduleDefinitionOrError"
        types = ("ScheduleDefinition", DauphinScheduleDefinitionNotFoundError, DauphinPythonError)


class DauphinScheduleDefinitions(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleDefinitions"

    results = dauphin.non_null_list("ScheduleDefinition")


class DauphinScheduleDefintionsOrError(dauphin.Union):
    class Meta(object):
        name = "ScheduleDefinitionsOrError"
        types = (DauphinScheduleDefinitions, DauphinRepositoryNotFoundError, DauphinPythonError)


class DauphinScheduleDefinition(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleDefinition"

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    pipeline_name = dauphin.NonNull(dauphin.String)
    solid_selection = dauphin.List(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    execution_timezone = dauphin.Field(dauphin.String)
    schedule_state = dauphin.Field("ScheduleState")

    runConfigOrError = dauphin.Field("ScheduleRunConfigOrError")
    partition_set = dauphin.Field("PartitionSet")

    def resolve_runConfigOrError(self, graphene_info):
        return get_schedule_config(graphene_info, self._external_schedule)

    def resolve_partition_set(self, graphene_info):
        if self._external_schedule.partition_set_name is None:
            return None

        repository = graphene_info.context.get_repository_location(
            self._external_schedule.handle.location_name
        ).get_repository(self._external_schedule.handle.repository_name)
        external_partition_set = repository.get_external_partition_set(
            self._external_schedule.partition_set_name
        )

        return graphene_info.schema.type_named("PartitionSet")(
            external_repository_handle=repository.handle,
            external_partition_set=external_partition_set,
        )

    def __init__(self, graphene_info, external_schedule):
        self._external_schedule = check.inst_param(
            external_schedule, "external_schedule", ExternalSchedule
        )
        self._schedule_state = graphene_info.context.instance.get_schedule_state(
            self._external_schedule.get_origin_id()
        )

        super(DauphinScheduleDefinition, self).__init__(
            name=external_schedule.name,
            cron_schedule=external_schedule.cron_schedule,
            pipeline_name=external_schedule.pipeline_name,
            solid_selection=external_schedule.solid_selection,
            mode=external_schedule.mode,
            schedule_state=graphene_info.schema.type_named("ScheduleState")(
                graphene_info, self._schedule_state
            )
            if self._schedule_state
            else None,
            execution_timezone=self._external_schedule.execution_timezone,
        )


class DauphinScheduleRunConfig(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleRunConfig"

    yaml = dauphin.NonNull(dauphin.String)


class DauphinScheduleRunConfigOrError(dauphin.Union):
    class Meta(object):
        name = "ScheduleRunConfigOrError"
        types = (DauphinScheduleRunConfig, DauphinPythonError)
