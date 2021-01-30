import os
import sys
import time

import pendulum
from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import (
    ExternalPipeline,
    PipelineSelector,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.host_representation.external_data import (
    ExternalSensorExecutionData,
    ExternalSensorExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.job import JobStatus, JobTickData, JobTickStatus, SensorJobData
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import RUN_KEY_TAG, check_tags
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

RECORDED_TICK_STATES = [JobTickStatus.SUCCESS, JobTickStatus.FAILURE]
FULFILLED_TICK_STATES = [JobTickStatus.SKIPPED, JobTickStatus.SUCCESS]


class SensorLaunchContext:
    def __init__(self, external_sensor, job_state, tick, instance, logger):
        self._external_sensor = external_sensor
        self._instance = instance
        self._logger = logger
        self._job_state = job_state
        self._tick = tick

    @property
    def status(self):
        return self._tick.status

    @property
    def logger(self):
        return self._logger

    @property
    def run_count(self):
        return len(self._tick.run_ids)

    def update_state(self, status, **kwargs):
        skip_reason = kwargs.get("skip_reason")
        if "skip_reason" in kwargs:
            del kwargs["skip_reason"]

        self._tick = self._tick.with_status(status=status, **kwargs).with_reason(
            skip_reason=skip_reason
        )

    def add_run(self, run_id, run_key=None):
        self._tick = self._tick.with_run(run_id, run_key)

    def _write(self):
        self._instance.update_job_tick(self._tick)
        if self._tick.status in FULFILLED_TICK_STATES:
            last_run_key = (
                self._job_state.job_specific_data.last_run_key
                if self._job_state.job_specific_data
                else None
            )
            if self._tick.run_keys:
                last_run_key = self._tick.run_keys[-1]
            self._instance.update_job_state(
                self._job_state.with_data(
                    SensorJobData(
                        last_tick_timestamp=self._tick.timestamp,
                        last_run_key=last_run_key,
                        min_interval=self._external_sensor.min_interval_seconds,
                    )
                )
            )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value and not isinstance(exception_value, KeyboardInterrupt):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.update_state(JobTickStatus.FAILURE, error=error_data)
            self._write()
            self._logger.error(
                "Error launching sensor run: {error_info}".format(
                    error_info=error_data.to_string()
                ),
            )
            return True  # Swallow the exception after logging in the tick DB

        self._write()


def _check_for_debug_crash(debug_crash_flags, key):
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")


def execute_sensor_iteration(instance, logger, debug_crash_flags=None):
    check.inst_param(instance, "instance", DagsterInstance)
    sensor_jobs = [
        s
        for s in instance.all_stored_job_state(job_type=JobType.SENSOR)
        if s.status == JobStatus.RUNNING
    ]
    if not sensor_jobs:
        logger.info("Not checking for any runs since no sensors have been started.")
        return
    logger.info(
        "Checking for new runs for the following sensors: {sensor_names}".format(
            sensor_names=", ".join([job.job_name for job in sensor_jobs]),
        )
    )

    for job_state in sensor_jobs:
        sensor_debug_crash_flags = (
            debug_crash_flags.get(job_state.job_name) if debug_crash_flags else None
        )
        error_info = None
        try:
            with RepositoryLocationHandle.create_from_repository_location_origin(
                job_state.origin.external_repository_origin.repository_location_origin
            ) as repo_location_handle:
                repo_location = RepositoryLocation.from_handle(repo_location_handle)

                repo_name = job_state.origin.external_repository_origin.repository_name

                check.invariant(
                    repo_location.has_repository(repo_name),
                    "Could not find repository {repo_name} in location {repo_location_name}".format(
                        repo_name=repo_name, repo_location_name=repo_location.name
                    ),
                )

                external_repo = repo_location.get_repository(repo_name)
                if not external_repo.has_external_job(job_state.job_name):
                    continue

                now = pendulum.now("UTC")
                if _is_under_min_interval(job_state, now):
                    continue

                tick = instance.create_job_tick(
                    JobTickData(
                        job_origin_id=job_state.job_origin_id,
                        job_name=job_state.job_name,
                        job_type=JobType.SENSOR,
                        status=JobTickStatus.STARTED,
                        timestamp=now.timestamp(),
                    )
                )

                _check_for_debug_crash(sensor_debug_crash_flags, "TICK_CREATED")

                external_sensor = external_repo.get_external_sensor(job_state.job_name)
                with SensorLaunchContext(
                    external_sensor, job_state, tick, instance, logger
                ) as tick_context:
                    _check_for_debug_crash(sensor_debug_crash_flags, "TICK_HELD")
                    _evaluate_sensor(
                        tick_context,
                        instance,
                        repo_location,
                        external_repo,
                        external_sensor,
                        job_state,
                        sensor_debug_crash_flags,
                    )

                instance.purge_job_ticks(
                    job_state.job_origin_id,
                    tick_status=JobTickStatus.SKIPPED,
                    before=now.subtract(days=7),  #  keep the last 7 days
                )
        except Exception:  # pylint: disable=broad-except
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(
                "Sensor failed for {sensor_name} : {error_info}".format(
                    sensor_name=job_state.job_name, error_info=error_info.to_string(),
                )
            )
        yield error_info


def _evaluate_sensor(
    context,
    instance,
    repo_location,
    external_repo,
    external_sensor,
    job_state,
    sensor_debug_crash_flags=None,
):
    sensor_runtime_data = repo_location.get_external_sensor_execution_data(
        instance,
        external_repo.handle,
        external_sensor.name,
        job_state.job_specific_data.last_tick_timestamp if job_state.job_specific_data else None,
        job_state.job_specific_data.last_run_key if job_state.job_specific_data else None,
    )
    if isinstance(sensor_runtime_data, ExternalSensorExecutionErrorData):
        context.logger.error(
            "Failed to resolve sensor for {sensor_name} : {error_info}".format(
                sensor_name=external_sensor.name, error_info=sensor_runtime_data.error.to_string(),
            )
        )
        context.update_state(JobTickStatus.FAILURE, error=sensor_runtime_data.error)
        return

    assert isinstance(sensor_runtime_data, ExternalSensorExecutionData)
    if not sensor_runtime_data.run_requests:
        if sensor_runtime_data.skip_message:
            context.logger.info(
                f"Sensor returned false for {external_sensor.name}, skipping: "
                f"{sensor_runtime_data.skip_message}"
            )
            context.update_state(
                JobTickStatus.SKIPPED, skip_reason=sensor_runtime_data.skip_message
            )
        else:
            context.logger.info(f"Sensor returned false for {external_sensor.name}, skipping")
            context.update_state(JobTickStatus.SKIPPED)
        return

    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=external_sensor.pipeline_name,
        solid_selection=external_sensor.solid_selection,
    )
    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    external_pipeline = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data, external_repo.handle,
    )

    for run_request in sensor_runtime_data.run_requests:
        run = _get_or_create_sensor_run(
            context, instance, repo_location, external_sensor, external_pipeline, run_request
        )

        if not run:
            # we already found and resolved a run
            continue

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_CREATED")

        try:
            context.logger.info(
                "Launching run for {sensor_name}".format(sensor_name=external_sensor.name)
            )
            instance.submit_run(run.run_id, external_pipeline)
            context.logger.info(
                "Completed launch of run {run_id} for {sensor_name}".format(
                    run_id=run.run_id, sensor_name=external_sensor.name
                )
            )
        except Exception:  # pylint: disable=broad-except
            context.logger.error(
                "Run {run_id} created successfully but failed to launch.".format(run_id=run.run_id)
            )

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_LAUNCHED")

        context.add_run(run_id=run.run_id, run_key=run_request.run_key)

    if context.run_count:
        context.update_state(JobTickStatus.SUCCESS)
    else:
        context.update_state(JobTickStatus.SKIPPED)


def _is_under_min_interval(job_state, now):
    if not job_state.job_specific_data:
        return False

    if not job_state.job_specific_data.last_tick_timestamp:
        return False

    if not job_state.job_specific_data.min_interval:
        return False

    elapsed = now.timestamp() - job_state.job_specific_data.last_tick_timestamp
    return elapsed < job_state.job_specific_data.min_interval


def _get_or_create_sensor_run(
    context, instance, repo_location, external_sensor, external_pipeline, run_request
):

    if not run_request.run_key:
        return _create_sensor_run(
            instance, repo_location, external_sensor, external_pipeline, run_request
        )

    existing_runs = instance.get_runs(
        PipelineRunsFilter(
            tags=merge_dicts(
                PipelineRun.tags_for_sensor(external_sensor), {RUN_KEY_TAG: run_request.run_key},
            )
        )
    )

    if len(existing_runs):
        run = existing_runs[0]
        if run.status != PipelineRunStatus.NOT_STARTED:
            # A run already exists and was launched for this time period,
            # but the scheduler must have crashed before the tick could be put
            # into a SUCCESS state

            context.logger.info(
                f"Run {run.run_id} already completed with the run key "
                f"`{run_request.run_key}` for {external_sensor.name}"
            )

            return None
        else:
            context.logger.info(
                f"Run {run.run_id} already created with the run key "
                f"`{run_request.run_key}` for {external_sensor.name}"
            )
            return run

    context.logger.info(f"Creating new run for {external_sensor.name}")

    return _create_sensor_run(
        instance, repo_location, external_sensor, external_pipeline, run_request
    )


def _create_sensor_run(instance, repo_location, external_sensor, external_pipeline, run_request):
    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline, run_request.run_config, external_sensor.mode, step_keys_to_execute=None,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    pipeline_tags = external_pipeline.tags or {}
    check_tags(pipeline_tags, "pipeline_tags")
    tags = merge_dicts(
        merge_dicts(pipeline_tags, run_request.tags), PipelineRun.tags_for_sensor(external_sensor),
    )
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key

    return instance.create_run(
        pipeline_name=external_sensor.pipeline_name,
        run_id=None,
        run_config=run_request.run_config,
        mode=external_sensor.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        status=PipelineRunStatus.NOT_STARTED,
        solid_selection=external_sensor.solid_selection,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline.get_external_origin(),
    )
