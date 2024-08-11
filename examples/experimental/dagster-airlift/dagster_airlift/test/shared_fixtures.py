import os
import signal
import subprocess
import time
from typing import Any, Generator

import pytest
import requests
from dagster._time import get_current_timestamp


def airflow_is_ready():
    try:
        response = requests.get("http://localhost:8080")
        return response.status_code == 200
    except:
        return False


# Setup should have set AIRFLOW_HOME env var
@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(setup: None) -> Generator[Any, None, None]:
    process = subprocess.Popen(
        ["airflow", "standalone"],
        env=os.environ,  # since we have some temp vars in the env right now
        shell=False,
        preexec_fn=os.setsid,  # noqa  # fuck it we ball
    )
    # Give airflow a second to stand up
    time.sleep(5)
    initial_time = get_current_timestamp()

    airflow_ready = False
    while get_current_timestamp() - initial_time < 60:
        if airflow_is_ready():
            airflow_ready = True
            break
        time.sleep(1)

    assert airflow_ready, "Airflow did not start within 30 seconds..."
    yield process
    # Kill process group, since process.kill and process.terminate do not work.
    os.killpg(process.pid, signal.SIGKILL)
