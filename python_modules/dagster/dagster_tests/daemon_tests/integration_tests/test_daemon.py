import time

from dagster.daemon.controller import all_daemons_healthy

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

        assert all_daemons_healthy(instance) is False

        with start_daemon():
            time.sleep(5)
            assert all_daemons_healthy(instance) is True

        time.sleep(5)
        assert all_daemons_healthy(instance) is False
