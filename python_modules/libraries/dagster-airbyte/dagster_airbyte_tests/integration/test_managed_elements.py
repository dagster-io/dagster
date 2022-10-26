# pylint: disable=unused-argument,print-call

import os
import subprocess
import time
from datetime import datetime

import pytest
import requests
from dagster_airbyte import airbyte_resource, load_assets_from_connections
from dagster_managed_elements import ManagedElementDiff
from dagster_managed_elements.cli import apply, check
from dagster_managed_elements.utils import diff_dicts

from dagster import AssetKey, materialize
from dagster._core.test_utils import environ
from dagster._utils import file_relative_path

TEST_ROOT_DIR = str(file_relative_path(__file__, "./example_stacks"))
from .example_stacks import example_airbyte_stack

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
    FILES = ["sample_file.json", "different_sample_file.json"]

    for file in FILES:
        with open(file_relative_path(__file__, file), "r", encoding="utf8") as f:
            contents = f.read()
        with open(os.path.join("/tmp/airbyte_local", file), "w", encoding="utf8") as f:
            f.write(contents)


def test_basic_integration(docker_compose_airbyte_instance, airbyte_source_files):

    ab_instance = airbyte_resource.configured(
        {
            "host": os.getenv("AIRBYTE_HOSTNAME"),
            "port": os.getenv("AIRBYTE_PORT"),
        }
    )
    ab_cacheable_assets = load_assets_from_connections(
        ab_instance, [example_airbyte_stack.local_json_conn]
    )

    with pytest.raises(ValueError):
        # Cannot load assets from connections because they haven't been created yet
        ab_assets = ab_cacheable_assets.build_definitions(
            ab_cacheable_assets.compute_cacheable_data()
        )

    # First, check that we get the expected diff
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    config_dict = {
        "local-json-input": {
            "url": "/local/sample_file.json",
            "format": "json",
            "provider": {"storage": "local"},
            "dataset_name": "my_data_stream",
        },
        "local-json-output": {
            "destination_path": "/local/destination_file.json",
        },
        "local-json-conn": {
            "source": "local-json-input",
            "destination": "local-json-output",
            "normalize data": False,
            "streams": {
                "my_data_stream": "FULL_REFRESH_APPEND",
            },
        },
    }
    expected_result = diff_dicts(
        config_dict,
        None,
    )

    assert expected_result == check_result

    # Then, apply the diff and check that we get the expected diff again

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    assert expected_result == apply_result

    # Now, check that we get no diff after applying the stack

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    assert check_result == ManagedElementDiff()

    # Test that we can load assets from connections
    ab_assets = ab_cacheable_assets.build_definitions(ab_cacheable_assets.compute_cacheable_data())

    tables = {"my_data_stream"}
    assert ab_assets[0].keys == {AssetKey(t) for t in tables}

    res = materialize(ab_assets)

    materializations = [
        event.event_specific_data.materialization
        for event in res.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == len(tables)
    assert {m.asset_key for m in materializations} == {AssetKey(t) for t in tables}

    # Ensure that the empty stack w/o delete has no diff (it will not try to delete resources it
    # doesn't know about)
    check_result = check(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler_no_delete")

    # Inverted result (e.g. all deletions)
    expected_result = ManagedElementDiff()

    # Now, we try to remove everything
    check_result = check(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler")

    # Inverted result (e.g. all deletions)
    expected_result = diff_dicts(
        None,
        config_dict,
    )

    assert expected_result == check_result

    # Then, apply the diff to remove everything and check that we get the expected diff again

    apply_result = apply(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler")

    assert expected_result == apply_result

    # Now, check that we get no diff after applying the stack

    check_result = check(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler")

    assert check_result == ManagedElementDiff()

    with pytest.raises(ValueError):
        # Cannot load assets from connections because they have been deleted
        ab_assets = ab_cacheable_assets.build_definitions(
            ab_cacheable_assets.compute_cacheable_data()
        )


def test_change_source_and_destination(docker_compose_airbyte_instance, airbyte_source_files):

    # Set up example element and ensure no diff
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert check_result == ManagedElementDiff()

    # Change the source, ensure that we get the proper diff
    expected_diff = diff_dicts(
        {
            "local-json-input": {
                "url": "/local/different_sample_file.json",
            },
        },
        {
            "local-json-input": {
                "url": "/local/sample_file.json",
            },
        },
    )
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_source")
    assert check_result == expected_diff

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_source")
    assert apply_result == expected_diff

    # Return to original state
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    # Change the destination, ensure that we get the proper diff
    expected_diff = diff_dicts(
        {
            "local-json-output": {
                "destination_path": "/local/different_destination_file.json",
            },
        },
        {
            "local-json-output": {
                "destination_path": "/local/destination_file.json",
            },
        },
    )

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
    assert check_result == expected_diff

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
    assert apply_result == expected_diff
