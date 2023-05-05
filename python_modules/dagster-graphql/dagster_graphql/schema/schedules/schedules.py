from typing import List, Optional

import dagster._check as check
import graphene
from dagster._core.host_representation import ExternalSchedule
from dagster._core.scheduler.instigation import InstigatorState
from dagster._seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime

from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader

from ..errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
)
from ..instigation import (
    GrapheneDryRunInstigationTick,
    GrapheneDryRunInstigationTicks,
    GrapheneInstigationState,
)
from ..util import ResolveInfo, non_null_list


class GrapheneSchedule(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    cron_schedule = graphene.NonNull(graphene.String)
    pipeline_name = graphene.NonNull(graphene.String)
    solid_selection = graphene.List(graphene.String)
    mode = graphene.NonNull(graphene.String)
    execution_timezone = graphene.Field(graphene.String)
    description = graphene.String()
    scheduleState = graphene.NonNull(GrapheneInstigationState)
    partition_set = graphene.Field("dagster_graphql.schema.partition_sets.GraphenePartitionSet")
    futureTicks = graphene.NonNull(
        GrapheneDryRunInstigationTicks,
        cursor=graphene.Float(),
        limit=graphene.Int(),
        until=graphene.Float(),
    )
    futureTick = graphene.NonNull(
        GrapheneDryRunInstigationTick, tick_timestamp=graphene.NonNull(graphene.Int)
    )
    potentialTickTimestamps = graphene.NonNull(
        graphene.List(graphene.NonNull(graphene.Float)),
        start_timestamp=graphene.Float(),
        upper_limit=graphene.Int(),
        lower_limit=graphene.Int(),
    )

    class Meta:
        name = "Schedule"

    def __init__(
        self,
        external_schedule: ExternalSchedule,
        schedule_state: Optional[InstigatorState],
        batch_loader: Optional[RepositoryScopedBatchLoader] = None,
    ):
        self._external_schedule = check.inst_param(
            external_schedule, "external_schedule", ExternalSchedule
        )

        # optional run loader, provided by a parent graphene object (e.g. GrapheneRepository)
        # that instantiates multiple schedules
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )

        self._schedule_state = self._external_schedule.get_current_instigator_state(schedule_state)

        super().__init__(
            name=external_schedule.name,
            cron_schedule=str(
                external_schedule.cron_schedule
            ),  # can be sequence, coercing to str for now
            pipeline_name=external_schedule.job_name,
            solid_selection=external_schedule.solid_selection,
            mode=external_schedule.mode,
            execution_timezone=(
                self._external_schedule.execution_timezone
                if self._external_schedule.execution_timezone
                else "UTC"
            ),
            description=external_schedule.description,
        )

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self._external_schedule.get_external_origin_id()

    def resolve_scheduleState(self, _graphene_info: ResolveInfo):
        # forward the batch run loader to the instigation state, which provides the schedule runs
        return GrapheneInstigationState(self._schedule_state, self._batch_loader)

    def resolve_partition_set(self, graphene_info: ResolveInfo):
        from ..partition_sets import GraphenePartitionSet

        if self._external_schedule.partition_set_name is None:
            return None

        repository = graphene_info.context.get_code_location(
            self._external_schedule.handle.location_name
        ).get_repository(self._external_schedule.handle.repository_name)
        external_partition_set = repository.get_external_partition_set(
            self._external_schedule.partition_set_name
        )

        return GraphenePartitionSet(
            external_repository_handle=repository.handle,
            external_partition_set=external_partition_set,
        )

    def resolve_futureTicks(
        self,
        _graphene_info: ResolveInfo,
        cursor: Optional[float] = None,
        limit: Optional[int] = None,
        until: Optional[float] = None,
    ):
        cursor = cursor or get_timestamp_from_utc_datetime(get_current_datetime_in_utc())

        tick_times: List[float] = []
        time_iter = self._external_schedule.execution_time_iterator(cursor)

        if until:
            currentTime = None
            while (not currentTime or currentTime < until) and (
                limit is None or len(tick_times) < limit
            ):
                try:
                    currentTime = next(time_iter).timestamp()
                    if currentTime < until:
                        tick_times.append(currentTime)
                except StopIteration:
                    break
        else:
            limit = limit or 10
            for _ in range(limit):
                tick_times.append(next(time_iter).timestamp())

        schedule_selector = self._external_schedule.schedule_selector
        future_ticks = [
            GrapheneDryRunInstigationTick(schedule_selector, tick_time) for tick_time in tick_times
        ]

        new_cursor = tick_times[-1] + 1 if tick_times else cursor
        return GrapheneDryRunInstigationTicks(results=future_ticks, cursor=new_cursor)

    def resolve_futureTick(self, _graphene_info: ResolveInfo, tick_timestamp: int):
        return GrapheneDryRunInstigationTick(
            self._external_schedule.schedule_selector, float(tick_timestamp)
        )

    def resolve_potentialTickTimestamps(
        self,
        _graphene_info: ResolveInfo,
        start_timestamp: Optional[float] = None,
        upper_limit: Optional[int] = None,
        lower_limit: Optional[int] = None,
    ):
        """Get timestamps when ticks will occur before and after a given timestamp.

        upper_limit defines how many ticks will be retrieved after the current timestamp, and lower_limit defines how many ticks will be retrieved before the current timestamp.
        """
        start_timestamp = start_timestamp or get_timestamp_from_utc_datetime(
            get_current_datetime_in_utc()
        )
        upper_limit = upper_limit or 10
        lower_limit = lower_limit or 10

        tick_times: List[float] = []
        ascending_tick_iterator = self._external_schedule.execution_time_iterator(start_timestamp)
        descending_tick_iterator = self._external_schedule.execution_time_iterator(
            start_timestamp, ascending=False
        )

        tick_times_below_timestamp: List[float] = []
        first_past_tick = next(descending_tick_iterator)

        # execution_time_iterator starts at first tick <= timestamp (or >= timestamp in
        # ascending case), so we need to make sure not to double count start_timestamp
        # if it falls on a tick time.
        if first_past_tick.timestamp() < start_timestamp:
            tick_times_below_timestamp.append(first_past_tick.timestamp())
            lower_limit -= 1

        for _ in range(lower_limit):
            tick_times_below_timestamp.append(next(descending_tick_iterator).timestamp())

        # Combine tick times < start_timestamp to tick times >= timestamp to get full
        # list. We reverse timestamp range because ticks should be in ascending order when we give the full list.
        tick_times = tick_times_below_timestamp[::-1] + [
            next(ascending_tick_iterator).timestamp() for _ in range(upper_limit)
        ]

        return tick_times


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
