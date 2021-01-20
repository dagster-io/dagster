import contextlib
import os

from dagster import seven
from dagster.core.instance import DagsterInstance
from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess


@contextlib.contextmanager
def setup_instance(dagster_home, instance_config):
    os.environ["DAGSTER_HOME"] = dagster_home

    with open(os.path.join(dagster_home, "dagster.yaml"), "w") as file:
        file.write(instance_config)

    with DagsterInstance.get() as instance:
        yield instance


@contextlib.contextmanager
def start_daemon():
    p = open_ipc_subprocess(["dagster-daemon", "run"])
    try:
        yield
    finally:
        interrupt_ipc_subprocess(p)
        seven.wait_for_process(p)
