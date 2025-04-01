import time
from datetime import timedelta

import pytest
from dagster import DagsterInvariantViolationError
from dagster._core.test_utils import environ, freeze_time, instance_for_test
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon.controller import (
    DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DEFAULT_WORKSPACE_FRESHNESS_TOLERANCE,
    RELOAD_WORKSPACE_INTERVAL,
    all_daemons_healthy,
    all_daemons_live,
    daemon_controller_from_instance,
    get_daemon_statuses,
)
from dagster._time import get_current_datetime
from dagster._utils.error import SerializableErrorInfo


def test_healthy():
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster._core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        init_time = get_current_datetime()

        heartbeat_interval_seconds = 1

        assert not all_daemons_healthy(
            instance,
            curr_time_seconds=init_time.timestamp(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
        assert not all_daemons_live(
            instance,
            curr_time_seconds=init_time.timestamp(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )

        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        ) as controller:
            while True:
                now = get_current_datetime()
                if all_daemons_healthy(
                    instance,
                    curr_time_seconds=now.timestamp(),
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                ) and all_daemons_live(
                    instance,
                    curr_time_seconds=now.timestamp(),
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                ):
                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    beyond_tolerated_time = (
                        now.timestamp() + DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS + 1
                    )

                    assert not all_daemons_healthy(
                        instance,
                        curr_time_seconds=beyond_tolerated_time,
                        heartbeat_interval_seconds=heartbeat_interval_seconds,
                    )
                    assert not all_daemons_live(
                        instance,
                        curr_time_seconds=beyond_tolerated_time,
                        heartbeat_interval_seconds=heartbeat_interval_seconds,
                    )
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for instance to become healthy")

                time.sleep(0.5)


def test_healthy_with_different_daemons():
    with instance_for_test() as instance:
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ):
            with instance_for_test(
                overrides={
                    "run_coordinator": {
                        "module": "dagster._core.run_coordinator.queued_run_coordinator",
                        "class": "QueuedRunCoordinator",
                    },
                }
            ) as other_instance:
                now = get_current_datetime()
                assert not all_daemons_healthy(other_instance, curr_time_seconds=now.timestamp())
                assert not all_daemons_live(other_instance, curr_time_seconds=now.timestamp())


def test_thread_die_daemon(monkeypatch):
    with instance_for_test(overrides={}) as instance:
        from dagster._daemon.daemon import SchedulerDaemon, SensorDaemon

        iteration_ran = {"ran": False}

        def run_loop_error(_, _ctx, _shutdown_event):
            iteration_ran["ran"] = True
            raise KeyboardInterrupt
            yield

        monkeypatch.setattr(SensorDaemon, "core_loop", run_loop_error)

        heartbeat_interval_seconds = 1

        init_time = get_current_datetime()
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        ) as controller:
            while True:
                now = get_current_datetime()

                status = get_daemon_statuses(
                    instance,
                    [SchedulerDaemon.daemon_type()],
                    now.timestamp(),
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )[SchedulerDaemon.daemon_type()]

                if iteration_ran["ran"] and status.healthy:
                    try:
                        controller.check_daemon_threads()  # Should eventually throw since the sensor thread is interrupted
                    except Exception as e:
                        assert (
                            "Stopped dagster-daemon process due to threads no longer running"
                            in str(e)
                        )
                        break

                if (now - init_time).total_seconds() > 20:
                    raise Exception("timed out waiting for check_daemons to fail")

                time.sleep(0.5)


def test_transient_heartbeat_failure(mocker, caplog):
    with instance_for_test() as instance:
        mocker.patch(
            "dagster.daemon.controller.get_daemon_statuses",
            side_effect=Exception("Transient heartbeat failure"),
        )

        heartbeat_interval_seconds = 1
        heartbeat_tolerance_seconds = 5

        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
        ) as controller:
            controller.check_daemon_heartbeats()  # doesn't immediately fail despite transient error

            time.sleep(2 * heartbeat_tolerance_seconds)

            assert not any(
                "The following threads have not sent heartbeats in more than 5 seconds"
                in str(record)
                for record in caplog.records
            )

            controller.check_daemon_heartbeats()

            assert any(
                "The following threads have not sent heartbeats in more than 5 seconds"
                in str(record)
                for record in caplog.records
            )


def test_error_daemon(monkeypatch):
    with instance_for_test() as instance:
        from dagster._daemon.daemon import SensorDaemon

        should_raise_errors = True

        error_count = {"count": 0}

        def run_loop_error(_, _ctx, _shutdown_event):
            if should_raise_errors:
                time.sleep(0.5)
                error_count["count"] = error_count["count"] + 1
                raise DagsterInvariantViolationError("foobar:" + str(error_count["count"]))

            while True:
                yield
                time.sleep(0.5)

        def _get_error_number(error):
            error_message = error.message.strip()
            return int(error_message.split("foobar:")[1])

        monkeypatch.setattr(SensorDaemon, "core_loop", run_loop_error)

        heartbeat_interval_seconds = 1

        gen_daemons = lambda instance: [SensorDaemon(instance.get_sensor_settings())]

        init_time = get_current_datetime()
        with environ({"DAGSTER_DAEMON_CORE_LOOP_EXCEPTION_SLEEP_INTERVAL": "1"}):
            with daemon_controller_from_instance(
                instance,
                workspace_load_target=EmptyWorkspaceTarget(),
                heartbeat_interval_seconds=heartbeat_interval_seconds,
                gen_daemons=gen_daemons,
                error_interval_seconds=10,
            ) as controller:
                while True:
                    now = get_current_datetime()

                    if get_daemon_statuses(
                        instance,
                        [SensorDaemon.daemon_type()],
                        heartbeat_interval_seconds=heartbeat_interval_seconds,
                        ignore_errors=True,
                    )[SensorDaemon.daemon_type()].healthy:
                        # Despite error, daemon should still be running
                        controller.check_daemon_threads()
                        controller.check_daemon_heartbeats()

                        status = get_daemon_statuses(
                            instance,
                            [SensorDaemon.daemon_type()],
                            now.timestamp(),
                            heartbeat_interval_seconds=heartbeat_interval_seconds,
                        )[SensorDaemon.daemon_type()]

                        # Errors build up until there are > 5, then pull off the last
                        if status.healthy is False and len(status.last_heartbeat.errors) >= 5:  # pyright: ignore[reportArgumentType,reportOptionalMemberAccess]
                            first_error_number = _get_error_number(status.last_heartbeat.errors[0])  # pyright: ignore[reportOptionalSubscript,reportOptionalMemberAccess]

                            if first_error_number > 5:
                                # Verify error numbers decrease consecutively
                                assert [
                                    _get_error_number(error)
                                    for error in status.last_heartbeat.errors  # pyright: ignore[reportOptionalIterable,reportOptionalMemberAccess]
                                ] == list(range(first_error_number, first_error_number - 5, -1))

                                assert not get_daemon_statuses(
                                    instance,
                                    [SensorDaemon.daemon_type()],
                                    curr_time_seconds=now.timestamp(),
                                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                                )[SensorDaemon.daemon_type()].healthy
                                assert get_daemon_statuses(
                                    instance,
                                    [SensorDaemon.daemon_type()],
                                    curr_time_seconds=now.timestamp(),
                                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                                    ignore_errors=True,
                                )[SensorDaemon.daemon_type()].healthy

                                time.sleep(3)

                                status = get_daemon_statuses(
                                    instance,
                                    [SensorDaemon.daemon_type()],
                                    now.timestamp(),
                                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                                )[SensorDaemon.daemon_type()]

                                # Error count does not rise above 5, continues to increase
                                assert len(status.last_heartbeat.errors) == 5  # pyright: ignore[reportArgumentType,reportOptionalMemberAccess]

                                new_first_error_number = _get_error_number(
                                    status.last_heartbeat.errors[0]  # pyright: ignore[reportOptionalSubscript,reportOptionalMemberAccess]
                                )

                                assert new_first_error_number > first_error_number

                                break

                    if (now - init_time).total_seconds() > 15:
                        raise Exception("timed out waiting for heartbeat error")

                    time.sleep(0.5)

                # Once the sensor no longer raises errors, they should return to 0 once
                # enough time passes
                should_raise_errors = False
                init_time = get_current_datetime()

                while True:
                    now = get_current_datetime()

                    status = get_daemon_statuses(
                        instance,
                        [SensorDaemon.daemon_type()],
                        now.timestamp(),
                        heartbeat_interval_seconds=heartbeat_interval_seconds,
                    )[SensorDaemon.daemon_type()]

                    # Error count does not rise above 5
                    if len(status.last_heartbeat.errors) == 0:  # pyright: ignore[reportArgumentType,reportOptionalMemberAccess]
                        break

                    if (now - init_time).total_seconds() > 15:
                        raise Exception("timed out waiting for hearrteat errors to return to 0")

                    time.sleep(0.5)


def test_multiple_error_daemon(monkeypatch):
    with instance_for_test() as instance:
        from dagster._daemon.daemon import SensorDaemon

        def run_loop_error(_, _ctx, _shutdown_event):
            # ?message stack cls_name cause"
            yield SerializableErrorInfo("foobar", None, None, None)  # pyright: ignore[reportArgumentType]
            yield SerializableErrorInfo("bizbuz", None, None, None)  # pyright: ignore[reportArgumentType]

            while True:
                yield
                time.sleep(0.5)

        monkeypatch.setattr(SensorDaemon, "core_loop", run_loop_error)

        init_time = get_current_datetime()

        heartbeat_interval_seconds = 1

        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        ) as controller:
            while True:
                now = get_current_datetime()

                if all_daemons_live(
                    instance, heartbeat_interval_seconds=heartbeat_interval_seconds
                ):
                    # Despite error, daemon should still be running
                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    status = get_daemon_statuses(
                        instance, [SensorDaemon.daemon_type()], now.timestamp()
                    )[SensorDaemon.daemon_type()]

                    if status.healthy is False and len(status.last_heartbeat.errors) == 2:  # pyright: ignore[reportArgumentType,reportOptionalMemberAccess]
                        assert status.last_heartbeat.errors[0].message.strip() == "bizbuz"  # pyright: ignore[reportOptionalSubscript,reportOptionalMemberAccess]
                        assert status.last_heartbeat.errors[1].message.strip() == "foobar"  # pyright: ignore[reportOptionalSubscript,reportOptionalMemberAccess]
                        break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)


def test_warn_multiple_daemons(capsys):
    from dagster._daemon.daemon import SensorDaemon

    with instance_for_test() as instance:
        init_time = get_current_datetime()

        heartbeat_interval_seconds = 1

        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        ):
            while True:
                now = get_current_datetime()

                if all_daemons_live(
                    instance, heartbeat_interval_seconds=heartbeat_interval_seconds
                ):
                    captured = capsys.readouterr()
                    assert "Another SENSOR daemon is still sending heartbeats" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for daemon status")

                time.sleep(0.5)

            capsys.readouterr()

        init_time = get_current_datetime()

        status = get_daemon_statuses(
            instance,
            [SensorDaemon.daemon_type()],
            now.timestamp(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )[SensorDaemon.daemon_type()]
        last_heartbeat_time = status.last_heartbeat.timestamp  # pyright: ignore[reportOptionalMemberAccess]

        # No warning when a second controller starts up again
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        ):
            while True:
                now = get_current_datetime()

                status = get_daemon_statuses(
                    instance,
                    [SensorDaemon.daemon_type()],
                    now.timestamp(),
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )[SensorDaemon.daemon_type()]

                if status.last_heartbeat and status.last_heartbeat.timestamp != last_heartbeat_time:
                    captured = capsys.readouterr()
                    assert "Another SENSOR daemon is still sending heartbeats" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for new daemon status")

                time.sleep(0.5)

            status = get_daemon_statuses(
                instance,
                [SensorDaemon.daemon_type()],
                now.timestamp(),
                heartbeat_interval_seconds=heartbeat_interval_seconds,
            )[SensorDaemon.daemon_type()]
            last_heartbeat_time = status.last_heartbeat.timestamp  # pyright: ignore[reportOptionalMemberAccess]

            # Starting up a controller while one is running produces the warning though
            with daemon_controller_from_instance(
                instance,
                workspace_load_target=EmptyWorkspaceTarget(),
                heartbeat_interval_seconds=heartbeat_interval_seconds,
            ):
                # Wait for heartbeats while two controllers are running at once and there will
                # be a warning
                init_time = get_current_datetime()

                while True:
                    now = get_current_datetime()

                    captured = capsys.readouterr()
                    if "Another SENSOR daemon is still sending heartbeats" in captured.out:
                        break

                    if (now - init_time).total_seconds() > 60:
                        raise Exception("timed out waiting for heartbeats")

                    time.sleep(5)


def test_workspace_refresh_failed(monkeypatch, caplog):
    with instance_for_test() as instance:
        from dagster._core.workspace.context import WorkspaceProcessContext

        def refresh_failure(_):
            raise Exception("Failed to load a location")

        monkeypatch.setattr(WorkspaceProcessContext, "refresh_workspace", refresh_failure)

        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ) as controller:
            last_workspace_update_time = get_current_datetime()

            controller.check_workspace_freshness(last_workspace_update_time.timestamp())
            # doesn't try to refresh yet
            assert not any(
                "Daemon controller failed to refresh workspace." in str(record)
                for record in caplog.records
            )

            with freeze_time(
                last_workspace_update_time + timedelta(seconds=(RELOAD_WORKSPACE_INTERVAL + 1)),
            ):
                controller.check_workspace_freshness(last_workspace_update_time.timestamp())
                # refresh fails, it logs but doesn't throw
                assert any(
                    "Daemon controller failed to refresh workspace." in str(record)
                    for record in caplog.records
                )

            with freeze_time(
                last_workspace_update_time
                + timedelta(seconds=(DEFAULT_WORKSPACE_FRESHNESS_TOLERANCE + 1)),
            ):
                # now it throws
                with pytest.raises(Exception, match="Failed to load a location"):
                    controller.check_workspace_freshness(last_workspace_update_time.timestamp())
