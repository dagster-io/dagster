# ruff: noqa: T201

import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import docker
import pytest
import requests
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._utils import (
    file_relative_path,
    library_version_from_core_version,
    parse_package_version,
)
from dagster_graphql import DagsterGraphQLClient

DAGSTER_CURRENT_BRANCH = "current_branch"
MAX_TIMEOUT_SECONDS = 20
IS_BUILDKITE = os.getenv("BUILDKITE") is not None
EARLIEST_TESTED_RELEASE = os.getenv("EARLIEST_TESTED_RELEASE")
MOST_RECENT_RELEASE_PLACEHOLDER = "most_recent"

pytest_plugins = ["dagster_test.fixtures"]


# Maps pytest marks to (dagit-version, user-code-version) 2-tuples. These versions are CORE
# versions-- library versions are derived from these later with `get_library_version`.
MARK_TO_VERSIONS_MAP = {
    "dagit-earliest-release": (EARLIEST_TESTED_RELEASE, DAGSTER_CURRENT_BRANCH),
    "user-code-earliest-release": (DAGSTER_CURRENT_BRANCH, EARLIEST_TESTED_RELEASE),
    "dagit-latest-release": (MOST_RECENT_RELEASE_PLACEHOLDER, DAGSTER_CURRENT_BRANCH),
    "user-code-latest-release": (DAGSTER_CURRENT_BRANCH, MOST_RECENT_RELEASE_PLACEHOLDER),
}


def get_library_version(version: str) -> str:
    if version == DAGSTER_CURRENT_BRANCH:
        return DAGSTER_CURRENT_BRANCH
    else:
        return library_version_from_core_version(version)


def assert_run_success(client, run_id):
    start_time = time.time()
    while True:
        if time.time() - start_time > MAX_TIMEOUT_SECONDS:
            raise Exception("Timed out waiting for launched run to complete")

        status = client.get_run_status(run_id)
        assert status and status != DagsterRunStatus.FAILURE
        if status == DagsterRunStatus.SUCCESS:
            break

        time.sleep(1)


@pytest.fixture(name="dagster_most_recent_release", scope="session")
def dagster_most_recent_release():
    res = requests.get("https://pypi.org/pypi/dagster/json")
    module_json = res.json()
    releases = module_json["releases"]
    release_versions = [
        parse_package_version(version)
        for version, files in releases.items()
        if not any(file.get("yanked") for file in files)
    ]
    for release_version in reversed(sorted(release_versions)):
        if not release_version.is_prerelease:
            return str(release_version)


# This yields a dictionary where the keys are "dagit"/"user_code" and the values are either (1) a
# string version (e.g. "1.0.5"); (2) the string "current_branch".
@pytest.fixture(
    params=[
        pytest.param(value, marks=getattr(pytest.mark, key), id=key)
        for key, value in MARK_TO_VERSIONS_MAP.items()
    ],
    scope="session",
)
def release_test_map(request, dagster_most_recent_release):
    dagit_version = request.param[0]
    if dagit_version == MOST_RECENT_RELEASE_PLACEHOLDER:
        dagit_version = dagster_most_recent_release
    user_code_version = request.param[1]
    if user_code_version == MOST_RECENT_RELEASE_PLACEHOLDER:
        user_code_version = dagster_most_recent_release

    return {"dagit": dagit_version, "user_code": user_code_version}


@contextmanager
def docker_service_up(docker_compose_file, build_args=None):
    if IS_BUILDKITE:
        try:
            yield  # buildkite pipeline handles the service
        finally:
            # collect logs from the containers and upload to buildkite
            client = docker.client.from_env()
            containers = client.containers.list()

            current_test = os.environ.get("PYTEST_CURRENT_TEST").split(":")[-1].split(" ")[0]
            logs_dir = f".docker_logs/{current_test}"

            # delete any existing logs
            p = subprocess.Popen(["rm", "-rf", "{dir}".format(dir=logs_dir)])
            p.communicate()
            assert p.returncode == 0

            Path(logs_dir).mkdir(parents=True, exist_ok=True)

            for c in containers:
                with open(
                    "{dir}/{container}-logs.txt".format(dir=logs_dir, container=c.name),
                    "w",
                    encoding="utf8",
                ) as log:
                    p = subprocess.Popen(
                        ["docker", "logs", c.name],
                        stdout=log,
                        stderr=log,
                    )
                    p.communicate()
                    print(f"container({c.name}) logs dumped")
                    if p.returncode != 0:
                        q = subprocess.Popen(
                            ["docker", "logs", c.name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        stdout, stderr = q.communicate()
                        print(f"{c.name} container log dump failed with stdout: ", stdout)
                        print(f"{c.name} container logs dump failed with stderr: ", stderr)

            p = subprocess.Popen(
                [
                    "buildkite-agent",
                    "artifact",
                    "upload",
                    "{dir}/**/*".format(dir=logs_dir),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = p.communicate()
            print("Buildkite artifact added with stdout: ", stdout)
            print("Buildkite artifact added with stderr: ", stderr)
        return

    try:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])
    except subprocess.CalledProcessError:
        pass

    build_process = subprocess.Popen(
        [file_relative_path(docker_compose_file, "./build.sh")] + (build_args if build_args else [])
    )
    build_process.wait()
    assert build_process.returncode == 0

    up_process = subprocess.Popen(["docker-compose", "-f", docker_compose_file, "up", "--no-start"])
    up_process.wait()
    assert up_process.returncode == 0

    start_process = subprocess.Popen(["docker-compose", "-f", docker_compose_file, "start"])
    start_process.wait()
    assert start_process.returncode == 0

    try:
        yield
    finally:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])


@pytest.fixture(scope="session")
def graphql_client(release_test_map, retrying_requests):
    dagit_host = os.environ.get("BACKCOMPAT_TESTS_DAGIT_HOST", "localhost")

    dagit_version = release_test_map["dagit"]
    dagit_library_version = get_library_version(dagit_version)
    user_code_version = release_test_map["user_code"]
    user_code_library_version = get_library_version(user_code_version)

    with docker_service_up(
        os.path.join(os.getcwd(), "dagit_service", "docker-compose.yml"),
        build_args=[
            dagit_version,
            dagit_library_version,
            user_code_version,
            user_code_library_version,
            extract_major_version(user_code_version),
        ],
    ):
        result = retrying_requests.get(f"http://{dagit_host}:3000/dagit_info")
        assert result.json().get("dagit_version")
        yield DagsterGraphQLClient(dagit_host, port_number=3000)


def test_backcompat_deployed_pipeline(graphql_client, release_test_map):
    # Only run this test on legacy versions
    if is_0_release(release_test_map["user_code"]):
        assert_runs_and_exists(graphql_client, "the_pipeline")


def test_backcompat_deployed_pipeline_subset(graphql_client, release_test_map):
    # Only run this test on legacy versions
    if is_0_release(release_test_map["user_code"]):
        assert_runs_and_exists(graphql_client, "the_pipeline", subset_selection=["my_solid"])


def test_backcompat_deployed_job(graphql_client):
    assert_runs_and_exists(graphql_client, "the_job")


def test_backcompat_deployed_job_subset(graphql_client):
    assert_runs_and_exists(graphql_client, "the_job", subset_selection=["my_op"])


def test_backcompat_ping_dagit(graphql_client):
    assert_runs_and_exists(
        graphql_client,
        "test_graphql",
    )


def assert_runs_and_exists(client: DagsterGraphQLClient, name, subset_selection=None):
    run_id = client.submit_pipeline_execution(
        pipeline_name=name,
        mode="default",
        run_config={},
        solid_selection=subset_selection,
    )
    assert_run_success(client, run_id)

    locations = (
        client._get_repo_locations_and_names_with_pipeline(  # pylint: disable=protected-access
            pipeline_name=name
        )
    )
    assert len(locations) == 1
    assert locations[0].pipeline_name == name


def is_0_release(release):
    """Returns true if 0.x.x release of dagster, false otherwise."""
    if release == "current_branch":
        return False
    return release.split(".")[0] == "0"


def extract_major_version(release):
    """Returns major version if 0.x.x release, returns 'current_branch' if master."""
    if release == "current_branch":
        return release
    return release.split(".")[0]
