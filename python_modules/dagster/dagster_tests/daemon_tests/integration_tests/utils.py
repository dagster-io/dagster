import contextlib
import os
import subprocess

from dagster.core.instance import DagsterInstance


@contextlib.contextmanager
def setup_instance(dagster_home, instance_config):
    os.environ["DAGSTER_HOME"] = dagster_home

    with open(os.path.join(dagster_home, "dagster.yaml"), "w") as file:
        file.write(instance_config)

    yield DagsterInstance.get()


@contextlib.contextmanager
def start_daemon():
    p = subprocess.Popen(["dagster-daemon", "run"])
    yield
    p.kill()
