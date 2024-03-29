import os
import signal
import subprocess
import tempfile
import time

import requests
import yaml
from dagster import DagsterEventType, DagsterInstance, EventRecordsFilter
from dagster._core.test_utils import environ, new_cwd
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import wait_for_grpc_server
from dagster._utils import find_free_port
from dagster_graphql import DagsterGraphQLClient


def _wait_for_dagit_running(dagit_port):
    start_time = time.time()
    while True:
        try:
            dagit_json = requests.get(f"http://localhost:{dagit_port}/server_info").json()
            if dagit_json:
                return
        except:
            print("Waiting for Dagit to be ready..")  # noqa: T201

        if time.time() - start_time > 30:
            raise Exception("Timed out waiting for Dagit to serve requests")

        time.sleep(1)


def test_dagster_dev_command_workspace():
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": ""}):
            with new_cwd(tempdir):
                dagit_port = find_free_port()
                dev_process = subprocess.Popen(
                    [
                        "dagster",
                        "dev",
                        "-w",
                        os.path.join(
                            os.path.dirname(__file__),
                            "workspace.yaml",
                        ),
                        "--dagit-port",
                        str(dagit_port),
                        "--log-level",
                        "debug",
                    ],
                    cwd=tempdir,
                )
                try:
                    _wait_for_dagit_running(dagit_port)
                finally:
                    dev_process.send_signal(signal.SIGINT)
                    dev_process.communicate()


def test_dagster_dev_command_loads_toys():
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": ""}):
            with new_cwd(tempdir):
                dagit_port = find_free_port()
                dev_process = subprocess.Popen(
                    [
                        "dagster",
                        "dev",
                        "-m",
                        "dagster_test.toys.repo",
                        "--dagit-port",
                        str(dagit_port),
                        "--log-level",
                        "debug",
                    ],
                    cwd=tempdir,
                )
                try:
                    _wait_for_dagit_running(dagit_port)
                finally:
                    dev_process.send_signal(signal.SIGINT)
                    dev_process.communicate()


# E2E test that spins up "dagster dev", accesses dagit,
# and waits for a schedule run to launch
def test_dagster_dev_command_no_dagster_home():
    with tempfile.TemporaryDirectory() as tempdir:
        with environ(
            {
                "DAGSTER_HOME": "",  # unset dagster home
                "CHECK_DAGSTER_DEV": "1",  # trigger target user code to check for DAGSTER_DEV env var
            }
        ):
            with new_cwd(tempdir):
                dagster_yaml = {
                    "run_coordinator": {
                        "module": "dagster.core.run_coordinator",
                        "class": "QueuedRunCoordinator",
                    },
                }
                with open(os.path.join(str(tempdir), "dagster.yaml"), "w") as config_file:
                    yaml.dump(dagster_yaml, config_file)

                dagit_port = find_free_port()

                dev_process = subprocess.Popen(
                    [
                        "dagster",
                        "dev",
                        "-f",
                        os.path.join(
                            os.path.dirname(__file__),
                            "repo.py",
                        ),
                        "--working-directory",
                        os.path.dirname(__file__),
                        "--dagit-port",
                        str(dagit_port),
                        "--dagit-host",
                        "127.0.0.1",
                    ],
                    cwd=tempdir,
                )

                _wait_for_dagit_running(dagit_port)

                instance = None

                try:
                    start_time = time.time()
                    instance_dir = None
                    while True:
                        if time.time() - start_time > 30:
                            raise Exception("Timed out waiting for instance files to exist")
                        subfolders = [
                            name
                            for name in os.listdir(tempdir)
                            if name.startswith("tmp")
                            and os.path.exists(os.path.join(tempdir, name, "history"))
                        ]

                        if len(subfolders):
                            assert len(subfolders) == 1
                            instance_dir = os.path.join(str(tempdir), subfolders[0])
                            break

                        time.sleep(1)

                    with DagsterInstance.from_config(instance_dir) as instance:
                        start_time = time.time()
                        while True:
                            if (
                                len(instance.get_runs()) > 0
                                and len(
                                    instance.get_event_records(
                                        event_records_filter=EventRecordsFilter(
                                            event_type=DagsterEventType.PIPELINE_ENQUEUED
                                        )
                                    )
                                )
                                > 0
                            ):
                                # Verify the run was queued (so the dagster.yaml was applied)
                                break

                            if time.time() - start_time > 30:
                                raise Exception("Timed out waiting for queued run to exist")

                            time.sleep(1)

                finally:
                    dev_process.send_signal(signal.SIGINT)
                    dev_process.communicate()


def test_dagster_dev_command_grpc_port():
    with tempfile.TemporaryDirectory() as tempdir:
        dagit_port = find_free_port()
        grpc_port = find_free_port()

        grpc_process = None
        dev_process = None

        try:
            subprocess_args = [
                "dagster",
                "api",
                "grpc",
                "-f",
                os.path.join(
                    os.path.dirname(__file__),
                    "repo.py",
                ),
                "--working-directory",
                os.path.dirname(__file__),
                "-p",
                str(grpc_port),
            ]
            grpc_process = subprocess.Popen(subprocess_args)

            client = DagsterGrpcClient(port=grpc_port, host="localhost")
            wait_for_grpc_server(grpc_process, client, subprocess_args)
            dev_process = subprocess.Popen(
                [
                    "dagster",
                    "dev",
                    "--dagit-port",
                    str(dagit_port),
                    "--dagit-host",
                    "127.0.0.1",
                    "--grpc-port",
                    str(grpc_port),
                    "--grpc-host",
                    "localhost",
                ],
                cwd=tempdir,
            )
            _wait_for_dagit_running(dagit_port)
            client = DagsterGraphQLClient(hostname="localhost", port_number=dagit_port)
            client.submit_job_execution("foo_job")
        finally:
            if grpc_process:
                grpc_process.send_signal(signal.SIGINT)
                grpc_process.communicate()

            if dev_process:
                dev_process.send_signal(signal.SIGINT)
                dev_process.communicate()
