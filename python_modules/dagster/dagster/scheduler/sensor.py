import os
import sys
import time

import pendulum
from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import EngineEventData
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
from dagster.core.storage.tags import EXECUTION_KEY_TAG, check_tags
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

RECORDED_TICK_STATES = [JobTickStatus.SUCCESS, JobTickStatus.FAILURE]
FULFILLED_TICK_STATES = [JobTickStatus.SKIPPED, JobTickStatus.SUCCESS]


class SensorLaunchContext:
    def __init__(self, job_state, tick, instance, logger):
        self._job_state = job_state
        self._tick = tick
        self._instance = instance
        self._logger = logger
        self._to_resolve = []

    @property
    def status(self):
        return self._tick.status

    @property
    def logger(self):
        return self._logger

    def add_state(self, status, **kwargs):
        self._to_resolve.append(self._tick.with_status(status=status, **kwargs))

    def _write(self):
        to_update = self._to_resolve[0] if self._to_resolve else self._tick
        self._instance.update_job_tick(to_update)
        for tick in self._to_resolve[1:]:
            self._instance.create_job_tick(tick.job_tick_data)
        if any([tick.status in FULFILLED_TICK_STATES for tick in self._to_resolve]):
            self._instance.update_job_state(
                self._job_state.with_data(SensorJobData(self._tick.timestamp))
            )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value and not isinstance(exception_value, KeyboardInterrupt):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.add_state(JobTickStatus.FAILURE, error=error_data)
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
        try:
            with RepositoryLocationHandle.create_from_repository_location_origin(
                job_state.origin.external_repository_origin.repository_location_origin
            ) as repo_location_handle:
                repo_location = RepositoryLocation.from_handle(repo_location_handle)
                repo_dict = repo_location.get_repositories()
                check.invariant(
                    len(repo_dict) == 1,
                    "Reconstructed repository location should have exactly one repository",
                )
                external_repo = next(iter(repo_dict.values()))
                if not external_repo.has_external_job(job_state.job_name):
                    continue

                now = pendulum.now()
                latest_tick = instance.get_latest_job_tick(job_state.job_origin_id)
                if not latest_tick or latest_tick.status in RECORDED_TICK_STATES:
                    tick = instance.create_job_tick(
                        JobTickData(
                            job_origin_id=job_state.job_origin_id,
                            job_name=job_state.job_name,
                            job_type=JobType.SENSOR,
                            status=JobTickStatus.STARTED,
                            timestamp=now.timestamp(),
                        )
                    )
                else:
                    tick = latest_tick.with_status(
                        JobTickStatus.STARTED, timestamp=now.timestamp(), execution_key=None,
                    )
                    instance.update_job_tick(tick)

                _check_for_debug_crash(sensor_debug_crash_flags, "TICK_CREATED")

                external_sensor = external_repo.get_external_sensor(job_state.job_name)
                with SensorLaunchContext(job_state, tick, instance, logger) as tick_context:
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
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "Sensor failed for {sensor_name} : {error_info}".format(
                    sensor_name=job_state.job_name,
                    error_info=serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
                )
            )


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
        job_state.job_specific_data.last_completed_timestamp
        if job_state.job_specific_data
        else None,
    )
    if isinstance(sensor_runtime_data, ExternalSensorExecutionErrorData):
        context.logger.error(
            "Failed to resolve sensor for {sensor_name} : {error_info}".format(
                sensor_name=external_sensor.name, error_info=sensor_runtime_data.error.to_string(),
            )
        )
        context.add_state(JobTickStatus.FAILURE, error=sensor_runtime_data.error)
        return

    assert isinstance(sensor_runtime_data, ExternalSensorExecutionData)
    if not sensor_runtime_data.run_params:
        if sensor_runtime_data.skip_message:
            context.logger.info(
                f"Sensor returned false for {external_sensor.name}, skipping: "
                f"{sensor_runtime_data.skip_message}"
            )
        else:
            context.logger.info(f"Sensor returned false for {external_sensor.name}, skipping")
        context.add_state(JobTickStatus.SKIPPED)
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

    for run_params in sensor_runtime_data.run_params:
        if run_params.execution_key and instance.has_job_tick(
            external_sensor.get_external_origin_id(),
            run_params.execution_key,
            [JobTickStatus.SUCCESS],
        ):
            context.logger.info(
                "Found existing run for sensor {sensor_name} with execution_key `{execution_key}`, skipping.".format(
                    sensor_name=external_sensor.name, execution_key=run_params.execution_key
                )
            )
            context.add_state(JobTickStatus.SKIPPED, execution_key=run_params.execution_key)
            continue

        run = _get_or_create_sensor_run(
            context, instance, repo_location, external_sensor, external_pipeline, run_params
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

        context.add_state(
            JobTickStatus.SUCCESS, run_id=run.run_id, execution_key=run_params.execution_key,
        )


def _get_or_create_sensor_run(
    context, instance, repo_location, external_sensor, external_pipeline, run_params
):

    if not run_params.execution_key:
        return _create_sensor_run(
            context, instance, repo_location, external_sensor, external_pipeline, run_params
        )

    existing_runs = instance.get_runs(
        PipelineRunsFilter(
            tags=merge_dicts(
                PipelineRun.tags_for_sensor(external_sensor),
                {EXECUTION_KEY_TAG: run_params.execution_key},
            )
        )
    )

    if len(existing_runs):
        check.invariant(len(existing_runs) == 1)
        run = existing_runs[0]
        if run.status != PipelineRunStatus.NOT_STARTED:
            # A run already exists and was launched for this time period,
            # but the scheduler must have crashed before the tick could be put
            # into a SUCCESS state

            context.logger.info(
                f"Run {run.run_id} already completed with the execution key "
                f"`{run_params.execution_key}` for {external_sensor.name}"
            )
            context.add_state(
                JobTickStatus.SUCCESS, run_id=run.run_id, execution_key=run_params.execution_key,
            )

            return None
        else:
            context.logger.info(
                f"Run {run.run_id} already created with the execution key "
                f"`{run_params.execution_key}` for {external_sensor.name}"
            )
            return run

    context.logger.info(f"Creating new run for {external_sensor.name}")

    return _create_sensor_run(
        context, instance, repo_location, external_sensor, external_pipeline, run_params
    )


def _create_sensor_run(
    context, instance, repo_location, external_sensor, external_pipeline, run_params
):
    execution_plan_errors = []
    execution_plan_snapshot = None
    try:
        external_execution_plan = repo_location.get_external_execution_plan(
            external_pipeline,
            run_params.run_config,
            external_sensor.mode,
            step_keys_to_execute=None,
        )
        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot
    except DagsterSubprocessError as e:
        execution_plan_errors.extend(e.subprocess_error_infos)
    except Exception as e:  # pylint: disable=broad-except
        execution_plan_errors.append(serializable_error_info_from_exc_info(sys.exc_info()))

    pipeline_tags = external_pipeline.tags or {}
    check_tags(pipeline_tags, "pipeline_tags")
    tags = merge_dicts(
        merge_dicts(pipeline_tags, run_params.tags), PipelineRun.tags_for_sensor(external_sensor)
    )
    if run_params.execution_key:
        tags[EXECUTION_KEY_TAG] = run_params.execution_key

    run = instance.create_run(
        pipeline_name=external_sensor.pipeline_name,
        run_id=None,
        run_config=run_params.run_config,
        mode=external_sensor.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=external_sensor.solid_selection,
        status=(
            PipelineRunStatus.FAILURE
            if len(execution_plan_errors) > 0
            else PipelineRunStatus.NOT_STARTED
        ),
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline.get_external_origin(),
    )

    if len(execution_plan_errors) > 0:
        for error in execution_plan_errors:
            instance.report_engine_event(
                error.message, run, EngineEventData.engine_error(error),
            )
        instance.report_run_failed(run)
        context.logger.error(
            "Failed to fetch execution plan for {sensor_name}: {error_string}".format(
                sensor_name=external_sensor.name,
                error_string="\n".join([error.to_string() for error in execution_plan_errors]),
            ),
        )

    return run
