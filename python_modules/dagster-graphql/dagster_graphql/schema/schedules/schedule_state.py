from dagster import check
from dagster.core.origin import RepositoryGrpcServerOrigin
from dagster.core.scheduler import ScheduleState
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster_graphql import dauphin
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinScheduleStateNotFoundError,
)

from .ticks import tick_specific_data_from_dagster_tick


class DapuphinScheduleStateOrError(dauphin.Union):
    class Meta(object):
        name = "ScheduleStateOrError"
        types = ("ScheduleState", DauphinScheduleStateNotFoundError, DauphinPythonError)


class DauphinScheduleStates(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleStates"

    results = dauphin.non_null_list("ScheduleState")


class DauphinScheduleStatesOrError(dauphin.Union):
    class Meta(object):
        name = "ScheduleStatesOrError"
        types = (DauphinScheduleStates, DauphinRepositoryNotFoundError, DauphinPythonError)


class DauphinScheduleState(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleState"

    schedule_origin_id = dauphin.NonNull(dauphin.String)
    schedule_name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull("ScheduleStatus")

    runs = dauphin.Field(dauphin.non_null_list("PipelineRun"), limit=dauphin.Int())
    runs_count = dauphin.NonNull(dauphin.Int)
    ticks = dauphin.Field(dauphin.non_null_list("ScheduleTick"), limit=dauphin.Int())
    ticks_count = dauphin.NonNull(dauphin.Int)
    stats = dauphin.NonNull("ScheduleTickStatsSnapshot")
    logs_path = dauphin.NonNull(dauphin.String)
    running_schedule_count = dauphin.NonNull(dauphin.Int)
    repository_origin = dauphin.NonNull("RepositoryOrigin")
    repository_origin_id = dauphin.NonNull(dauphin.String)
    id = dauphin.NonNull(dauphin.ID)

    def __init__(self, _graphene_info, schedule_state):
        self._schedule_state = check.inst_param(schedule_state, "schedule", ScheduleState)
        self._external_schedule_origin_id = self._schedule_state.schedule_origin_id

        super(DauphinScheduleState, self).__init__(
            schedule_origin_id=schedule_state.schedule_origin_id,
            schedule_name=schedule_state.name,
            cron_schedule=schedule_state.cron_schedule,
            status=schedule_state.status,
        )

    def resolve_id(self, _graphene_info):
        return self._external_schedule_origin_id

    def resolve_running_schedule_count(self, graphene_info):
        running_schedule_count = graphene_info.context.instance.running_schedule_count(
            self._external_schedule_origin_id
        )
        return running_schedule_count

    def resolve_stats(self, graphene_info):
        stats = graphene_info.context.instance.get_schedule_tick_stats(
            self._external_schedule_origin_id
        )
        return graphene_info.schema.type_named("ScheduleTickStatsSnapshot")(stats)

    def resolve_ticks(self, graphene_info, limit=None):

        # TODO: Add cursor limit argument to get_schedule_ticks_by_schedule
        # https://github.com/dagster-io/dagster/issues/2291
        ticks = graphene_info.context.instance.get_schedule_ticks(self._external_schedule_origin_id)

        if not limit:
            tick_subset = ticks
        else:
            tick_subset = ticks[:limit]

        return [
            graphene_info.schema.type_named("ScheduleTick")(
                tick_id=tick.tick_id,
                status=tick.status,
                timestamp=tick.timestamp,
                tick_specific_data=tick_specific_data_from_dagster_tick(graphene_info, tick),
            )
            for tick in tick_subset
        ]

    def resolve_ticks_count(self, graphene_info):
        ticks = graphene_info.context.instance.get_schedule_ticks(self._external_schedule_origin_id)
        return len(ticks)

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named("PipelineRun")(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(self._schedule_state),
                limit=kwargs.get("limit"),
            )
        ]

    def resolve_runs_count(self, graphene_info):
        return graphene_info.context.instance.get_runs_count(
            filters=PipelineRunsFilter.for_schedule(self._schedule_state)
        )

    def resolve_repository_origin_id(self, _graphene_info):
        return self._schedule_state.repository_origin_id

    def resolve_repository_origin(self, graphene_info):
        origin = self._schedule_state.origin.get_repo_origin()
        if isinstance(origin, RepositoryGrpcServerOrigin):
            return graphene_info.schema.type_named("GrpcRepositoryOrigin")(origin)
        else:
            return graphene_info.schema.type_named("PythonRepositoryOrigin")(origin)
