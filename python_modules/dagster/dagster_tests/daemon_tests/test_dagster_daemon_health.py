import pendulum
from dagster import DagsterInvariantViolationError
from dagster.core.test_utils import instance_for_test
from dagster.daemon.controller import (
    DAEMON_HEARTBEAT_INTERVAL_SECONDS,
    DagsterDaemonController,
    all_daemons_healthy,
    get_daemon_status,
)


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
        beyond_tolerated_time = init_time.float_timestamp + 100

        controller = DagsterDaemonController(instance)
        assert not all_daemons_healthy(instance, curr_time_seconds=init_time.float_timestamp)

        controller.run_iteration(init_time)
        assert all_daemons_healthy(instance, curr_time_seconds=init_time.float_timestamp)

        assert not all_daemons_healthy(instance, curr_time_seconds=beyond_tolerated_time)


def test_healthy_with_different_daemons():
    with instance_for_test() as instance:
        init_time = pendulum.now("UTC")
        controller = DagsterDaemonController(instance)
        controller.run_iteration(init_time)

    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        assert not all_daemons_healthy(instance, curr_time_seconds=init_time.float_timestamp)


def test_error_daemon(monkeypatch):
    with instance_for_test(overrides={}) as instance:
        from dagster.daemon.daemon import SensorDaemon

        def run_iteration_error(_):
            raise DagsterInvariantViolationError("foobar")
            yield  # pylint: disable=unreachable

        monkeypatch.setattr(SensorDaemon, "run_iteration", run_iteration_error)
        controller = DagsterDaemonController(instance)
        init_time = pendulum.now("UTC")
        controller.run_iteration(init_time)

        status = get_daemon_status(instance, SensorDaemon.daemon_type(), init_time.float_timestamp)
        assert status.healthy == False
        assert (
            status.last_heartbeat.error.message.strip()
            == "dagster.core.errors.DagsterInvariantViolationError: foobar"
        )


def test_warn_multiple_daemons(capsys):
    with instance_for_test() as instance:
        init_time = pendulum.now("UTC")
        next_time = init_time.add(seconds=100)

        controller1 = DagsterDaemonController(instance)
        controller1.run_iteration(init_time)
        captured = capsys.readouterr()
        assert "Taking over from another SENSOR daemon process" not in captured.out

        controller2 = DagsterDaemonController(instance)
        controller2.run_iteration(init_time)
        captured = capsys.readouterr()
        assert "Taking over from another SENSOR daemon process" not in captured.out

        controller1.run_iteration(next_time)
        captured = capsys.readouterr()
        assert "Taking over from another SENSOR daemon process" in captured.out
