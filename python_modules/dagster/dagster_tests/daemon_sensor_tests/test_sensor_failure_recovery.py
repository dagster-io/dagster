import multiprocessing

import pendulum
import pytest

from dagster._core.definitions.run_request import InstigatorType
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._core.storage.tags import RUN_KEY_TAG, SENSOR_NAME_TAG
from dagster._core.test_utils import (
    SingleThreadPoolExecutor,
    cleanup_test_instance,
    create_test_daemon_workspace_context,
    get_crash_signals,
    wait_for_futures,
)
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.sensor import execute_sensor_iteration
from dagster._seven import IS_WINDOWS
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_sensor_run import wait_for_all_runs_to_start, workspace_load_target

spawn_ctx = multiprocessing.get_context("spawn")


def _test_launch_sensor_runs_in_subprocess(instance_ref, execution_datetime, debug_crash_flags):
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            with pendulum.test(execution_datetime), create_test_daemon_workspace_context(
                workspace_load_target=workspace_load_target(),
                instance=instance,
            ) as workspace_context:
                logger = get_default_daemon_logger("SensorDaemon")
                futures = {}
                list(
                    execute_sensor_iteration(
                        workspace_context,
                        logger,
                        threadpool_executor=SingleThreadPoolExecutor(),
                        debug_crash_flags=debug_crash_flags,
                        sensor_tick_futures=futures,
                    )
                )
                wait_for_futures(futures)
        finally:
            cleanup_test_instance(instance)


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_location", ["TICK_CREATED", "TICK_HELD"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_before_run_created(crash_location, crash_signal, instance, external_repo):
    frozen_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, hour=0, minute=0, second=1, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(frozen_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        # create a tick
        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime, None],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SKIPPED

        # create a starting tick, but crash
        debug_crash_flags = {external_sensor.name: {crash_location: crash_signal}}
        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime.add(seconds=31), debug_crash_flags],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode != 0

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2
        assert ticks[0].status == TickStatus.STARTED
        assert not int(ticks[0].timestamp) % 2  # skip condition for simple_sensor
        assert instance.get_runs_count() == 0

        # create another tick, but ensure that the last evaluation time used is from the first,
        # successful tick rather than the failed tick
        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime.add(seconds=62), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode == 0
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 1

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 3
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_location", ["RUN_CREATED"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_after_run_created_before_run_launched(
    crash_location, crash_signal, instance, external_repo
):
    frozen_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, hour=0, minute=0, second=0, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(frozen_datetime):
        external_sensor = external_repo.get_external_sensor("run_key_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        # create a starting tick, but crash
        debug_crash_flags = {external_sensor.name: {crash_location: crash_signal}}
        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode != 0

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.STARTED
        assert instance.get_runs_count() == 1

        run = instance.get_runs()[0]
        # Run was created, but hasn't launched yet
        assert run.status == PipelineRunStatus.NOT_STARTED
        assert run.tags.get(SENSOR_NAME_TAG) == "run_key_sensor"
        assert run.tags.get(RUN_KEY_TAG) == "only_once"

        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime.add(seconds=31), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode == 0
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_location", ["RUN_LAUNCHED"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_after_run_launched(crash_location, crash_signal, instance, external_repo):
    frozen_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=28,
            hour=0,
            minute=0,
            second=0,
            tz="UTC",
        ),
        "US/Central",
    )
    with pendulum.test(frozen_datetime):
        external_sensor = external_repo.get_external_sensor("run_key_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        # create a run, launch but crash
        debug_crash_flags = {external_sensor.name: {crash_location: crash_signal}}
        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode != 0

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.STARTED
        assert instance.get_runs_count() == 1

        run = instance.get_runs()[0]
        wait_for_all_runs_to_start(instance)
        assert run.tags.get(SENSOR_NAME_TAG) == "run_key_sensor"
        assert run.tags.get(RUN_KEY_TAG) == "only_once"

        launch_process = spawn_ctx.Process(
            target=_test_launch_sensor_runs_in_subprocess,
            args=[instance.get_ref(), frozen_datetime.add(seconds=31), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)

        assert launch_process.exitcode == 0
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2
        assert ticks[0].status == TickStatus.SKIPPED
