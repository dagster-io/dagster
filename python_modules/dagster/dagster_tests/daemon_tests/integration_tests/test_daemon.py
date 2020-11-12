import time

from .utils import setup_instance, start_daemon


def test_heartbeat(tmpdir,):

    dagster_home_path = tmpdir.strpath
    with setup_instance(
        dagster_home_path,
        """run_coordinator:
    module: dagster.core.run_coordinator
    class: QueuedRunCoordinator
    config:
        dequeue_interval_seconds: 1
    """,
    ) as instance:

        assert instance.daemon_healthy() is False

        with start_daemon():
            time.sleep(2)
            assert instance.daemon_healthy() is True

        time.sleep(6)
        assert instance.daemon_healthy() is False
