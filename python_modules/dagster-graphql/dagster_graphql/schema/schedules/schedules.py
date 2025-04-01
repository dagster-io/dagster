import time
from collections.abc import Sequence
from typing import Optional

import dagster._check as check
import graphene
from dagster import DefaultScheduleStatus
from dagster._core.remote_representation import RemoteSchedule
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus
from dagster._time import get_current_timestamp

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.schema.asset_selections import GrapheneAssetSelection
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
)
from dagster_graphql.schema.instigation import (
    GrapheneDryRunInstigationTick,
    GrapheneDryRunInstigationTicks,
    GrapheneInstigationState,
    GrapheneInstigationStatus,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.tags import GrapheneDefinitionTag
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneSchedule(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    cron_schedule = graphene.NonNull(graphene.String)
    pipeline_name = graphene.NonNull(graphene.String)
    solid_selection = graphene.List(graphene.String)
    mode = graphene.NonNull(graphene.String)
    execution_timezone = graphene.Field(graphene.String)
    description = graphene.String()
    defaultStatus = graphene.NonNull(GrapheneInstigationStatus)
    canReset = graphene.NonNull(graphene.Boolean)
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
    assetSelection = graphene.Field(GrapheneAssetSelection)
    tags = non_null_list(GrapheneDefinitionTag)
    metadataEntries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "Schedule"

    def __init__(
        self,
        remote_schedule: RemoteSchedule,
        schedule_state: Optional[InstigatorState],
        batch_loader: Optional[RepositoryScopedBatchLoader] = None,
    ):
        self._remote_schedule = check.inst_param(remote_schedule, "remote_schedule", RemoteSchedule)

        # optional run loader, provided by a parent graphene object (e.g. GrapheneRepository)
        # that instantiates multiple schedules
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )

        self._stored_state = schedule_state
        self._schedule_state = self._remote_schedule.get_current_instigator_state(schedule_state)

        super().__init__(
            name=remote_schedule.name,
            cron_schedule=str(
                remote_schedule.cron_schedule
            ),  # can be sequence, coercing to str for now
            pipeline_name=remote_schedule.job_name,
            solid_selection=remote_schedule.op_selection,
            mode=remote_schedule.mode,
            execution_timezone=(
                self._remote_schedule.execution_timezone
                if self._remote_schedule.execution_timezone
                else "UTC"
            ),
            description=remote_schedule.description,
            assetSelection=GrapheneAssetSelection(
                asset_selection=remote_schedule.asset_selection,
                repository_handle=remote_schedule.handle.repository_handle,
            )
            if remote_schedule.asset_selection
            else None,
        )

    def resolve_id(self, _graphene_info: ResolveInfo) -> str:
        return self._remote_schedule.get_compound_id().to_string()

    def resolve_defaultStatus(self, _graphene_info: ResolveInfo):
        default_schedule_status = self._remote_schedule.default_status

        if default_schedule_status == DefaultScheduleStatus.RUNNING:
            return GrapheneInstigationStatus.RUNNING
        elif default_schedule_status == DefaultScheduleStatus.STOPPED:
            return GrapheneInstigationStatus.STOPPED

    def resolve_canReset(self, _graphene_info: ResolveInfo):
        return bool(
            self._stored_state and self._stored_state.status != InstigatorStatus.DECLARED_IN_CODE
        )

    def resolve_scheduleState(self, _graphene_info: ResolveInfo):
        # forward the batch run loader to the instigation state, which provides the schedule runs
        return GrapheneInstigationState(self._schedule_state, self._batch_loader)

    def resolve_partition_set(self, graphene_info: ResolveInfo):
        from dagster_graphql.schema.partition_sets import GraphenePartitionSet

        if self._remote_schedule.partition_set_name is None:
            return None

        repository = graphene_info.context.get_code_location(
            self._remote_schedule.handle.location_name
        ).get_repository(self._remote_schedule.handle.repository_name)
        partition_set = repository.get_partition_set(self._remote_schedule.partition_set_name)

        return GraphenePartitionSet(
            repository_handle=repository.handle,
            remote_partition_set=partition_set,
        )

    def resolve_futureTicks(
        self,
        _graphene_info: ResolveInfo,
        cursor: Optional[float] = None,
        limit: Optional[int] = None,
        until: Optional[float] = None,
    ):
        cursor = cursor or time.time()

        tick_times: list[float] = []
        time_iter = self._remote_schedule.execution_time_iterator(cursor)

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

        schedule_selector = self._remote_schedule.schedule_selector
        future_ticks = [
            GrapheneDryRunInstigationTick(schedule_selector, tick_time) for tick_time in tick_times
        ]

        new_cursor = tick_times[-1] + 1 if tick_times else cursor
        return GrapheneDryRunInstigationTicks(results=future_ticks, cursor=new_cursor)

    def resolve_futureTick(self, _graphene_info: ResolveInfo, tick_timestamp: int):
        return GrapheneDryRunInstigationTick(
            self._remote_schedule.schedule_selector, float(tick_timestamp)
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
        start_timestamp = start_timestamp or get_current_timestamp()
        upper_limit = upper_limit or 10
        lower_limit = lower_limit or 10

        tick_times: list[float] = []
        ascending_tick_iterator = self._remote_schedule.execution_time_iterator(start_timestamp)
        descending_tick_iterator = self._remote_schedule.execution_time_iterator(
            start_timestamp, ascending=False
        )

        tick_times_below_timestamp: list[float] = []
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

    def resolve_tags(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneDefinitionTag]:
        return [
            GrapheneDefinitionTag(key, value)
            for key, value in (self._remote_schedule.tags or {}).items()
        ]

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo) -> list[GrapheneMetadataEntry]:
        return list(iterate_metadata_entries(self._remote_schedule.metadata))


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
