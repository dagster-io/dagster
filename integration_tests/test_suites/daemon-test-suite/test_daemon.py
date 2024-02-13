import time

import pendulum
from dagster._core.test_utils import instance_for_test
from dagster._daemon.controller import (
    DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    all_daemons_healthy,
)
from dagster._seven.compat.pendulum import pendulum_freeze_time
from utils import start_daemon


def test_heartbeat():
    with instance_for_test() as instance:
        assert all_daemons_healthy(instance) is False

        with start_daemon(log_level="debug"):
            time.sleep(5)
            assert all_daemons_healthy(instance) is True

        frozen_datetime = pendulum.now().add(
            seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS
            + DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS
            + 5
        )
        with pendulum_freeze_time(frozen_datetime):
            assert all_daemons_healthy(instance) is False
