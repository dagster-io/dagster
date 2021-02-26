import time

import pendulum
from dagster.daemon.controller import (
    DAEMON_HEARTBEAT_INTERVAL_SECONDS,
    DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    all_daemons_healthy,
)

from .utils import setup_instance, start_daemon


def test_heartbeat(
    tmpdir,
):

    dagster_home_path = tmpdir.strpath
    with setup_instance(dagster_home_path, "") as instance:

        assert all_daemons_healthy(instance) is False

        with start_daemon():
            time.sleep(5)
            assert all_daemons_healthy(instance) is True

        frozen_datetime = pendulum.now().add(
            seconds=DAEMON_HEARTBEAT_INTERVAL_SECONDS + DAEMON_HEARTBEAT_TOLERANCE_SECONDS + 5
        )
        with pendulum.test(frozen_datetime):
            assert all_daemons_healthy(instance) is False
