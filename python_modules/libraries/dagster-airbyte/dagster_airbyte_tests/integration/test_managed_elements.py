# ruff: noqa: T201
# pylint: disable=unused-argument

import os
import time
from datetime import datetime
from typing import cast

import mock
import pytest
import requests
import requests_mock
from dagster import AssetKey, materialize
from dagster._core.events import StepMaterializationData
from dagster._core.test_utils import environ
from dagster._utils import file_relative_path
from dagster_airbyte import airbyte_resource, load_assets_from_connections
from dagster_managed_elements import ManagedElementDiff
from dagster_managed_elements.cli import apply, check
from dagster_managed_elements.utils import diff_dicts

from .example_stacks import example_airbyte_stack

TEST_ROOT_DIR = str(file_relative_path(__file__, "./example_stacks"))

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture(name="docker_compose_file", scope="session")
def docker_compose_file_fixture():
    return file_relative_path(__file__, "docker-compose.yml")


@pytest.fixture(name="docker_compose_env_file", scope="session")
def docker_compose_env_file_fixture():
    return file_relative_path(__file__, "docker-compose.env")


RETRY_DELAY_SEC = 5
STARTUP_TIME_SEC = 120


@pytest.fixture(name="docker_compose_airbyte_instance", scope="module")
def docker_compose_airbyte_instance_fixture(
    docker_compose_cm,
    docker_compose_file,
    docker_compose_env_file,
):
    """Spins up an Airbyte instance using docker-compose, and tears it down after the test."""
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


@pytest.fixture(name="track_make_requests")
def track_make_requests_fixture():
    with requests_mock.mock(real_http=True) as m:
        yield m


@pytest.fixture(name="empty_airbyte_instance")
def empty_airbyte_instance_fixture(docker_compose_airbyte_instance):
    """Ensures that the docker-compose Airbyte instance is empty before running a test."""
    apply(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler")

    yield docker_compose_airbyte_instance

    apply(TEST_ROOT_DIR, "empty_airbyte_stack:reconciler")


@pytest.fixture(name="airbyte_source_files")
def airbyte_source_files_fixture():
    FILES = ["sample_file.json", "different_sample_file.json"]

    for file in FILES:
        with open(file_relative_path(__file__, file), "r", encoding="utf8") as f:
            contents = f.read()
        with open(os.path.join("/tmp/airbyte_local", file), "w", encoding="utf8") as f:
            f.write(contents)


def _calls_to(rm: requests_mock.Mocker, url_suffix: str) -> int:
    return len([call for call in rm.request_history if call.url.endswith(url_suffix)])


@pytest.mark.parametrize("filename", ["example_airbyte_stack", "example_airbyte_stack_generated"])
def test_basic_integration(
    empty_airbyte_instance,
    airbyte_source_files,
    filename,
    track_make_requests: requests_mock.Mocker,
):
    ab_instance = airbyte_resource.configured(
        {
            "host": os.getenv("AIRBYTE_HOSTNAME", "localhost"),
            "port": os.getenv("AIRBYTE_PORT", "80"),
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
    check_result = check(TEST_ROOT_DIR, f"{filename}:reconciler")

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
                "my_data_stream": {"syncMode": "full_refresh", "destinationSyncMode": "append"}
            },
            "destination namespace": "SAME_AS_SOURCE",
            "prefix": None,
        },
    }
    expected_result = diff_dicts(
        config_dict,
        None,
    )

    assert expected_result == check_result
    assert _calls_to(track_make_requests, "/sources/create") == 0

    # Then, apply the diff and check that we get the expected diff again

    apply_result = apply(TEST_ROOT_DIR, f"{filename}:reconciler")

    assert expected_result == apply_result
    assert _calls_to(track_make_requests, "/sources/create") == 1

    # Now, check that we get no diff after applying the stack

    check_result = check(TEST_ROOT_DIR, f"{filename}:reconciler")

    assert check_result == ManagedElementDiff()

    # Test that we can load assets from connections
    ab_assets = ab_cacheable_assets.build_definitions(ab_cacheable_assets.compute_cacheable_data())

    tables = {"my_data_stream"}
    assert ab_assets[0].keys == {AssetKey(t) for t in tables}

    res = materialize(ab_assets)

    materializations = [
        cast(StepMaterializationData, event.event_specific_data).materialization
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


def test_change_source_and_destination(
    empty_airbyte_instance,
    airbyte_source_files,
    track_make_requests: requests_mock.Mocker,
):
    # Set up example element and ensure no diff and initial call counts are correct
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert _calls_to(track_make_requests, "/sources/update") == 0
    assert _calls_to(track_make_requests, "/destinations/update") == 0
    assert _calls_to(track_make_requests, "/sources/create") == 1
    assert _calls_to(track_make_requests, "/destinations/create") == 1

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
    assert _calls_to(track_make_requests, "/sources/update") == 1
    assert _calls_to(track_make_requests, "/sources/create") == 1

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_source")
    assert check_result == ManagedElementDiff()
    assert _calls_to(track_make_requests, "/sources/create") == 1

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

    # Apply new destination config, ensure that we get the proper diff and that the call count
    # stays the same since we are just reconfiguring the same destination type
    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
    assert apply_result == expected_diff
    assert _calls_to(track_make_requests, "/destinations/create") == 1
    assert _calls_to(track_make_requests, "/destinations/update") > 0

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
    assert check_result == ManagedElementDiff()
    assert _calls_to(track_make_requests, "/sources/create") == 1

    # Try new destination type, same name, which forces recreation, incrementing the call count
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_csv")
    assert _calls_to(track_make_requests, "/destinations/create") == 2


def test_mark_secrets_as_changed(docker_compose_airbyte_instance, airbyte_source_files):
    # First, apply a stack and check that there's no diff after applying it
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert ManagedElementDiff() == check_result

    # Ensure that a different config has a diff
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
    other_check_result = check(
        TEST_ROOT_DIR,
        "example_airbyte_stack:reconciler_different_dest",
        include_all_secrets=True,
    )
    assert other_check_result == check_result
    assert ManagedElementDiff() != check_result

    # Next, mock to treat all config as secrets - now, we don't expect a diff
    # because we ignore all the config fields which have changed
    with mock.patch(
        "dagster_airbyte.managed.reconciliation._ignore_secrets_compare_fn", return_value=True
    ):
        check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
        assert ManagedElementDiff() == check_result

        check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_different_dest")
        assert ManagedElementDiff() == check_result

        # This reconciler has mark_secrets_as_changed set to True, so we expect a diff
        check_result = check(
            TEST_ROOT_DIR,
            "example_airbyte_stack:reconciler_different_dest",
            include_all_secrets=True,
        )
        assert ManagedElementDiff() != check_result


def test_change_destination_namespace(empty_airbyte_instance, airbyte_source_files):
    # Set up example element and ensure no diff
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert check_result == ManagedElementDiff()

    # Change the destination namespace, ensure that we get the proper diff
    expected_diff = diff_dicts(
        {
            "local-json-conn": {
                "destination namespace": "DESTINATION_DEFAULT",
            },
        },
        {
            "local-json-conn": {
                "destination namespace": "SAME_AS_SOURCE",
            },
        },
    )
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_dest_default")
    assert check_result == expected_diff

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_dest_default")
    assert apply_result == expected_diff

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_dest_default")
    assert check_result == ManagedElementDiff()

    # Reset to original state
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert check_result == ManagedElementDiff()

    # Change the destination namespace, ensure that we get the proper diff
    expected_diff = diff_dicts(
        {
            "local-json-conn": {
                "destination namespace": "my-cool-namespace",
            },
        },
        {
            "local-json-conn": {
                "destination namespace": "SAME_AS_SOURCE",
            },
        },
    )
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_namespace")
    assert check_result == expected_diff

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_namespace")
    assert apply_result == expected_diff

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_namespace")
    assert check_result == ManagedElementDiff()


def test_change_destination_prefix(empty_airbyte_instance, airbyte_source_files):
    # Set up example element and ensure no diff
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert check_result == ManagedElementDiff()

    # Change the destination prefix, ensure that we get the proper diff
    expected_diff = diff_dicts(
        {
            "local-json-conn": {
                "prefix": "my_prefix",
            },
        },
        {
            "local-json-conn": {
                "prefix": None,
            },
        },
    )
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_prefix")
    assert check_result == expected_diff

    apply_result = apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_prefix")
    assert apply_result == expected_diff

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_custom_prefix")
    assert check_result == ManagedElementDiff()


def test_sync_modes(docker_compose_airbyte_instance, airbyte_source_files):
    # First, apply a stack and check that there's no diff after applying it
    apply(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")

    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler")
    assert ManagedElementDiff() == check_result

    # Ensure that a different config has a diff
    check_result = check(TEST_ROOT_DIR, "example_airbyte_stack:reconciler_alt_sync_mode")

    config_dict = {
        "local-json-conn": {
            "streams": {
                "my_data_stream": {
                    "syncMode": "incremental",
                    "cursorField": ["foo"],
                }
            },
        },
    }
    dest_dict = {
        "local-json-conn": {
            "streams": {
                "my_data_stream": {
                    "syncMode": "full_refresh",
                    "cursorField": [],
                }
            },
        },
    }
    expected_result = diff_dicts(
        config_dict,
        dest_dict,
    )

    assert check_result == expected_result
