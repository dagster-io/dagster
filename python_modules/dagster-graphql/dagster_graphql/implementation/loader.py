from collections import defaultdict
from collections.abc import Sequence
from enum import Enum
from typing import Any, Optional

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.remote_representation import RemoteRepository
from dagster._core.scheduler.instigation import InstigatorState, InstigatorType


class RepositoryDataType(Enum):
    JOB_RUNS = "job_runs"
    SCHEDULE_RUNS = "schedule_runs"
    SENSOR_RUNS = "sensor_runs"
    SCHEDULE_STATES = "schedule_states"
    SENSOR_STATES = "sensor_states"
    SCHEDULE_TICKS = "schedule_ticks"
    SENSOR_TICKS = "sensor_ticks"


class RepositoryScopedBatchLoader:
    """A batch loader that fetches an assortment of data for a given repository.  This loader is
    expected to be instantiated once per repository, and then passed to various child graphene
    objects to batch calls to the DB.

    We can instantiate this loader without knowing which data we will end up requesting deeper in
    the graphql nested schema, which means we can batch DB requests without changing the structure
     of our graphql request.

    Example: When the last 10 runs are requested for a job in the repository, we know that they will
    be fetched for every job in the repository.  We can batch fetch the last 10 runs for every job,
    reducing the number of roundtrips to the DB, and then access them using the in-memory loader
    cache.
    """

    def __init__(self, instance: DagsterInstance, remote_repository: RemoteRepository):
        self._instance = instance
        self._repository = remote_repository
        self._data: dict[RepositoryDataType, dict[str, list[Any]]] = {}
        self._limits: dict[RepositoryDataType, int] = {}

    def _get(self, data_type: RepositoryDataType, key: str, limit: int) -> Sequence[Any]:
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.str_param(key, "key")
        check.int_param(limit, "limit")
        if self._data.get(data_type) is None or limit > self._limits.get(data_type, 0):
            self._fetch(data_type, limit)
        return self._data[data_type].get(key, [])[:limit]

    def _fetch(self, data_type: RepositoryDataType, limit: int) -> None:
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.int_param(limit, "limit")

        fetched: dict[str, list[Any]] = defaultdict(list)

        if data_type == RepositoryDataType.SCHEDULE_STATES:
            schedule_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_remote_origin_id(),
                repository_selector_id=self._repository.selector_id,
                instigator_type=InstigatorType.SCHEDULE,
            )
            for state in schedule_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SENSOR_STATES:
            sensor_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_remote_origin_id(),
                repository_selector_id=self._repository.selector_id,
                instigator_type=InstigatorType.SENSOR,
            )
            for state in sensor_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SCHEDULE_TICKS:
            if self._instance.supports_batch_tick_queries:
                selector_ids = [
                    schedule.selector_id for schedule in self._repository.get_schedules()
                ]
                ticks_by_selector = self._instance.get_batch_ticks(selector_ids, limit=limit)
                for schedule in self._repository.get_schedules():
                    fetched[schedule.get_remote_origin_id()] = list(
                        ticks_by_selector.get(schedule.selector_id, [])
                    )
            else:
                for schedule in self._repository.get_schedules():
                    origin_id = schedule.get_remote_origin_id()
                    fetched[origin_id] = list(
                        self._instance.get_ticks(origin_id, schedule.selector_id, limit=limit)
                    )

        elif data_type == RepositoryDataType.SENSOR_TICKS:
            if self._instance.supports_batch_tick_queries:
                selector_ids = [schedule.selector_id for schedule in self._repository.get_sensors()]
                ticks_by_selector = self._instance.get_batch_ticks(selector_ids, limit=limit)
                for sensor in self._repository.get_sensors():
                    fetched[sensor.get_remote_origin_id()] = list(
                        ticks_by_selector.get(sensor.selector_id, [])
                    )
            else:
                for sensor in self._repository.get_sensors():
                    origin_id = sensor.get_remote_origin_id()
                    fetched[origin_id] = list(
                        self._instance.get_ticks(origin_id, sensor.selector_id, limit=limit)
                    )

        else:
            check.failed(f"Unknown data type for {self.__class__.__name__}: {data_type}")

        self._data[data_type] = fetched
        self._limits[data_type] = limit

    def get_schedule_state(self, schedule_name: str) -> Optional[InstigatorState]:
        check.invariant(self._repository.has_schedule(schedule_name))
        states = self._get(RepositoryDataType.SCHEDULE_STATES, schedule_name, 1)
        return states[0] if states else None

    def get_sensor_state(self, sensor_name: str) -> Optional[InstigatorState]:
        check.invariant(self._repository.has_sensor(sensor_name))
        states = self._get(RepositoryDataType.SENSOR_STATES, sensor_name, 1)
        return states[0] if states else None

    def get_sensor_ticks(self, origin_id: str, selector_id: str, limit: int) -> Sequence[Any]:
        check.invariant(
            any(selector_id == sensor.selector_id for sensor in self._repository.get_sensors())
        )
        return self._get(RepositoryDataType.SENSOR_TICKS, origin_id, limit)

    def get_schedule_ticks(self, origin_id: str, selector_id: str, limit: int) -> Sequence[Any]:
        check.invariant(
            any(
                selector_id == schedule.selector_id for schedule in self._repository.get_schedules()
            )
        )
        return self._get(RepositoryDataType.SCHEDULE_TICKS, origin_id, limit)


# CachingStaleStatusResolver from core can be used directly as a GQL batch loader.
StaleStatusLoader = CachingStaleStatusResolver
