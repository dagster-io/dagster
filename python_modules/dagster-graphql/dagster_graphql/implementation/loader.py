from collections import defaultdict
from enum import Enum

from dagster import DagsterInstance, check
from dagster.core.host_representation import ExternalRepository
from dagster.core.scheduler.instigation import InstigatorType
from dagster.core.storage.pipeline_run import JobBucket, TagBucket
from dagster.core.storage.tags import SCHEDULE_NAME_TAG, SENSOR_NAME_TAG


class RepositoryDataType(Enum):
    JOB_RUNS = "job_runs"
    SCHEDULE_RUNS = "schedule_runs"
    SENSOR_RUNS = "sensor_runs"
    SCHEDULE_STATES = "schedule_states"
    SENSOR_STATES = "sensor_states"


class RepositoryScopedBatchLoader:
    def __init__(self, instance, external_repository):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._data = {}
        self._limits = {}

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
            runs = self._instance.get_runs(
                bucket=JobBucket(bucket_limit=limit, job_names=job_names),
            )
            for run in runs:
                fetched[run.pipeline_name].append(run)

        elif data_type == RepositoryDataType.SCHEDULE_RUNS:
            schedule_names = [
                schedule.name for schedule in self._repository.get_external_schedules()
            ]
            runs = self._instance.get_runs(
                bucket=TagBucket(
                    tag_key=SCHEDULE_NAME_TAG,
                    bucket_limit=limit,
                    tag_values=schedule_names,
                ),
            )
            for run in runs:
                fetched[run.tags.get(SCHEDULE_NAME_TAG)].append(run)

        elif data_type == RepositoryDataType.SENSOR_RUNS:
            sensor_names = [sensor.name for sensor in self._repository.get_external_sensors()]
            runs = self._instance.get_runs(
                bucket=TagBucket(
                    tag_key=SENSOR_NAME_TAG,
                    bucket_limit=limit,
                    tag_values=sensor_names,
                ),
            )
            for run in runs:
                fetched[run.tags.get(SENSOR_NAME_TAG)].append(run)

        elif data_type == RepositoryDataType.SCHEDULE_STATES:
            schedule_states = self._instance.all_stored_job_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                job_type=InstigatorType.SCHEDULE,
            )
            for state in schedule_states:
                fetched[state.name].append(state)

        elif data_type == RepositoryDataType.SENSOR_STATES:
            sensor_states = self._instance.all_stored_job_state(
                repository_origin_id=self._repository.get_external_origin_id(),
                job_type=InstigatorType.SENSOR,
            )
            for state in sensor_states:
                fetched[state.name].append(state)
        else:
            check.failed(f"Unknown data type for {self.__class__.__name__}: {data_type}")

        self._data[data_type] = fetched
        self._limits[data_type] = limit

    def get_runs_for_job(self, job_name, limit):
        check.invariant(
            job_name
            in [pipeline.name for pipeline in self._repository.get_all_external_pipelines()]
        )
        return self._get(RepositoryDataType.JOB_RUNS, job_name, limit)

    def get_runs_for_schedule(self, schedule_name, limit):
        check.invariant(
            schedule_name
            in [schedule.name for schedule in self._repository.get_external_schedules()]
        )
        return self._get(RepositoryDataType.SCHEDULE_RUNS, schedule_name, limit)

    def get_runs_for_sensor(self, sensor_name, limit):
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
