import os

from ..defines import GCP_CREDS_LOCAL_FILE, TOX_MAP, SupportedPython, SupportedPythons
from ..images.versions import COVERAGE_IMAGE_VERSION
from ..module_build_spec import ModuleBuildSpec
from ..step_builder import StepBuilder
from ..utils import check_for_release, connect_sibling_docker_container, network_buildkite_container
from .docs import docs_steps
from .helm import helm_steps
from .test_images import core_test_image_depends_fn, publish_test_images, test_image_depends_fn

GIT_REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")


def airflow_extra_cmds_fn(version):
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
        "pushd python_modules/libraries/dagster-airflow/dagster_airflow_tests/",
        "docker-compose up -d --remove-orphans",
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-airflow",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


def airline_demo_extra_cmds_fn(_):
    return [
        "pushd examples/airline_demo",
        # Run the postgres db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres", "test-postgres-db-airline", "POSTGRES_TEST_DB_HOST"
        ),
        "popd",
    ]


def dbt_example_extra_cmds_fn(_):
    return [
        "pushd examples/dbt_example",
        # Run the postgres db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres", "dbt_example_postgresql", "DAGSTER_DBT_EXAMPLE_PGHOST"
        ),
        "mkdir -p ~/.dbt/",
        "touch ~/.dbt/profiles.yml",
        "cat dbt_example_project/profiles.yml >> ~/.dbt/profiles.yml",
        "popd",
    ]


def deploy_docker_example_extra_cmds_fn(_):
    return [
        "pushd examples/deploy_docker/from_source",
        "./build.sh",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        network_buildkite_container("docker_example_network"),
        connect_sibling_docker_container(
            "docker_example_network",
            "docker_example_dagit",
            "DEPLOY_DOCKER_DAGIT_HOST",
        ),
        "popd",
    ]


def celery_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("rabbitmq"),
        connect_sibling_docker_container("rabbitmq", "test-rabbitmq", "DAGSTER_CELERY_BROKER_HOST"),
        "popd",
    ]


def celery_docker_extra_cmds_fn(version):
    return celery_extra_cmds_fn(version) + [
        "pushd python_modules/libraries/dagster-celery-docker/dagster_celery_docker_tests/",
        "docker-compose up -d --remove-orphans",
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-celery-docker",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


def docker_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "pushd python_modules/libraries/dagster-docker/dagster_docker_tests/",
        "docker-compose up -d --remove-orphans",
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres",
            "test-postgres-db-docker",
            "POSTGRES_TEST_DB_HOST",
        ),
        "popd",
    ]


def dagster_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
        "export IMAGE_NAME=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/buildkite-test-image-core:$${BUILDKITE_BUILD_ID}-"
        + version,
        "pushd python_modules/dagster/dagster_tests",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        network_buildkite_container("dagster"),
        connect_sibling_docker_container("dagster", "dagster-grpc-server", "GRPC_SERVER_HOST"),
        "popd",
    ]


def dagit_extra_cmds_fn(_):
    return ["make rebuild_dagit"]


def legacy_examples_extra_cmds_fn(_):
    return [
        "pushd examples/legacy_examples",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("postgres"),
        connect_sibling_docker_container("postgres", "test-postgres-db", "POSTGRES_TEST_DB_HOST"),
        "popd",
    ]


def dbt_extra_cmds_fn(_):
    return [
        "pushd python_modules/libraries/dagster-dbt/dagster_dbt_tests",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres", "test-postgres-db-dbt", "POSTGRES_TEST_DB_DBT_HOST"
        ),
        "popd",
    ]


def k8s_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
    ]


def gcp_extra_cmds_fn(_):
    return [
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
    ]


def postgres_extra_cmds_fn(_):
    return [
        "pushd python_modules/libraries/dagster-postgres/dagster_postgres_tests/",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        "docker-compose -f docker-compose-multi.yml up -d",  # clean up in hooks/pre-exit,
        network_buildkite_container("postgres"),
        connect_sibling_docker_container("postgres", "test-postgres-db", "POSTGRES_TEST_DB_HOST"),
        network_buildkite_container("postgres_multi"),
        connect_sibling_docker_container(
            "postgres_multi",
            "test-run-storage-db",
            "POSTGRES_TEST_RUN_STORAGE_DB_HOST",
        ),
        connect_sibling_docker_container(
            "postgres_multi",
            "test-event-log-storage-db",
            "POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST",
        ),
        "popd",
    ]


def graphql_pg_extra_cmds_fn(_):
    return [
        "pushd python_modules/dagster-graphql/dagster_graphql_tests/graphql/",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("postgres"),
        connect_sibling_docker_container(
            "postgres", "test-postgres-db-graphql", "POSTGRES_TEST_DB_HOST"
        ),
        "popd",
    ]


# Some Dagster packages have more involved test configs or support only certain Python version;
# special-case those here
DAGSTER_PACKAGES_WITH_CUSTOM_TESTS = [
    # Examples: Airline Demo
    ModuleBuildSpec(
        "examples/airline_demo",
        extra_cmds_fn=airline_demo_extra_cmds_fn,
        buildkite_label="airline-demo",
    ),
    ModuleBuildSpec(
        "examples/dbt_example",
        extra_cmds_fn=dbt_example_extra_cmds_fn,
        buildkite_label="dbt_example",
        upload_coverage=False,
    ),
    ModuleBuildSpec(
        "examples/deploy_docker",
        extra_cmds_fn=deploy_docker_example_extra_cmds_fn,
        buildkite_label="deploy_docker_example",
        upload_coverage=False,
    ),
    # Examples: Events Demo
    # TODO: https://github.com/dagster-io/dagster/issues/2617
    # ModuleBuildSpec(
    #     'examples',
    #     env_vars=['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION'],
    #     tox_file='tox_events.ini',
    #     buildkite_label='events-demo',
    # ),
    # Examples
    ModuleBuildSpec(
        "examples/legacy_examples",
        extra_cmds_fn=legacy_examples_extra_cmds_fn,
        upload_coverage=False,
    ),
    ModuleBuildSpec(
        "examples/docs_snippets",
        extra_cmds_fn=legacy_examples_extra_cmds_fn,
        upload_coverage=False,
    ),
    ModuleBuildSpec("python_modules/dagit", extra_cmds_fn=dagit_extra_cmds_fn),
    ModuleBuildSpec("python_modules/automation"),
    ModuleBuildSpec(
        "python_modules/dagster",
        extra_cmds_fn=dagster_extra_cmds_fn,
        env_vars=["AWS_ACCOUNT_ID"],
        depends_on_fn=core_test_image_depends_fn,
        tox_env_suffixes=[
            "-api_tests",
            "-cli_tests",
            "-core_tests",
            "-daemon_tests",
            "-general_tests",
            "-scheduler_tests",
        ],
    ),
    ModuleBuildSpec(
        "python_modules/dagster-graphql",
        tox_env_suffixes=[
            "-not_graphql_context_test_suite",
            "-in_memory_instance_hosted_user_process_env",
            "-in_memory_instance_multi_location",
            "-in_memory_instance_managed_grpc_env",
            "-sqlite_instance_hosted_user_process_env",
            "-sqlite_instance_multi_location",
            "-sqlite_instance_managed_grpc_env",
            # Temporarily disabling due to thread-safety issues with
            # deployed gRPC servers (https://github.com/dagster-io/dagster/issues/3404)
            # "-sqlite_instance_deployed_grpc_env",
        ],
    ),
    ModuleBuildSpec(
        "python_modules/dagster-graphql",
        extra_cmds_fn=graphql_pg_extra_cmds_fn,
        tox_file="tox_postgres.ini",
        buildkite_label="dagster-graphql-postgres",
        tox_env_suffixes=[
            "-graphql_context_variants",
            "-postgres_instance_hosted_user_process_env",
            "-postgres_instance_multi_location",
            "-postgres_instance_managed_grpc_env",
            # Temporarily disabling due to thread-safety issues with
            # deployed gRPC servers (https://github.com/dagster-io/dagster/issues/3404)
            # "-postgres_instance_deployed_grpc_env",
        ],
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-dbt",
        extra_cmds_fn=dbt_extra_cmds_fn,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-airflow",
        env_vars=[
            "AIRFLOW_HOME",
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
        extra_cmds_fn=airflow_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
        tox_env_suffixes=["-default", "-requiresairflowdb"],
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-aws",
        env_vars=["AWS_DEFAULT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-azure",
        env_vars=["AZURE_STORAGE_ACCOUNT_KEY"],
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-celery",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        extra_cmds_fn=celery_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-celery-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        extra_cmds_fn=celery_docker_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-dask",
        env_vars=["AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION"],
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-docker",
        env_vars=["AWS_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        extra_cmds_fn=docker_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-gcp",
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
            "GCP_PROJECT_ID",
        ],
        extra_cmds_fn=gcp_extra_cmds_fn,
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-k8s",
        env_vars=[
            "AWS_ACCOUNT_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "BUILDKITE_SECRETS_BUCKET",
        ],
        extra_cmds_fn=k8s_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-postgres", extra_cmds_fn=postgres_extra_cmds_fn
    ),
    ModuleBuildSpec(
        "python_modules/libraries/dagster-twilio",
        env_vars=["TWILIO_TEST_ACCOUNT_SID", "TWILIO_TEST_AUTH_TOKEN"],
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    ModuleBuildSpec("python_modules/libraries/lakehouse", upload_coverage=False),
]


def extra_library_tests():
    """Ensure we test any remaining libraries not explicitly listed above"""
    library_path = os.path.join(GIT_REPO_ROOT, "python_modules", "libraries")
    library_packages = [
        os.path.join("python_modules", "libraries", library) for library in os.listdir(library_path)
    ]

    dirs = set([pkg.directory for pkg in DAGSTER_PACKAGES_WITH_CUSTOM_TESTS])

    tests = []
    for library in library_packages:
        if library not in dirs:
            tests += ModuleBuildSpec(library).get_tox_build_steps()
    return tests


def examples_tests():
    """Auto-discover and test all new examples"""

    skip_examples = [
        # Skip these folders because they need custom build config
        "docs_snippets",
        "legacy_examples",
        "airline_demo",
        "dbt_example",
        "deploy_docker",
    ]

    examples_root = os.path.join(GIT_REPO_ROOT, "examples")

    examples_packages = [
        os.path.join("examples", example)
        for example in os.listdir(examples_root)
        if example not in skip_examples and os.path.isdir(os.path.join(examples_root, example))
    ]

    tests = []
    for example in examples_packages:
        tests += ModuleBuildSpec(example, upload_coverage=False).get_tox_build_steps()
    return tests


def pipenv_smoke_tests():
    is_release = check_for_release()
    if is_release:
        return []

    smoke_test_steps = [
        "pushd /workdir/python_modules",
        "pip install pipenv",
        "pipenv install",
    ]

    # See: https://github.com/dagster-io/dagster/issues/2079
    return [
        StepBuilder(f"pipenv smoke tests {TOX_MAP[version]}")
        .run(*smoke_test_steps)
        .on_unit_image(version)
        .build()
        for version in SupportedPythons
    ]


def coverage_step():
    return (
        StepBuilder(":coverage:")
        .run(
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            'buildkite-agent artifact download "lcov.*" tmp/',
            "cd tmp",
            "coverage debug sys",
            "coverage debug data",
            "coverage combine",
            # coveralls-lcov is currently not working - fails with:
            # converter.rb:63:in `initialize': No such file or directory @ rb_sysopen - jest/mocks/dagre_layout.worker.ts
            # "coveralls-lcov -v -n lcov.* > coverage.js.json",
            "coveralls",  # add '--merge=coverage.js.json' to report JS coverage
        )
        .on_python_image(
            "buildkite-coverage:py3.8.7-{version}".format(version=COVERAGE_IMAGE_VERSION),
            [
                "COVERALLS_REPO_TOKEN",  # exported by /env in ManagedSecretsBucket
                "CI_NAME",
                "CI_BUILD_NUMBER",
                "CI_BUILD_URL",
                "CI_BRANCH",
                "CI_PULL_REQUEST",
            ],
        )
        .build()
    )


def pylint_steps():
    base_paths = [".buildkite", "bin", "docs/next/src"]
    base_paths_ext = ['"%s/**.py"' % p for p in base_paths]

    return [
        StepBuilder("pylint misc")
        .run(
            # Deps needed to pylint docs
            """pip install \
                -e python_modules/dagster \
                -e python_modules/dagit \
                -e python_modules/automation \
                -e python_modules/libraries/dagstermill \
                -e python_modules/libraries/dagster-celery \
                -e python_modules/libraries/dagster-dask \
                -e examples/legacy_examples
            """,
            "pylint -j 0 `git ls-files %s` --rcfile=.pylintrc" % " ".join(base_paths_ext),
        )
        .on_integration_image(SupportedPython.V3_7)
        .build()
    ]


def version_equality_checks(version=SupportedPython.V3_7):
    return [
        StepBuilder("all versions == ?")
        .on_integration_image(version)
        .run("pip install -e python_modules/automation", "dagster-release version")
        .build()
    ]


def schema_checks(version=SupportedPython.V3_8):
    return [
        StepBuilder("SQL schema checks")
        .on_integration_image(version)
        .run("pip install -e python_modules/dagster", "python scripts/check_schemas.py")
        .build()
    ]


def dagster_steps():
    steps = []
    steps += publish_test_images()

    steps += pylint_steps()
    steps += [
        StepBuilder(":isort:")
        .run(
            "pip install isort>=4.3.21",
            "make isort",
            "git diff --exit-code",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":python-black:")
        # See: https://github.com/dagster-io/dagster/issues/1999
        .run("pip install -e python_modules/dagster[test]", "make check_black")
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]

    for m in DAGSTER_PACKAGES_WITH_CUSTOM_TESTS:
        steps += m.get_tox_build_steps()

    steps += extra_library_tests()

    # https://github.com/dagster-io/dagster/issues/2785
    steps += pipenv_smoke_tests()
    steps += version_equality_checks()
    steps += docs_steps()
    steps += examples_tests()
    steps += helm_steps()
    steps += schema_checks()

    return steps
