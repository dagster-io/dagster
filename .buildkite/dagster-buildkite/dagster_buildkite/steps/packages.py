import os
from glob import glob
from typing import List, Optional

from dagster_buildkite.defines import GCP_CREDS_LOCAL_FILE, GIT_REPO_ROOT
from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.steps.test_project import test_project_depends_fn
from dagster_buildkite.utils import (
    BuildkiteStep,
    connect_sibling_docker_container,
    network_buildkite_container,
)


def build_example_packages_steps() -> List[BuildkiteStep]:
    custom_example_pkg_roots = [pkg.directory for pkg in EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG]
    example_packages_with_standard_config = [
        PackageSpec(pkg)
        for pkg in (
            _get_uncustomized_pkg_roots("examples", custom_example_pkg_roots)
            + _get_uncustomized_pkg_roots("examples/experimental", custom_example_pkg_roots)
        )
    ]

    example_packages = EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG + example_packages_with_standard_config

    return _build_steps_from_package_specs(example_packages)


def build_library_packages_steps() -> List[BuildkiteStep]:
    custom_library_pkg_roots = [pkg.directory for pkg in LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG]
    library_packages_with_standard_config = [
        *[
            PackageSpec(pkg)
            for pkg in _get_uncustomized_pkg_roots("python_modules", custom_library_pkg_roots)
        ],
        *[
            PackageSpec(pkg)
            for pkg in _get_uncustomized_pkg_roots(
                "python_modules/libraries", custom_library_pkg_roots
            )
        ],
    ]

    return _build_steps_from_package_specs(
        LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG + library_packages_with_standard_config
    )


def build_dagit_screenshot_steps() -> List[BuildkiteStep]:
    return _build_steps_from_package_specs([PackageSpec("docs/dagit-screenshot", run_pytest=False)])


def _build_steps_from_package_specs(package_specs: List[PackageSpec]) -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []
    all_packages = sorted(
        package_specs,
        key=lambda p: f"{_PACKAGE_TYPE_ORDER.index(p.package_type)} {p.name}",  # type: ignore[arg-type]
    )

    for pkg in all_packages:
        steps += pkg.build_steps()

    return steps


_PACKAGE_TYPE_ORDER = ["core", "extension", "example", "infrastructure", "unknown"]


# Find packages under a root subdirectory that are not configured above.
def _get_uncustomized_pkg_roots(root, custom_pkg_roots) -> List[str]:
    all_files_in_root = [
        os.path.relpath(p, GIT_REPO_ROOT) for p in glob(os.path.join(GIT_REPO_ROOT, root, "*"))
    ]
    return [
        p for p in all_files_in_root if p not in custom_pkg_roots and os.path.exists(f"{p}/tox.ini")
    ]


# ########################
# ##### PACKAGES WITH CUSTOM STEPS
# ########################


def airflow_extra_cmds(version: str, _) -> List[str]:
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
    ]


airline_demo_extra_cmds = [
    "pushd examples/airline_demo",
    # Run the postgres db. We are in docker running docker
    # so this will be a sibling container.
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
    # Can't use host networking on buildkite and communicate via localhost
    # between these sibling containers, so pass along the ip.
    *network_buildkite_container("postgres"),
    *connect_sibling_docker_container(
        "postgres", "test-postgres-db-airline", "POSTGRES_TEST_DB_HOST"
    ),
    "popd",
]


def dagster_graphql_extra_cmds(_, tox_factor: Optional[str]) -> List[str]:
    if tox_factor and tox_factor.startswith("postgres"):
        return [
            "pushd python_modules/dagster-graphql/dagster_graphql_tests/graphql/",
            "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
            # Can't use host networking on buildkite and communicate via localhost
            # between these sibling containers, so pass along the ip.
            *network_buildkite_container("postgres"),
            *connect_sibling_docker_container(
                "postgres", "test-postgres-db-graphql", "POSTGRES_TEST_DB_HOST"
            ),
            "popd",
        ]
    else:
        return []


docs_snippets_extra_cmds = [
    "pushd examples/docs_snippets",
    # Run the postgres db. We are in docker running docker
    # so this will be a sibling container.
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
    # Can't use host networking on buildkite and communicate via localhost
    # between these sibling containers, so pass along the ip.
    *network_buildkite_container("postgres"),
    *connect_sibling_docker_container(
        "postgres", "test-postgres-db-docs-snippets", "POSTGRES_TEST_DB_HOST"
    ),
    "popd",
]


deploy_docker_example_extra_cmds = [
    "pushd examples/deploy_docker/from_source",
    "./build.sh",
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
    *network_buildkite_container("docker_example_network"),
    *connect_sibling_docker_container(
        "docker_example_network",
        "docker_example_webserver",
        "DEPLOY_DOCKER_WEBSERVER_HOST",
    ),
    "popd",
]


def celery_extra_cmds(version: str, _) -> List[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
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


def celery_docker_extra_cmds(version: str, _) -> List[str]:
    return celery_extra_cmds(version, _) + [
        "pushd python_modules/libraries/dagster-celery-docker/dagster_celery_docker_tests/",
        "docker-compose up -d --remove-orphans",
        *network_buildkite_container("postgres"),
        *connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-celery-docker",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


def docker_extra_cmds(version: str, _) -> List[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "pushd python_modules/libraries/dagster-docker/dagster_docker_tests/",
        "docker-compose up -d --remove-orphans",
        *network_buildkite_container("postgres"),
        *connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-docker",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


ui_extra_cmds = ["make rebuild_ui"]


mysql_extra_cmds = [
    "pushd python_modules/libraries/dagster-mysql/dagster_mysql_tests/",
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
    *network_buildkite_container("mysql"),
    *network_buildkite_container("mysql_pinned"),
    *network_buildkite_container("mysql_pinned_backcompat"),
    *connect_sibling_docker_container("mysql", "test-mysql-db", "MYSQL_TEST_DB_HOST"),
    *connect_sibling_docker_container(
        "mysql_pinned", "test-mysql-db-pinned", "MYSQL_TEST_PINNED_DB_HOST"
    ),
    *connect_sibling_docker_container(
        "mysql_pinned_backcompat",
        "test-mysql-db-pinned-backcompat",
        "MYSQL_TEST_PINNED_BACKCOMPAT_DB_HOST",
    ),
    "popd",
]


def k8s_extra_cmds(version: str, _) -> List[str]:
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
    ]


gcp_extra_cmds = (
    [
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
    ]
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS")
    else []
)


postgres_extra_cmds = [
    "pushd python_modules/libraries/dagster-postgres/dagster_postgres_tests/",
    "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
    "docker-compose -f docker-compose-multi.yml up -d",  # clean up in hooks/pre-exit,
    *network_buildkite_container("postgres"),
    *connect_sibling_docker_container("postgres", "test-postgres-db", "POSTGRES_TEST_DB_HOST"),
    *network_buildkite_container("postgres_multi"),
    *connect_sibling_docker_container(
        "postgres_multi",
        "test-run-storage-db",
        "POSTGRES_TEST_RUN_STORAGE_DB_HOST",
    ),
    *connect_sibling_docker_container(
        "postgres_multi",
        "test-event-log-storage-db",
        "POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST",
    ),
    "popd",
]


# Some Dagster packages have more involved test configs or support only certain Python version;
# special-case those here
EXAMPLE_PACKAGES_WITH_CUSTOM_CONFIG: List[PackageSpec] = [
    PackageSpec(
        "examples/with_airflow",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_9,
            AvailablePythonVersion.V3_10,
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/assets_smoke_test",
    ),
    PackageSpec(
        "examples/deploy_docker",
        pytest_extra_cmds=deploy_docker_example_extra_cmds,
    ),
    PackageSpec(
        "examples/docs_snippets",
        pytest_extra_cmds=docs_snippets_extra_cmds,
        unsupported_python_versions=[
            # dependency on 3.9-incompatible extension libs
            AvailablePythonVersion.V3_9,
            # depends on some packages not yet available on python 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/project_fully_featured",
        unsupported_python_versions=[
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/with_great_expectations",
        unsupported_python_versions=[
            # Issue with pinned of great_expectations
            AvailablePythonVersion.V3_10,
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/with_pyspark",
        unsupported_python_versions=[
            # pyspark not yet 3.11 compatible
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/with_pyspark_emr",
        unsupported_python_versions=[
            # pyspark not yet 3.11 compatible
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "examples/with_wandb",
        unsupported_python_versions=[
            # wandb not yet 3.11 compatible
            AvailablePythonVersion.V3_11,
        ],
    ),
    # The 6 tutorials referenced in cloud onboarding cant test "source" due to dagster-cloud dep
    PackageSpec(
        "examples/assets_modern_data_stack",
        pytest_tox_factors=["pypi"],
    ),
    PackageSpec(
        "examples/assets_dbt_python",
        pytest_tox_factors=["pypi"],
    ),
    PackageSpec(
        "examples/quickstart_aws",
        pytest_tox_factors=["pypi"],
    ),
    PackageSpec(
        "examples/quickstart_etl",
        pytest_tox_factors=["pypi"],
    ),
    PackageSpec(
        "examples/quickstart_gcp",
        pytest_tox_factors=["pypi"],
    ),
    PackageSpec(
        "examples/quickstart_snowflake",
        pytest_tox_factors=["pypi"],
    ),
]

LIBRARY_PACKAGES_WITH_CUSTOM_CONFIG: List[PackageSpec] = [
    PackageSpec("python_modules/automation"),
    PackageSpec("python_modules/dagster-webserver", pytest_extra_cmds=ui_extra_cmds),
    PackageSpec(
        "python_modules/dagster",
        env_vars=["AWS_ACCOUNT_ID"],
        pytest_tox_factors=[
            "api_tests",
            "cli_tests",
            "core_tests_pydantic1",
            "core_tests_pydantic2",
            "storage_tests_sqlalchemy_1_3",
            "storage_tests_sqlalchemy_1_4",
            "daemon_sensor_tests",
            "daemon_tests",
            "definitions_tests_old_pendulum",
            "general_tests",
            "general_tests_old_protobuf",
            "scheduler_tests",
            "scheduler_tests_old_pendulum",
            "execution_tests",
            "storage_tests",
            "type_signature_tests",
            "definitions_tests",
            "asset_defs_tests",
            "launcher_tests",
            "logging_tests",
        ],
        unsupported_python_versions=(
            lambda tox_factor: (
                [AvailablePythonVersion.V3_11]
                if (
                    tox_factor
                    in {
                        "general_tests_old_protobuf",  # protobuf 3 not compatible with python 3.11
                        "cli_tests",  # test suite prone to hangs on unpinned grpcio version due to https://github.com/grpc/grpc/issues/31885
                    }
                )
                else []
            )
        ),
    ),
    PackageSpec(
        "python_modules/dagster-graphql",
        pytest_extra_cmds=dagster_graphql_extra_cmds,
        pytest_tox_factors=[
            "not_graphql_context_test_suite",
            "sqlite_instance_multi_location",
            "sqlite_instance_managed_grpc_env",
            "sqlite_instance_deployed_grpc_env",
            "sqlite_instance_code_server_cli_grpc_env",
            "graphql_python_client",
            "postgres-graphql_context_variants",
            "postgres-instance_multi_location",
            "postgres-instance_managed_grpc_env",
            "postgres-instance_deployed_grpc_env",
        ],
        unsupported_python_versions=(
            lambda tox_factor: (
                [AvailablePythonVersion.V3_11]
                if (
                    tox_factor
                    in {
                        # test suites particularly likely to crash and/or hang
                        # due to https://github.com/grpc/grpc/issues/31885
                        "sqlite_instance_managed_grpc_env",
                        "sqlite_instance_deployed_grpc_env",
                        "sqlite_instance_code_server_cli_grpc_env",
                        "sqlite_instance_multi_location",
                        "postgres-instance_multi_location",
                        "postgres-instance_managed_grpc_env",
                        "postgres-instance_deployed_grpc_env",
                    }
                )
                else []
            )
        ),
        timeout_in_minutes=30,
    ),
    PackageSpec(
        "python_modules/dagster-test",
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dbt",
        unsupported_python_versions=lambda tox_factor: (
            [
                AvailablePythonVersion.V3_11,
            ]
            if tox_factor == "dbt_13X"
            else []
        ),
        pytest_tox_factors=[
            "dbt_13X_legacy",
            "dbt_14X_legacy",
            "dbt_15X_legacy",
            "dbt_16X_legacy",
            "dbt_13X",
            "dbt_14X",
            "dbt_15X",
            "dbt_16X",
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airbyte",
        pytest_tox_factors=["unit", "integration"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-airflow",
        # omit python 3.10 until we add support
        unsupported_python_versions=[
            AvailablePythonVersion.V3_10,
            AvailablePythonVersion.V3_11,
        ],
        env_vars=[
            "AIRFLOW_HOME",
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
        pytest_extra_cmds=airflow_extra_cmds,
        pytest_tox_factors=[
            "default-airflow1",
            "localdb-airflow1",
            "persistentdb-airflow1",
            "default-airflow2",
            "localdb-airflow2",
            "persistentdb-airflow2",
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-aws",
        env_vars=["AWS_DEFAULT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-azure",
        env_vars=["AZURE_STORAGE_ACCOUNT_KEY"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-celery",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=celery_extra_cmds,
        unsupported_python_versions=[
            AvailablePythonVersion.V3_11,  # no celery support for 3.11
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-celery-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=celery_docker_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
        unsupported_python_versions=[
            AvailablePythonVersion.V3_11,  # no celery support for 3.11
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-dask",
        env_vars=["AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-databricks",
        unsupported_python_versions=[
            # pyspark not supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        pytest_extra_cmds=docker_extra_cmds,
        pytest_step_dependencies=test_project_depends_fn,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-duckdb-pyspark",
        unsupported_python_versions=[
            # pyspark not supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_extra_cmds,
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp-pandas",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_extra_cmds,
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-gcp-pyspark",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        pytest_extra_cmds=gcp_extra_cmds,
        unsupported_python_versions=[
            # pyspark not supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-ge",
        unsupported_python_versions=[
            # great-expectations not yet supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-k8s",
        env_vars=[
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
        ],
        pytest_tox_factors=[
            "default",
            "old_kubernetes",
        ],
        pytest_extra_cmds=k8s_extra_cmds,
    ),
    PackageSpec(
        "python_modules/libraries/dagster-mlflow",
        unsupported_python_versions=[
            # https://github.com/mlflow/mlflow/issues/7681
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-mysql",
        pytest_extra_cmds=mysql_extra_cmds,
        unsupported_python_versions=[
            # mysql-connector-python not supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake-pandas",
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_BUILDKITE_PASSWORD"],
    ),
    PackageSpec(
        "python_modules/libraries/dagster-snowflake-pyspark",
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_BUILDKITE_PASSWORD"],
        unsupported_python_versions=[
            # pyspark not supported on 3.11
            AvailablePythonVersion.V3_11,
        ],
    ),
    PackageSpec("python_modules/libraries/dagster-postgres", pytest_extra_cmds=postgres_extra_cmds),
    PackageSpec(
        "python_modules/libraries/dagster-twilio",
        env_vars=["TWILIO_TEST_ACCOUNT_SID", "TWILIO_TEST_AUTH_TOKEN"],
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    PackageSpec(
        "python_modules/libraries/dagstermill",
        pytest_tox_factors=["papermill1", "papermill2"],
        retries=2,  # Workaround for flaky kernel issues
    ),
    PackageSpec(
        ".buildkite/dagster-buildkite",
        run_pytest=False,
    ),
]
