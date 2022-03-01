from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

from dagster import DagsterInstance, check
from dagster.core.definitions.events import AssetKey
from dagster.core.events.log import EventLogEntry
from dagster.core.host_representation import ExternalRepository
from dagster.core.scheduler.instigation import InstigatorType
from dagster.core.storage.pipeline_run import JobBucket, RunRecord, RunsFilter, TagBucket
from dagster.core.storage.tags import SCHEDULE_NAME_TAG, SENSOR_NAME_TAG


class RepositoryDataType(Enum):
    JOB_RUNS = "job_runs"
    SCHEDULE_RUNS = "schedule_runs"
    SENSOR_RUNS = "sensor_runs"
    SCHEDULE_STATES = "schedule_states"
    SENSOR_STATES = "sensor_states"


class RepositoryScopedBatchLoader:
    """
    A batch loader that fetches an assortment of data for a given repository.  This loader is
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

    def __init__(self, instance: DagsterInstance, external_repository: ExternalRepository):
        self._instance = instance
        self._repository = external_repository
        self._data: Dict[RepositoryDataType, Dict[str, List[Any]]] = {}
        self._limits: Dict[RepositoryDataType, int] = {}

    def _get(self, data_type, key, limit):
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.str_param(key, "key")
        check.int_param(limit, "limit")
        if self._data.get(data_type) is None or limit > self._limits.get(data_type, 0):
            self._fetch(data_type, limit)
        return self._data[data_type].get(key, [])[:limit]

    def _fetch(self, data_type, limit):
        check.inst_param(data_type, "data_type", RepositoryDataType)
        check.int_param(limit, "limit")

        fetched = defaultdict(list)

        if data_type == RepositoryDataType.JOB_RUNS:
            job_names = [x.name for x in self._repository.get_all_external_pipelines()]
            if self._instance.supports_bucket_queries:
                records = self._instance.get_run_records(
                    bucket_by=JobBucket(bucket_limit=limit, job_names=job_names),
                )
            else:
                records = []
                for job_name in job_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(pipeline_name=job_name), limit=limit
                            )
                        )
                    )
            for record in records:
                fetched[record.pipeline_run.pipeline_name].append(record)

        elif data_type == RepositoryDataType.SCHEDULE_RUNS:
            schedule_names = [
                schedule.name for schedule in self._repository.get_external_schedules()
            ]
            if self._instance.supports_bucket_queries:
                records = self._instance.get_run_records(
                    bucket_by=TagBucket(
                        tag_key=SCHEDULE_NAME_TAG,
                        bucket_limit=limit,
                        tag_values=schedule_names,
                    ),
                )
            else:
                records = []
                for schedule_name in schedule_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(tags={SCHEDULE_NAME_TAG: schedule_name}),
                                limit=limit,
                            )
                        )
                    )
            for record in records:
                fetched[record.pipeline_run.tags.get(SCHEDULE_NAME_TAG)].append(record)

        elif data_type == RepositoryDataType.SENSOR_RUNS:
            sensor_names = [sensor.name for sensor in self._repository.get_external_sensors()]
            if self._instance.supports_bucket_queries:
                records = self._instance.get_run_records(
                    bucket_by=TagBucket(
                        tag_key=SENSOR_NAME_TAG,
                        bucket_limit=limit,
                        tag_values=sensor_names,
                    ),
                )
            else:
                records = []
                for sensor_name in sensor_names:
                    records.extend(
                        list(
                            self._instance.get_run_records(
                                filters=RunsFilter(tags={SENSOR_NAME_TAG: sensor_name}),
                                limit=limit,
                            )
                        )
                    )
            for record in records:
                fetched[record.pipeline_run.tags.get(SENSOR_NAME_TAG)].append(record)

        elif data_type == RepositoryDataType.SCHEDULE_STATES:
            schedule_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                instigator_type=InstigatorType.SCHEDULE,
            )
            for state in schedule_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SENSOR_STATES:
            sensor_states = self._instance.all_instigator_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                instigator_type=InstigatorType.SENSOR,
            )
            for state in sensor_states:
                fetched[state.name].append(state)
        else:
            check.failed(f"Unknown data type for {self.__class__.__name__}: {data_type}")

        self._data[data_type] = fetched
        self._limits[data_type] = limit

    def get_run_records_for_job(self, job_name, limit):
        check.invariant(
            job_name
            in [pipeline.name for pipeline in self._repository.get_all_external_pipelines()]
        )
        return self._get(RepositoryDataType.JOB_RUNS, job_name, limit)

    def get_run_records_for_schedule(self, schedule_name, limit):
        check.invariant(
            schedule_name
            in [schedule.name for schedule in self._repository.get_external_schedules()]
        )
        return self._get(RepositoryDataType.SCHEDULE_RUNS, schedule_name, limit)

    def get_run_records_for_sensor(self, sensor_name, limit):
        check.invariant(
            sensor_name in [sensor.name for sensor in self._repository.get_external_sensors()]
        )
        return self._get(RepositoryDataType.SENSOR_RUNS, sensor_name, limit)

    def get_schedule_state(self, schedule_name):
        check.invariant(
            schedule_name
            in [schedule.name for schedule in self._repository.get_external_schedules()]
        )
        states = self._get(RepositoryDataType.SCHEDULE_STATES, schedule_name, 1)
        return states[0] if states else None

    def get_sensor_state(self, sensor_state):
        check.invariant(
            sensor_state in [sensor.name for sensor in self._repository.get_external_sensors()]
        )
        states = self._get(RepositoryDataType.SENSOR_STATES, sensor_state, 1)
        return states[0] if states else None


class BatchRunLoader:
    """
    A batch loader that fetches a set of runs by run_id. This loader is expected to be instantiated
    once with a set of run_ids. For example, for a particular asset, we can fetch a list of asset
    materializations, all of which may have been materialized from a different run.
    """

    def __init__(self, instance: DagsterInstance, run_ids: Iterable[str]):
        self._instance = instance
        self._run_ids: Set[str] = set(run_ids)
        self._records: Dict[str, RunRecord] = {}

    def get_run_record_by_run_id(self, run_id: str) -> Optional[RunRecord]:
        if run_id not in self._run_ids:
            check.failed(
                f"Run id {run_id} not recognized for this loader.  Expected one of: {self._run_ids}"
            )
        if self._records.get(run_id) is None:
            self._fetch()
        return self._records.get(run_id)

    def _fetch(self):
        records = self._instance.get_run_records(RunsFilter(run_ids=list(self._run_ids)))
        for record in records:
            self._records[record.pipeline_run.run_id] = record


class BatchMaterializationLoader:
    """
    A batch loader that fetches materializations for asset keys.  This loader is expected to be
    instantiated with a set of asset keys.
    """

    def __init__(self, instance: DagsterInstance, asset_keys: Iterable[AssetKey]):
        self._instance = instance
        self._asset_keys: List[AssetKey] = list(asset_keys)
        self._fetched = False
        self._materializations: Dict[AssetKey, EventLogEntry] = {}

    def get_latest_materialization_for_asset_key(self, asset_key: AssetKey) -> EventLogEntry:
        if asset_key not in self._asset_keys:
            check.failed(
                f"Asset key {asset_key} not recognized for this loader.  Expected one of: {self._asset_keys}"
            )
        if self._materializations.get(asset_key) is None:
            self._fetch()
        return self._materializations.get(asset_key)

    def _fetch(self):
        self._fetched = True
        self._materializations = self._instance.get_latest_materialization_events(self._asset_keys)
