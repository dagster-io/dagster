import os
from typing import Callable, List, Optional, Union

import packaging.version

from dagster_buildkite.defines import (
    GCP_CREDS_FILENAME,
    GCP_CREDS_LOCAL_FILE,
    LATEST_DAGSTER_RELEASE,
)
from dagster_buildkite.package_spec import PackageSpec, UnsupportedVersionsFunction
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import BuildkiteQueue
from dagster_buildkite.steps.test_project import test_project_depends_fn
from dagster_buildkite.utils import (
    BuildkiteStep,
    BuildkiteTopLevelStep,
    connect_sibling_docker_container,
    has_helm_changes,
    library_version_from_core_version,
    network_buildkite_container,
)

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
DAGSTER_CURRENT_BRANCH = "current_branch"
EARLIEST_TESTED_RELEASE = "0.12.8"


def build_integration_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    # Shared dependency of some test suites
    steps += PackageSpec(
        os.path.join("integration_tests", "python_modules", "dagster-k8s-test-infra"),
    ).build_steps()

    # test suites
    steps += build_backcompat_suite_steps()
    steps += build_celery_k8s_suite_steps()
    steps += build_k8s_suite_steps()
    steps += build_daemon_suite_steps()
    steps += build_auto_materialize_perf_suite_steps()

    return steps


# ########################
# ##### BACKCOMPAT
# ########################


def build_backcompat_suite_steps() -> List[BuildkiteTopLevelStep]:
    tox_factors = [
        "webserver-latest-release",
        "webserver-earliest-release",
        "user-code-latest-release",
        "user-code-earliest-release",
    ]

    return build_integration_suite_steps(
        os.path.join("integration_tests", "test_suites", "backcompat-test-suite"),
        pytest_extra_cmds=backcompat_extra_cmds,
        pytest_tox_factors=tox_factors,
    )


def backcompat_extra_cmds(_, factor: str) -> List[str]:
    tox_factor_map = {
        "webserver-latest-release": {
            "webserver": LATEST_DAGSTER_RELEASE,
            "user_code": DAGSTER_CURRENT_BRANCH,
        },
        "webserver-earliest-release": {
            "webserver": EARLIEST_TESTED_RELEASE,
            "user_code": DAGSTER_CURRENT_BRANCH,
        },
        "user-code-latest-release": {
            "webserver": DAGSTER_CURRENT_BRANCH,
            "user_code": LATEST_DAGSTER_RELEASE,
        },
        "user-code-earliest-release": {
            "webserver": DAGSTER_CURRENT_BRANCH,
            "user_code": EARLIEST_TESTED_RELEASE,
        },
    }

    release_mapping = tox_factor_map[factor]
    webserver_version = release_mapping["webserver"]
    webserver_library_version = _get_library_version(webserver_version)
    webserver_package = _infer_webserver_package(webserver_version)
    user_code_version = release_mapping["user_code"]
    user_code_library_version = _get_library_version(user_code_version)
    user_code_definitions_file = _infer_user_code_definitions_files(user_code_version)

    return [
        f"export EARLIEST_TESTED_RELEASE={EARLIEST_TESTED_RELEASE}",
        f"export WEBSERVER_PACKAGE={webserver_package}",
        f"export USER_CODE_DEFINITIONS_FILE={user_code_definitions_file}",
        "pushd integration_tests/test_suites/backcompat-test-suite/webserver_service",
        " ".join(
            [
                "./build.sh",
                webserver_version,
                webserver_library_version,
                webserver_package,
                user_code_version,
                user_code_library_version,
                user_code_definitions_file,
            ]
        ),
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        *network_buildkite_container("webserver_service_network"),
        *connect_sibling_docker_container(
            "webserver_service_network",
            "dagster_webserver",
            "BACKCOMPAT_TESTS_WEBSERVER_HOST",
        ),
        "popd",
    ]


def _infer_webserver_package(release: str) -> str:
    """Returns `dagster-webserver` if on source or version >=1.3.14 (first dagster-webserver
    release), `dagit` otherwise.
    """
    if release == "current_branch":
        return "dagster-webserver"
    else:
        version = packaging.version.parse(release)
        return "dagit" if version < packaging.version.Version("1.3.14") else "dagster-webserver"


def _infer_user_code_definitions_files(release: str) -> str:
    """Returns `repo.py` if on source or version >=1.0, `legacy_repo.py` otherwise."""
    if release == "current_branch":
        return "repo.py"
    else:
        version = packaging.version.parse(release)
        return "legacy_repo.py" if version < packaging.version.Version("1.0") else "repo.py"


def _get_library_version(version: str) -> str:
    if version == DAGSTER_CURRENT_BRANCH:
        return DAGSTER_CURRENT_BRANCH
    else:
        return library_version_from_core_version(version)


# ########################
# ##### CELERY K8S
# ########################


def build_celery_k8s_suite_steps() -> List[BuildkiteTopLevelStep]:
    pytest_tox_factors = [
        "-default",
        "-markredis",
    ]
    directory = os.path.join("integration_tests", "test_suites", "celery-k8s-test-suite")
    return build_integration_suite_steps(
        directory,
        pytest_tox_factors,
        queue=BuildkiteQueue.DOCKER,  # crashes on python 3.11/3.12 without additional resources
        always_run_if=has_helm_changes,
        pytest_extra_cmds=celery_k8s_integration_suite_pytest_extra_cmds,
    )


# ########################
# ##### DAEMON
# ########################


def build_daemon_suite_steps():
    pytest_tox_factors = None
    directory = os.path.join("integration_tests", "test_suites", "daemon-test-suite")
    return build_integration_suite_steps(
        directory,
        pytest_tox_factors,
        pytest_extra_cmds=daemon_pytest_extra_cmds,
    )


def build_auto_materialize_perf_suite_steps():
    pytest_tox_factors = None
    directory = os.path.join("integration_tests", "test_suites", "auto_materialize_perf_tests")
    return build_integration_suite_steps(
        directory,
        pytest_tox_factors,
        unsupported_python_versions=[
            version
            for version in AvailablePythonVersion.get_all()
            if version != AvailablePythonVersion.V3_11
        ],
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
    return build_integration_suite_steps(
        directory,
        pytest_tox_factors,
        always_run_if=has_helm_changes,
        pytest_extra_cmds=k8s_integration_suite_pytest_extra_cmds,
    )


# ########################
# ##### UTILITIES
# ########################


def build_integration_suite_steps(
    directory: str,
    pytest_tox_factors: Optional[List[str]],
    pytest_extra_cmds: Optional[Callable] = None,
    queue=None,
    always_run_if: Optional[Callable[[], bool]] = None,
    unsupported_python_versions: Optional[
        Union[List[AvailablePythonVersion], UnsupportedVersionsFunction]
    ] = None,
) -> List[BuildkiteTopLevelStep]:
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
        pytest_extra_cmds=pytest_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
        pytest_tox_factors=pytest_tox_factors,
        retries=2,
        timeout_in_minutes=30,
        queue=queue,
        always_run_if=always_run_if,
        unsupported_python_versions=unsupported_python_versions,
    ).build_steps()


def k8s_integration_suite_pytest_extra_cmds(version: str, _) -> List[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
    ]


def celery_k8s_integration_suite_pytest_extra_cmds(version: str, _) -> List[str]:
    cmds = [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
    ]

    # If integration tests are disabled, we won't have any gcp credentials to download.
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        cmds += [
            rf"aws s3 cp s3://\${{BUILDKITE_SECRETS_BUCKET}}/{GCP_CREDS_FILENAME} "
            + GCP_CREDS_LOCAL_FILE,
            "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
        ]

    cmds += [
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

    return cmds
