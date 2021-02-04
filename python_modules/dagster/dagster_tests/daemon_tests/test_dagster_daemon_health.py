import time

import pendulum
from dagster import DagsterInvariantViolationError
from dagster.core.test_utils import instance_for_test
from dagster.daemon.controller import (
    DagsterDaemonController,
    all_daemons_healthy,
    all_daemons_live,
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

        assert not all_daemons_healthy(instance, curr_time_seconds=init_time.float_timestamp)
        assert not all_daemons_live(instance, curr_time_seconds=init_time.float_timestamp)

        with DagsterDaemonController(instance) as controller:

            while True:
                now = pendulum.now("UTC")
                if all_daemons_healthy(
                    instance, curr_time_seconds=now.float_timestamp
                ) and all_daemons_live(instance, curr_time_seconds=now.float_timestamp):

                    controller.check_daemons()

                    beyond_tolerated_time = now.float_timestamp + 100

                    assert not all_daemons_healthy(
                        instance, curr_time_seconds=beyond_tolerated_time
                    )
                    assert not all_daemons_live(instance, curr_time_seconds=beyond_tolerated_time)
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for instance to become healthy")

                time.sleep(0.5)


def test_healthy_with_different_daemons():
    with instance_for_test() as instance:
        with DagsterDaemonController(instance):

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

        def run_iteration_error(_):
            iteration_ran["ran"] = True
            raise KeyboardInterrupt
            yield  # pylint: disable=unreachable

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        init_time = pendulum.now("UTC")
        with DagsterDaemonController(instance) as controller:
            while True:
                now = pendulum.now("UTC")

                status = get_daemon_status(
                    instance, SchedulerDaemon.daemon_type(), now.float_timestamp
                )

                if iteration_ran["ran"] and status.healthy:
                    try:
                        controller.check_daemons()  # Should throw since the sensor thread is interrupted
                    except Exception as e:  # pylint: disable=broad-except
                        assert (
                            "Stopping dagster-daemon process since the following threads are no longer sending heartbeats: ['SENSOR']"
                            in str(e)
                        )
                        break
                    else:
                        raise Exception("check_daemons should fail if a thread has died")

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)


def test_error_daemon(monkeypatch):
    with instance_for_test(overrides={}) as instance:
        from dagster.daemon.daemon import SensorDaemon

        def run_iteration_error(_):
            raise DagsterInvariantViolationError("foobar")
            yield  # pylint: disable=unreachable

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        init_time = pendulum.now("UTC")
        with DagsterDaemonController(instance) as controller:
            while True:
                now = pendulum.now("UTC")

                if all_daemons_live(instance):
                    # Despite error, daemon should still be running
                    controller.check_daemons()

                    status = get_daemon_status(
                        instance, SensorDaemon.daemon_type(), now.float_timestamp
                    )

                    assert status.healthy == False
                    assert len(status.last_heartbeat.errors) == 1
                    assert (
                        status.last_heartbeat.errors[0].message.strip()
                        == "dagster.core.errors.DagsterInvariantViolationError: foobar"
                    )
                    assert not all_daemons_healthy(instance, curr_time_seconds=now.float_timestamp)
                    assert all_daemons_live(instance, curr_time_seconds=now.float_timestamp)
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)


def test_multiple_error_daemon(monkeypatch):
    with instance_for_test(overrides={}) as instance:
        from dagster.daemon.daemon import SensorDaemon

        def run_iteration_error(_):
            # ?message stack cls_name cause"
            yield SerializableErrorInfo("foobar", None, None, None)
            yield SerializableErrorInfo("bizbuz", None, None, None)

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)

        init_time = pendulum.now("UTC")

        with DagsterDaemonController(instance) as controller:
            while True:

                now = pendulum.now("UTC")

                if all_daemons_live(instance):

                    # Despite error, daemon should still be running
                    controller.check_daemons()

                    status = get_daemon_status(
                        instance, SensorDaemon.daemon_type(), now.float_timestamp
                    )

                    assert status.healthy == False
                    assert len(status.last_heartbeat.errors) == 2
                    assert status.last_heartbeat.errors[0].message.strip() == "foobar"
                    assert status.last_heartbeat.errors[1].message.strip() == "bizbuz"
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for heartbeat error")

                time.sleep(0.5)


def test_warn_multiple_daemons(capsys):
    from dagster.daemon.daemon import SensorDaemon

    with instance_for_test() as instance:
        init_time = pendulum.now("UTC")

        with DagsterDaemonController(instance):
            while True:
                now = pendulum.now("UTC")

                if all_daemons_live(instance):
                    captured = capsys.readouterr()
                    assert "Taking over from another SENSOR daemon process" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for daemon status")

                time.sleep(0.5)

            capsys.readouterr()

        init_time = pendulum.now("UTC")

        status = get_daemon_status(instance, SensorDaemon.daemon_type(), now.float_timestamp)
        last_heartbeat_time = status.last_heartbeat.timestamp

        # No warning when a second controller starts up again
        with DagsterDaemonController(instance):
            while True:
                now = pendulum.now("UTC")

                status = get_daemon_status(
                    instance, SensorDaemon.daemon_type(), now.float_timestamp
                )

                if status.last_heartbeat and status.last_heartbeat.timestamp != last_heartbeat_time:
                    captured = capsys.readouterr()
                    assert "Taking over from another SENSOR daemon process" not in captured.out
                    break

                if (now - init_time).total_seconds() > 10:
                    raise Exception("timed out waiting for new daemon status")

                time.sleep(0.5)

            status = get_daemon_status(instance, SensorDaemon.daemon_type(), now.float_timestamp)
            last_heartbeat_time = status.last_heartbeat.timestamp

            # Starting up a controller while one is running produces the warning though
            with DagsterDaemonController(instance):
                # Wait for heartbeats while two controllers are running at once and there will
                # be a warning
                init_time = pendulum.now("UTC")

                while True:
                    now = pendulum.now("UTC")

                    captured = capsys.readouterr()
                    if "Taking over from another SENSOR daemon process" in captured.out:
                        break

                    if (now - init_time).total_seconds() > 120:
                        raise Exception("timed out waiting for heartbeats")

                    time.sleep(5)
