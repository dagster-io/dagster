import time

import pendulum
import pytest
from dagster import DagsterInvariantViolationError
from dagster.core.test_utils import instance_for_test
from dagster.daemon.controller import (
    DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    all_daemons_healthy,
    all_daemons_live,
    daemon_controller_from_instance,
    get_daemon_status,
)
from dagster.utils.error import SerializableErrorInfo


def test_healthy():

    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        init_time = pendulum.now("UTC")

        heartbeat_interval_seconds = 1

        assert not all_daemons_healthy(
            instance,
            curr_time_seconds=init_time.float_timestamp,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
        assert not all_daemons_live(
            instance,
            curr_time_seconds=init_time.float_timestamp,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )

        with daemon_controller_from_instance(
            instance, heartbeat_interval_seconds=heartbeat_interval_seconds
        ) as controller:

            while True:
                now = pendulum.now("UTC")
                if all_daemons_healthy(
                    instance,
                    curr_time_seconds=now.float_timestamp,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                ) and all_daemons_live(
                    instance,
                    curr_time_seconds=now.float_timestamp,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                ):

                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    beyond_tolerated_time = (
                        now.float_timestamp + DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS + 1
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
        with daemon_controller_from_instance(instance):

            with instance_for_test(
                overrides={
                    "run_coordinator": {
                        "module": "dagster.core.run_coordinator.queued_run_coordinator",
                        "class": "QueuedRunCoordinator",
                    },
                }
            ) as other_instance:
                now = pendulum.now("UTC")
                assert not all_daemons_healthy(
                    other_instance, curr_time_seconds=now.float_timestamp
                )
                assert not all_daemons_live(other_instance, curr_time_seconds=now.float_timestamp)


def test_thread_die_daemon(monkeypatch):
    with instance_for_test(overrides={}) as instance:
        from dagster.daemon.daemon import SchedulerDaemon, SensorDaemon

        iteration_ran = {"ran": False}

        def run_iteration_error(_, _instance, _workspace):
            iteration_ran["ran"] = True
            raise KeyboardInterrupt
            yield  # pylint: disable=unreachable

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        heartbeat_interval_seconds = 1

        init_time = pendulum.now("UTC")
        with daemon_controller_from_instance(
            instance, heartbeat_interval_seconds=heartbeat_interval_seconds
        ) as controller:
            while True:
                now = pendulum.now("UTC")

                status = get_daemon_status(
                    instance,
                    SchedulerDaemon.daemon_type(),
                    now.float_timestamp,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )

                if iteration_ran["ran"] and status.healthy:
                    try:
                        controller.check_daemon_threads()  # Should eventually throw since the sensor thread is interrupted
                    except Exception as e:  # pylint: disable=broad-except
                        assert (
                            "Stopping dagster-daemon process since the following threads are no longer running: ['SENSOR']"
                            in str(e)
                        )
                        break

                if (now - init_time).total_seconds() > 20:
                    raise Exception("timed out waiting for check_daemons to fail")

                time.sleep(0.5)


def test_transient_heartbeat_failure(mocker):
    with instance_for_test() as instance:
        mocker.patch(
            "dagster.daemon.controller.get_daemon_status",
            side_effect=Exception("Transient heartbeat failure"),
        )

        heartbeat_interval_seconds = 1
        heartbeat_tolerance_seconds = 5

        with daemon_controller_from_instance(
            instance,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
        ) as controller:
            controller.check_daemon_heartbeats()  # doesn't immediately fail despite transient error

            time.sleep(2 * heartbeat_tolerance_seconds)

            with pytest.raises(
                Exception,
                match="Stopping dagster-daemon process since the following threads are no longer sending heartbeats",
            ):
                controller.check_daemon_heartbeats()


def test_error_daemon(monkeypatch):
    with instance_for_test() as instance:
        from dagster.daemon.daemon import SensorDaemon

        should_raise_errors = True

        error_count = {"count": 0}

        def run_iteration_error(_, _instance, _workspace):
            if should_raise_errors:
                error_count["count"] = error_count["count"] + 1
                raise DagsterInvariantViolationError("foobar:" + str(error_count["count"]))
            yield

        def _get_error_number(error):
            error_message = error.message.strip()
            return int(error_message.split("foobar:")[1])

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        heartbeat_interval_seconds = 1

        gen_daemons = lambda instance: [SensorDaemon(interval_seconds=1)]

        init_time = pendulum.now("UTC")
        with daemon_controller_from_instance(
            instance,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            gen_daemons=gen_daemons,
            error_interval_seconds=10,
        ) as controller:
            while True:
                now = pendulum.now("UTC")

                if get_daemon_status(
                    instance,
                    SensorDaemon.daemon_type(),
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                    ignore_errors=True,
                ).healthy:
                    # Despite error, daemon should still be running
                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    status = get_daemon_status(
                        instance,
                        SensorDaemon.daemon_type(),
                        now.float_timestamp,
                        heartbeat_interval_seconds=heartbeat_interval_seconds,
                    )

                    assert status.healthy == False

                    # Errors build up until there are > 5, then pull off the last
                    if len(status.last_heartbeat.errors) >= 5:

                        first_error_number = _get_error_number(status.last_heartbeat.errors[0])

                        if first_error_number > 5:

                            # Verify error numbers decrease consecutively
                            assert [
                                _get_error_number(error) for error in status.last_heartbeat.errors
                            ] == list(range(first_error_number, first_error_number - 5, -1))

                            assert not get_daemon_status(
                                instance,
                                SensorDaemon.daemon_type(),
                                curr_time_seconds=now.float_timestamp,
                                heartbeat_interval_seconds=heartbeat_interval_seconds,
                            ).healthy
                            assert get_daemon_status(
                                instance,
                                SensorDaemon.daemon_type(),
                                curr_time_seconds=now.float_timestamp,
                                heartbeat_interval_seconds=heartbeat_interval_seconds,
                                ignore_errors=True,
                            ).healthy

                            time.sleep(3)

                            status = get_daemon_status(
                                instance,
                                SensorDaemon.daemon_type(),
                                now.float_timestamp,
                                heartbeat_interval_seconds=heartbeat_interval_seconds,
                            )

                            # Error count does not rise above 5, continues to increase
                            assert len(status.last_heartbeat.errors) == 5

                            new_first_error_number = _get_error_number(
                                status.last_heartbeat.errors[0]
                            )

                            assert new_first_error_number > first_error_number

                            break

                if (now - init_time).total_seconds() > 15:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)

            # Once the sensor no longer raises errors, they should return to 0 once
            # enough time passes
            should_raise_errors = False
            init_time = pendulum.now("UTC")

            while True:
                now = pendulum.now("UTC")

                status = get_daemon_status(
                    instance,
                    SensorDaemon.daemon_type(),
                    now.float_timestamp,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )

                # Error count does not rise above 5
                if len(status.last_heartbeat.errors) == 0:
                    break

                if (now - init_time).total_seconds() > 15:
                    raise Exception("timed out waiting for hearrteat errors to return to 0")

                time.sleep(0.5)


def test_multiple_error_daemon(monkeypatch):
    with instance_for_test() as instance:
        from dagster.daemon.daemon import SensorDaemon

        def run_iteration_error(_, _instance, _workspace):
            # ?message stack cls_name cause"
            yield SerializableErrorInfo("foobar", None, None, None)
            yield SerializableErrorInfo("bizbuz", None, None, None)

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        init_time = pendulum.now("UTC")

        heartbeat_interval_seconds = 1

        with daemon_controller_from_instance(
            instance, heartbeat_interval_seconds=heartbeat_interval_seconds
        ) as controller:
            while True:

                now = pendulum.now("UTC")

                if all_daemons_live(
                    instance, heartbeat_interval_seconds=heartbeat_interval_seconds
                ):

                    # Despite error, daemon should still be running
                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    status = get_daemon_status(
                        instance, SensorDaemon.daemon_type(), now.float_timestamp
                    )

                    if status.healthy == False and len(status.last_heartbeat.errors) == 2:
                        assert status.last_heartbeat.errors[0].message.strip() == "bizbuz"
                        assert status.last_heartbeat.errors[1].message.strip() == "foobar"
                        break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)


def test_warn_multiple_daemons(capsys):
    from dagster.daemon.daemon import SensorDaemon

    with instance_for_test() as instance:
        init_time = pendulum.now("UTC")

        heartbeat_interval_seconds = 1

        with daemon_controller_from_instance(
            instance, heartbeat_interval_seconds=heartbeat_interval_seconds
        ):
            while True:
                now = pendulum.now("UTC")

                if all_daemons_live(
                    instance, heartbeat_interval_seconds=heartbeat_interval_seconds
                ):
                    captured = capsys.readouterr()
                    assert "Taking over from another SENSOR daemon process" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for daemon status")

                time.sleep(0.5)

            capsys.readouterr()

        init_time = pendulum.now("UTC")

        status = get_daemon_status(
            instance,
            SensorDaemon.daemon_type(),
            now.float_timestamp,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
        last_heartbeat_time = status.last_heartbeat.timestamp

        # No warning when a second controller starts up again
        with daemon_controller_from_instance(
            instance, heartbeat_interval_seconds=heartbeat_interval_seconds
        ):
            while True:
                now = pendulum.now("UTC")

                status = get_daemon_status(
                    instance,
                    SensorDaemon.daemon_type(),
                    now.float_timestamp,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )

                if status.last_heartbeat and status.last_heartbeat.timestamp != last_heartbeat_time:
                    captured = capsys.readouterr()
                    assert "Taking over from another SENSOR daemon process" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for new daemon status")

                time.sleep(0.5)

            status = get_daemon_status(
                instance,
                SensorDaemon.daemon_type(),
                now.float_timestamp,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
            )
            last_heartbeat_time = status.last_heartbeat.timestamp

            # Starting up a controller while one is running produces the warning though
            with daemon_controller_from_instance(
                instance, heartbeat_interval_seconds=heartbeat_interval_seconds
            ):
                # Wait for heartbeats while two controllers are running at once and there will
                # be a warning
                init_time = pendulum.now("UTC")

                while True:
                    now = pendulum.now("UTC")

                    captured = capsys.readouterr()
                    if "Taking over from another SENSOR daemon process" in captured.out:
                        break

                    if (now - init_time).total_seconds() > 60:
                        raise Exception("timed out waiting for heartbeats")

                    time.sleep(5)
