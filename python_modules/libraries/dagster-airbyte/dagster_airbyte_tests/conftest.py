# pylint: disable=print-call

import os
import subprocess
import time
from datetime import datetime

import pytest
import requests

from dagster._core.test_utils import environ
from dagster._utils import file_relative_path

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture(name="docker_compose_file")
def docker_compose_file_fixture():
    return file_relative_path(__file__, "docker-compose.yml")


@pytest.fixture(name="docker_compose_env_file")
def docker_compose_env_file_fixture():
    return file_relative_path(__file__, "docker-compose.env")


RETRY_DELAY_SEC = 5
STARTUP_TIME_SEC = 120
AIRBYTE_VOLUMES = [
    "airbyte_integration_tests_data",
    "airbyte_integration_tests_db",
    "airbyte_integration_tests_workspace",
]


def _cleanup_docker(docker_compose_file, docker_compose_env_file):
    subprocess.check_output(
        ["docker-compose", "--env-file", docker_compose_env_file, "-f", docker_compose_file, "stop"]
    )
    subprocess.check_output(
        [
            "docker-compose",
            "--env-file",
            docker_compose_env_file,
            "-f",
            docker_compose_file,
            "rm",
            "-f",
        ]
    )
    subprocess.check_output(["docker", "volume", "rm"] + AIRBYTE_VOLUMES)


@pytest.fixture(name="docker_compose_airbyte_instance")
def docker_compose_airbyte_instance_fixture(
    docker_compose_cm, docker_compose_file, docker_compose_env_file
):
    """
    Spins up an Airbyte instance using docker-compose, and tears it down after the test.
    """

    with docker_compose_cm(docker_compose_file, env_file=docker_compose_env_file) as hostnames:

        webapp_host = hostnames["airbyte-webapp"]
        webapp_port = "8000" if webapp_host == "localhost" else "80"

        # Poll Airbyte API until it's ready
        # Healthcheck endpoint is ready before API is ready, so we poll the API
        start_time = datetime.now()
        while True:
            now = datetime.now()
            if (now - start_time).seconds > STARTUP_TIME_SEC:
                raise Exception("Airbyte instance failed to start in time")

            poll_result = None
            try:
                poll_result = requests.post(
                    f"http://{webapp_host}:{webapp_port}/api/v1/workspaces/list",
                    headers={"Content-Type": "application/json"},
                )
                if poll_result.status_code == 200:
                    break
            except requests.exceptions.ConnectionError as e:
                print(e)

            time.sleep(RETRY_DELAY_SEC)
            print(
                f"Waiting for Airbyte instance to start on {webapp_host}"
                + "." * (3 + (now - start_time).seconds // RETRY_DELAY_SEC)
                + (f"\n{poll_result.status_code}: {poll_result.text}" if poll_result else "")
            )

        with environ({"AIRBYTE_HOSTNAME": webapp_host, "AIRBYTE_PORT": webapp_port}):
            yield webapp_host


@pytest.fixture(name="airbyte_source_files")
def airbyte_source_files_fixture():
    FILES = ["sample_file.json"]

    for file in FILES:
        with open(file_relative_path(__file__, file), "r", encoding="utf8") as f:
            contents = f.read()
        with open(os.path.join("/tmp/airbyte_local", file), "w", encoding="utf8") as f:
            f.write(contents)
