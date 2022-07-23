import os
from typing import Callable, List, Optional

from ..defines import GCP_CREDS_LOCAL_FILE, LATEST_DAGSTER_RELEASE
from ..package_spec import PackageSpec
from ..python_version import AvailablePythonVersion
from ..utils import (
    BuildkiteStep,
    GroupStep,
    connect_sibling_docker_container,
    network_buildkite_container,
)
from .test_project import test_project_depends_fn

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
DAGSTER_CURRENT_BRANCH = "current_branch"
EARLIEST_TESTED_RELEASE = "0.12.8"


def build_integration_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    # Shared dependency of some test suites
    steps += PackageSpec(
        os.path.join("integration_tests", "python_modules", "dagster-k8s-test-infra"),
        upload_coverage=True,
    ).build_steps()

    # test suites
    steps += build_backcompat_suite_steps()
    steps += build_celery_k8s_suite_steps()
    steps += build_k8s_suite_steps()
    steps += build_daemon_suite_steps()

    return steps


# ########################
# ##### BACKCOMPAT
# ########################


def build_backcompat_suite_steps() -> List[GroupStep]:

    tox_factors = [
        "dagit-latest-release",
        "dagit-earliest-release",
        "user-code-latest-release",
        "user-code-earliest-release",
    ]

    return build_integration_suite_steps(
        os.path.join("integration_tests", "test_suites", "backcompat-test-suite"),
        pytest_extra_cmds=backcompat_extra_cmds,
        pytest_tox_factors=tox_factors,
        upload_coverage=False,
    )


def backcompat_extra_cmds(_, factor: str) -> List[str]:

    tox_factor_map = {
        "dagit-latest-release": {
            "dagit": LATEST_DAGSTER_RELEASE,
            "user_code": DAGSTER_CURRENT_BRANCH,
        },
        "dagit-earliest-release": {
            "dagit": EARLIEST_TESTED_RELEASE,
            "user_code": DAGSTER_CURRENT_BRANCH,
        },
        "user-code-latest-release": {
            "dagit": DAGSTER_CURRENT_BRANCH,
            "user_code": LATEST_DAGSTER_RELEASE,
        },
        "user-code-earliest-release": {
            "dagit": DAGSTER_CURRENT_BRANCH,
            "user_code": EARLIEST_TESTED_RELEASE,
        },
    }

    release_mapping = tox_factor_map[factor]
    dagit_version = release_mapping["dagit"]
    user_code_version = release_mapping["user_code"]

    return [
        f"export EARLIEST_TESTED_RELEASE={EARLIEST_TESTED_RELEASE}",
        "pushd integration_tests/test_suites/backcompat-test-suite/dagit_service",
        f"./build.sh {dagit_version} {user_code_version}",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        *network_buildkite_container("dagit_service_network"),
        *connect_sibling_docker_container(
            "dagit_service_network",
            "dagit",
            "BACKCOMPAT_TESTS_DAGIT_HOST",
        ),
        "popd",
    ]


# ########################
# ##### CELERY K8S
# ########################


def build_celery_k8s_suite_steps() -> List[GroupStep]:
    pytest_tox_factors = [
        "-default",
        "-markusercodedeploymentsubchart",
        "-markdaemon",
        "-markredis",
        "-markmonitoring",
    ]
    directory = os.path.join("integration_tests", "test_suites", "celery-k8s-test-suite")
    return build_integration_suite_steps(directory, pytest_tox_factors, upload_coverage=True)


# ########################
# ##### DAEMON
# ########################


def build_daemon_suite_steps():
    pytest_tox_factors = None
    directory = os.path.join("integration_tests", "test_suites", "daemon-test-suite")
    return build_integration_suite_steps(
        directory,
        pytest_tox_factors,
        upload_coverage=False,
        pytest_extra_cmds=daemon_pytest_extra_cmds,
    )


def daemon_pytest_extra_cmds(version: AvailablePythonVersion, _):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "pushd integration_tests/test_suites/daemon-test-suite/monitoring_daemon_tests/",
        "docker-compose up -d --remove-orphans",
        *network_buildkite_container("postgres"),
        *connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-docker",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


# ########################
# ##### K8S
# ########################


def build_k8s_suite_steps():
    pytest_tox_factors = ["-default", "-subchart"]
    directory = os.path.join("integration_tests", "test_suites", "k8s-test-suite")
    return build_integration_suite_steps(directory, pytest_tox_factors, upload_coverage=True)


# ########################
# ##### UTILITIES
# ########################


def build_integration_suite_steps(
    directory: str,
    pytest_tox_factors: Optional[List[str]],
    upload_coverage: bool,
    pytest_extra_cmds: Optional[Callable] = None,
    queue=None,
) -> List[GroupStep]:
    pytest_extra_cmds = pytest_extra_cmds or default_integration_suite_pytest_extra_cmds
    return PackageSpec(
        directory,
        env_vars=[
            "AIRFLOW_HOME",
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
        upload_coverage=upload_coverage,
        pytest_extra_cmds=pytest_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
        pytest_tox_factors=pytest_tox_factors,
        retries=2,
        timeout_in_minutes=30,
        queue=queue,
    ).build_steps()


def default_integration_suite_pytest_extra_cmds(version: str, _) -> List[str]:
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        *network_buildkite_container("rabbitmq"),
        *connect_sibling_docker_container(
            "rabbitmq", "test-rabbitmq", "DAGSTER_CELERY_BROKER_HOST"
        ),
        "popd",
    ]
