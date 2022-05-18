import os
import sys
import time
from typing import Dict, NamedTuple, Optional

import pendulum

import dagster._check as check
import dagster.seven as seven
from dagster.core.definitions.run_request import InstigatorType
from dagster.core.definitions.sensor_definition import DefaultSensorStatus, SensorExecutionData
from dagster.core.definitions.utils import validate_tags
from dagster.core.errors import DagsterError
from dagster.core.host_representation import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, RunsFilter, TagBucket
from dagster.core.storage.tags import RUN_KEY_TAG
from dagster.core.telemetry import SENSOR_RUN_CREATED, hash_name, log_action
from dagster.core.workspace import IWorkspace
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

MIN_INTERVAL_LOOP_TIME = 5

FINISHED_TICK_STATES = [TickStatus.SKIPPED, TickStatus.SUCCESS, TickStatus.FAILURE]


class DagsterSensorDaemonError(DagsterError):
    """Error when running the SensorDaemon"""


class SkippedSensorRun(
    NamedTuple("SkippedSensorRun", [("run_key", Optional[str]), ("existing_run", PipelineRun)])
):
    """Placeholder for runs that are skipped during the run_key idempotence check"""


class SensorLaunchContext:
    def __init__(self, external_sensor, tick, instance, logger):
        self._external_sensor = external_sensor
        self._instance = instance
        self._logger = logger
        self._tick = tick

        self._should_update_cursor_on_failure = False

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
        cursor = kwargs.get("cursor")
        origin_run_id = kwargs.get("origin_run_id")
        if "skip_reason" in kwargs:
            del kwargs["skip_reason"]

        if "cursor" in kwargs:
            del kwargs["cursor"]

        if "origin_run_id" in kwargs:
            del kwargs["origin_run_id"]
        if kwargs:
            check.inst_param(status, "status", TickStatus)

        if status:
            self._tick = self._tick.with_status(status=status, **kwargs)

        if skip_reason:
            self._tick = self._tick.with_reason(skip_reason=skip_reason)

        if cursor:
            self._tick = self._tick.with_cursor(cursor)

        if origin_run_id:
            self._tick = self._tick.with_origin_run(origin_run_id)

    def add_run_info(self, run_id=None, run_key=None):
        self._tick = self._tick.with_run_info(run_id, run_key)

    def set_should_update_cursor_on_failure(self, should_update_cursor_on_failure: bool):
        self._should_update_cursor_on_failure = should_update_cursor_on_failure

    def _write(self):
        self._instance.update_tick(self._tick)

        if self._tick.status not in FINISHED_TICK_STATES:
            return

        should_update_cursor_and_last_run_key = (
            self._tick.status != TickStatus.FAILURE
        ) or self._should_update_cursor_on_failure

        # fetch the most recent state.  we do this as opposed to during context initialization time
        # because we want to minimize the window of clobbering the sensor state upon updating the
        # sensor state data.
        state = self._instance.get_instigator_state(
            self._external_sensor.get_external_origin_id(), self._external_sensor.selector_id
        )
        last_run_key = state.instigator_data.last_run_key if state.instigator_data else None
        if self._tick.run_keys and should_update_cursor_and_last_run_key:
            last_run_key = self._tick.run_keys[-1]

        cursor = state.instigator_data.cursor if state.instigator_data else None
        if should_update_cursor_and_last_run_key:
            cursor = self._tick.cursor

        self._instance.update_instigator_state(
            state.with_data(
                SensorInstigatorData(
                    last_tick_timestamp=self._tick.timestamp,
                    last_run_key=last_run_key,
                    min_interval=self._external_sensor.min_interval_seconds,
                    cursor=cursor,
                )
            )
        )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type and isinstance(exception_value, KeyboardInterrupt):
            return

        # Log the error if the failure wasn't an interrupt or the daemon generator stopping
        if exception_value and not isinstance(exception_value, GeneratorExit):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.update_state(TickStatus.FAILURE, error=error_data)

        self._write()

        self._instance.purge_ticks(
            self._external_sensor.get_external_origin_id(),
            selector_id=self._external_sensor.selector_id,
            tick_status=TickStatus.SKIPPED,
            before=pendulum.now("UTC").subtract(days=7).timestamp(),  #  keep the last 7 days
        )


def _check_for_debug_crash(debug_crash_flags, key):
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")


RELOAD_WORKSPACE = 60


def execute_sensor_iteration_loop(instance, workspace, logger, until=None):
    """
    Helper function that performs sensor evaluations on a tighter loop, while reusing grpc locations
    within a given daemon interval.  Rather than relying on the daemon machinery to run the
    iteration loop every 30 seconds, sensors are continuously evaluated, every 5 seconds. We rely on
    each sensor definition's min_interval to check that sensor evaluations are spaced appropriately.
    """
    workspace_loaded_time = pendulum.now("UTC").timestamp()

    workspace_iteration = 0
    start_time = pendulum.now("UTC").timestamp()
    while True:
        start_time = pendulum.now("UTC").timestamp()
        if until and start_time >= until:
            # provide a way of organically ending the loop to support test environment
            break

        if start_time - workspace_loaded_time > RELOAD_WORKSPACE:
            workspace.cleanup()
            workspace_loaded_time = pendulum.now("UTC").timestamp()
            workspace_iteration = 0

        yield from execute_sensor_iteration(
            instance, logger, workspace, log_verbose_checks=(workspace_iteration == 0)
        )

        loop_duration = pendulum.now("UTC").timestamp() - start_time
        sleep_time = max(0, MIN_INTERVAL_LOOP_TIME - loop_duration)
        time.sleep(sleep_time)
        yield
        workspace_iteration += 1


def execute_sensor_iteration(
    instance, logger, workspace, log_verbose_checks=True, debug_crash_flags=None
):
    check.inst_param(workspace, "workspace", IWorkspace)
    check.inst_param(instance, "instance", DagsterInstance)

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace.get_workspace_snapshot().values()
    }

    all_sensor_states = {
        sensor_state.selector_id: sensor_state
        for sensor_state in instance.all_instigator_state(instigator_type=InstigatorType.SENSOR)
    }

    sensors = {}
    for location_entry in workspace_snapshot.values():
        repo_location = location_entry.repository_location
        if repo_location:
            for repo in repo_location.get_repositories().values():
                for sensor in repo.get_external_sensors():
                    selector_id = sensor.selector_id
                    if sensor.get_current_instigator_state(
                        all_sensor_states.get(selector_id)
                    ).is_running:
                        sensors[selector_id] = sensor
        elif location_entry.load_error and log_verbose_checks:
            logger.warning(
                f"Could not load location {location_entry.origin.location_name} to check for sensors due to the following error: {location_entry.load_error}"
            )

    if log_verbose_checks:
        unloadable_sensor_states = {
            selector_id: sensor_state
            for selector_id, sensor_state in all_sensor_states.items()
            if selector_id not in sensors and sensor_state.status == InstigatorStatus.RUNNING
        }

        for sensor_state in unloadable_sensor_states.values():
            sensor_name = sensor_state.origin.instigator_name
            repo_location_origin = (
                sensor_state.origin.external_repository_origin.repository_location_origin
            )

            repo_location_name = repo_location_origin.location_name
            repo_name = sensor_state.origin.external_repository_origin.repository_name
            if (
                repo_location_name not in workspace_snapshot
                or not workspace_snapshot[repo_location_name].repository_location
            ):
                logger.warning(
                    f"Sensor {sensor_name} was started from a location "
                    f"{repo_location_name} that can no longer be found in the workspace. "
                    "You can turn off this sensor in the Dagit UI from the Status tab."
                )
            elif not workspace_snapshot[repo_location_name].repository_location.has_repository(
                repo_name
            ):
                logger.warning(
                    f"Could not find repository {repo_name} in location {repo_location_name} to "
                    + f"run sensor {sensor_name}. If this repository no longer exists, you can "
                    + "turn off the sensor in the Dagit UI from the Status tab.",
                )
            else:
                logger.warning(
                    f"Could not find sensor {sensor_name} in repository {repo_name}. If this "
                    "sensor no longer exists, you can turn it off in the Dagit UI from the "
                    "Status tab.",
                )

    if not sensors:
        if log_verbose_checks:
            logger.info("Not checking for any runs since no sensors have been started.")
        yield
        return

    now = pendulum.now("UTC")

    for external_sensor in sensors.values():
        sensor_name = external_sensor.name
        sensor_debug_crash_flags = debug_crash_flags.get(sensor_name) if debug_crash_flags else None
        error_info = None
        try:
            sensor_state = all_sensor_states.get(external_sensor.selector_id)
            if not sensor_state:
                assert external_sensor.default_status == DefaultSensorStatus.RUNNING
                sensor_state = InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.AUTOMATICALLY_RUNNING,
                    SensorInstigatorData(min_interval=external_sensor.min_interval_seconds),
                )
                instance.add_instigator_state(sensor_state)
            elif _is_under_min_interval(sensor_state, external_sensor, now):
                continue

            tick = instance.create_tick(
                TickData(
                    instigator_origin_id=sensor_state.instigator_origin_id,
                    instigator_name=sensor_state.instigator_name,
                    instigator_type=InstigatorType.SENSOR,
                    status=TickStatus.STARTED,
                    timestamp=now.timestamp(),
                    selector_id=external_sensor.selector_id,
                )
            )

            _check_for_debug_crash(sensor_debug_crash_flags, "TICK_CREATED")

            with SensorLaunchContext(external_sensor, tick, instance, logger) as tick_context:
                _check_for_debug_crash(sensor_debug_crash_flags, "TICK_HELD")
                yield from _evaluate_sensor(
                    tick_context,
                    instance,
                    workspace,
                    external_sensor,
                    sensor_state,
                    sensor_debug_crash_flags,
                )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(
                "Sensor daemon caught an error for sensor {sensor_name} : {error_info}".format(
                    sensor_name=external_sensor.name,
                    error_info=error_info.to_string(),
                )
            )
        yield error_info


def _evaluate_sensor(
    context,
    instance,
    workspace,
    external_sensor,
    state,
    sensor_debug_crash_flags=None,
):
    context.logger.info(f"Checking for new runs for sensor: {external_sensor.name}")

    sensor_origin = external_sensor.get_external_origin()
    repository_handle = external_sensor.handle.repository_handle
    repo_location = workspace.get_repository_location(
        sensor_origin.external_repository_origin.repository_location_origin.location_name
    )

    sensor_runtime_data = repo_location.get_external_sensor_execution_data(
        instance,
        repository_handle,
        external_sensor.name,
        state.instigator_data.last_tick_timestamp if state.instigator_data else None,
        state.instigator_data.last_run_key if state.instigator_data else None,
        state.instigator_data.cursor if state.instigator_data else None,
    )

    yield

    assert isinstance(sensor_runtime_data, SensorExecutionData)
    if not sensor_runtime_data.run_requests:
        if sensor_runtime_data.pipeline_run_reactions:
            for pipeline_run_reaction in sensor_runtime_data.pipeline_run_reactions:
                origin_run_id = pipeline_run_reaction.pipeline_run.run_id
                if pipeline_run_reaction.error:
                    context.logger.error(
                        f"Got a reaction request for run {origin_run_id} but execution errorred: {pipeline_run_reaction.error}"
                    )
                    context.update_state(
                        TickStatus.FAILURE,
                        cursor=sensor_runtime_data.cursor,
                        error=pipeline_run_reaction.error,
                    )
                    # Since run status sensors have side effects that we don't want to repeat,
                    # we still want to update the cursor, even though the tick failed
                    context.set_should_update_cursor_on_failure(True)
                else:
                    # Use status from the PipelineRunReaction object if it is from a new enough
                    # version (0.14.4) to be set (the status on the PipelineRun object itself
                    # may have since changed)
                    status = (
                        pipeline_run_reaction.run_status.value
                        if pipeline_run_reaction.run_status
                        else pipeline_run_reaction.pipeline_run.status.value
                    )
                    # log to the original pipeline run
                    message = (
                        f'Sensor "{external_sensor.name}" acted on run status '
                        f"{status} of run {origin_run_id}."
                    )
                    instance.report_engine_event(
                        message=message, pipeline_run=pipeline_run_reaction.pipeline_run
                    )
                    context.logger.info(
                        f"Completed a reaction request for run {origin_run_id}: {message}"
                    )
                    context.update_state(
                        TickStatus.SUCCESS,
                        cursor=sensor_runtime_data.cursor,
                        origin_run_id=origin_run_id,
                    )
        elif sensor_runtime_data.skip_message:
            context.logger.info(
                f"Sensor {external_sensor.name} skipped: {sensor_runtime_data.skip_message}"
            )
            context.update_state(
                TickStatus.SKIPPED,
                skip_reason=sensor_runtime_data.skip_message,
                cursor=sensor_runtime_data.cursor,
            )
        else:
            context.logger.info(f"No run requests returned for {external_sensor.name}, skipping")
            context.update_state(TickStatus.SKIPPED, cursor=sensor_runtime_data.cursor)

        yield
        return

    skipped_runs = []
    existing_runs_by_key = _fetch_existing_runs(
        instance, external_sensor, sensor_runtime_data.run_requests
    )

    for run_request in sensor_runtime_data.run_requests:
        target_data = external_sensor.get_target_data(run_request.job_name)

        pipeline_selector = PipelineSelector(
            location_name=repo_location.name,
            repository_name=sensor_origin.external_repository_origin.repository_name,
            pipeline_name=target_data.pipeline_name,
            solid_selection=target_data.solid_selection,
        )
        external_pipeline = repo_location.get_external_pipeline(pipeline_selector)
        run = _get_or_create_sensor_run(
            context,
            instance,
            repo_location,
            external_sensor,
            external_pipeline,
            run_request,
            target_data,
            existing_runs_by_key,
        )

        if isinstance(run, SkippedSensorRun):
            skipped_runs.append(run)
            context.add_run_info(run_id=None, run_key=run_request.run_key)
            yield
            continue

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_CREATED")

        error_info = None

        try:
            context.logger.info(
                "Launching run for {sensor_name}".format(sensor_name=external_sensor.name)
            )
            instance.submit_run(run.run_id, workspace)
            context.logger.info(
                "Completed launch of run {run_id} for {sensor_name}".format(
                    run_id=run.run_id, sensor_name=external_sensor.name
                )
            )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            context.logger.error(
                f"Run {run.run_id} created successfully but failed to launch: " f"{str(error_info)}"
            )

        yield error_info

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_LAUNCHED")

        context.add_run_info(run_id=run.run_id, run_key=run_request.run_key)

    if skipped_runs:
        run_keys = [skipped.run_key for skipped in skipped_runs]
        skipped_count = len(skipped_runs)
        context.logger.info(
            f"Skipping {skipped_count} {'run' if skipped_count == 1 else 'runs'} for sensor "
            f"{external_sensor.name} already completed with run keys: {seven.json.dumps(run_keys)}"
        )

    if context.run_count:
        context.update_state(TickStatus.SUCCESS, cursor=sensor_runtime_data.cursor)
    else:
        context.update_state(TickStatus.SKIPPED, cursor=sensor_runtime_data.cursor)

    yield


def _is_under_min_interval(state, external_sensor, now):
    if not state.instigator_data:
        return False

    if not state.instigator_data.last_tick_timestamp:
        return False

    if not external_sensor.min_interval_seconds:
        return False

    elapsed = now.timestamp() - state.instigator_data.last_tick_timestamp
    return elapsed < external_sensor.min_interval_seconds


def _fetch_existing_runs(instance, external_sensor, run_requests):
    run_keys = [run_request.run_key for run_request in run_requests if run_request.run_key]

    if not run_keys:
        return {}

    existing_runs = {}

    if instance.supports_bucket_queries:
        runs = instance.get_runs(
            filters=RunsFilter(
                tags=PipelineRun.tags_for_sensor(external_sensor),
            ),
            bucket_by=TagBucket(
                tag_key=RUN_KEY_TAG,
                bucket_limit=1,
                tag_values=run_keys,
            ),
        )
        for run in runs:
            tags = run.tags or {}
            run_key = tags.get(RUN_KEY_TAG)
            existing_runs[run_key] = run
        return existing_runs

    else:
        for run_key in run_keys:
            runs = instance.get_runs(
                filters=RunsFilter(
                    tags=merge_dicts(
                        PipelineRun.tags_for_sensor(external_sensor),
                        {RUN_KEY_TAG: run_key},
                    )
                ),
                limit=1,
            )
            if runs:
                existing_runs[run_key] = runs[0]
    return existing_runs


def _get_or_create_sensor_run(
    context,
    instance: DagsterInstance,
    repo_location,
    external_sensor,
    external_pipeline,
    run_request,
    target_data,
    existing_runs_by_key: Dict[str, PipelineRun],
):

    if not run_request.run_key:
        return _create_sensor_run(
            instance, repo_location, external_sensor, external_pipeline, run_request, target_data
        )

    run = existing_runs_by_key.get(run_request.run_key)

    if run:
        if run.status != PipelineRunStatus.NOT_STARTED:
            # A run already exists and was launched for this run key, but the daemon must have
            # crashed before the tick could be updated
            return SkippedSensorRun(run_key=run_request.run_key, existing_run=run)
        else:
            context.logger.info(
                f"Run {run.run_id} already created with the run key "
                f"`{run_request.run_key}` for {external_sensor.name}"
            )
            return run

    context.logger.info(f"Creating new run for {external_sensor.name}")

    return _create_sensor_run(
        instance, repo_location, external_sensor, external_pipeline, run_request, target_data
    )


def _create_sensor_run(
    instance, repo_location, external_sensor, external_pipeline, run_request, target_data
):
    from dagster.daemon.daemon import get_telemetry_daemon_session_id

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        run_request.run_config,
        target_data.mode,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    pipeline_tags = validate_tags(external_pipeline.tags or {}, allow_reserved_tags=False)
    tags = merge_dicts(
        merge_dicts(pipeline_tags, run_request.tags),
        PipelineRun.tags_for_sensor(external_sensor),
    )
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key

    log_action(
        instance,
        SENSOR_RUN_CREATED,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "SENSOR_NAME_HASH": hash_name(external_sensor.name),
            "pipeline_name_hash": hash_name(external_pipeline.name),
            "repo_hash": hash_name(repo_location.name),
        },
    )

    return instance.create_run(
        pipeline_name=target_data.pipeline_name,
        run_id=None,
        run_config=run_request.run_config,
        mode=target_data.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        status=PipelineRunStatus.NOT_STARTED,
        solid_selection=target_data.solid_selection,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )
