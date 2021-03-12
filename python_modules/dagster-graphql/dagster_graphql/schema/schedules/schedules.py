import graphene
from dagster import check
from dagster.core.host_representation import ExternalSchedule
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime

from ..errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
)
from ..jobs import GrapheneFutureJobTick, GrapheneFutureJobTicks, GrapheneJobState
from ..util import non_null_list


class GrapheneSchedule(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    cron_schedule = graphene.NonNull(graphene.String)
    pipeline_name = graphene.NonNull(graphene.String)
    solid_selection = graphene.List(graphene.String)
    mode = graphene.NonNull(graphene.String)
    execution_timezone = graphene.Field(graphene.String)
    description = graphene.String()
    scheduleState = graphene.NonNull(GrapheneJobState)
    partition_set = graphene.Field("dagster_graphql.schema.partition_sets.GraphenePartitionSet")
    futureTicks = graphene.NonNull(
        GrapheneFutureJobTicks, cursor=graphene.Float(), limit=graphene.Int()
    )
    futureTick = graphene.NonNull(
        GrapheneFutureJobTick, tick_timestamp=graphene.NonNull(graphene.Int)
    )

    class Meta:
        name = "Schedule"

    def __init__(self, graphene_info, external_schedule):
        self._external_schedule = check.inst_param(
            external_schedule, "external_schedule", ExternalSchedule
        )
        self._schedule_state = graphene_info.context.instance.get_job_state(
            self._external_schedule.get_external_origin_id()
        )

        if not self._schedule_state:
            # Also include a ScheduleState for a stopped schedule that may not
            # have a stored database row yet
            self._schedule_state = self._external_schedule.get_default_job_state(
                graphene_info.context.instance
            )

        super().__init__(
            name=external_schedule.name,
            cron_schedule=external_schedule.cron_schedule,
            pipeline_name=external_schedule.pipeline_name,
            solid_selection=external_schedule.solid_selection,
            mode=external_schedule.mode,
            scheduleState=GrapheneJobState(self._schedule_state),
            execution_timezone=(
                self._external_schedule.execution_timezone
                if self._external_schedule.execution_timezone
                else "UTC"
            ),
            description=external_schedule.description,
        )

    def resolve_id(self, _):
        return "%s:%s" % (self.name, self.pipeline_name)

    def resolve_partition_set(self, graphene_info):
        from ..partition_sets import GraphenePartitionSet

        if self._external_schedule.partition_set_name is None:
            return None

        repository = graphene_info.context.get_repository_location(
            self._external_schedule.handle.location_name
        ).get_repository(self._external_schedule.handle.repository_name)
        external_partition_set = repository.get_external_partition_set(
            self._external_schedule.partition_set_name
        )

        return GraphenePartitionSet(
            external_repository_handle=repository.handle,
            external_partition_set=external_partition_set,
        )

    def resolve_futureTicks(self, _graphene_info, **kwargs):
        cursor = kwargs.get(
            "cursor", get_timestamp_from_utc_datetime(get_current_datetime_in_utc())
        )
        limit = kwargs.get("limit", 10)

        tick_times = []
        time_iter = self._external_schedule.execution_time_iterator(cursor)

        for _ in range(limit):
            tick_times.append(next(time_iter).timestamp())

        future_ticks = [
            GrapheneFutureJobTick(self._schedule_state, tick_time) for tick_time in tick_times
        ]

        return GrapheneFutureJobTicks(results=future_ticks, cursor=tick_times[-1] + 1)

    def resolve_futureTick(self, _graphene_info, tick_timestamp):
        return GrapheneFutureJobTick(self._schedule_state, float(tick_timestamp))


class GrapheneScheduleOrError(graphene.Union):
    class Meta:
        types = (GrapheneSchedule, GrapheneScheduleNotFoundError, GraphenePythonError)
        name = "ScheduleOrError"


class GrapheneSchedules(graphene.ObjectType):
    results = non_null_list(GrapheneSchedule)

    class Meta:
        name = "Schedules"


class GrapheneSchedulesOrError(graphene.Union):
    class Meta:
        types = (GrapheneSchedules, GrapheneRepositoryNotFoundError, GraphenePythonError)
        name = "SchedulesOrError"
