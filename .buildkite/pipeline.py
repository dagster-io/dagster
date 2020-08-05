import os

import yaml
from defines import (
    TOX_MAP,
    UNIT_IMAGE_VERSION,
    SupportedPython,
    SupportedPython3s,
    SupportedPythons,
)
from module_build_spec import ModuleBuildSpec
from step_builder import StepBuilder, wait_step
from utils import check_for_release, connect_sibling_docker_container, network_buildkite_container

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

# https://github.com/dagster-io/dagster/issues/1662
DO_COVERAGE = True

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = "/tmp/gcp-key-elementl-dev.json"


def publish_test_images():
    '''This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests
    '''
    tests = []
    for version in SupportedPythons:
        key = "dagster-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("test images {version}".format(version=version), key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see .buildkite/images/test_image_builder/Dockerfile
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-1 | sh",
                "export GOOGLE_APPLICATION_CREDENTIALS=\"/tmp/gcp-key-elementl-dev.json\"",
                "/scriptdir/aws.pex s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
                #
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/dagster_test/test_project/build.sh "
                + version
                + " $${TEST_IMAGE}",
                #
                # push the built image
                "echo -e \"--- \033[32m:docker: Pushing Docker image\033[0m\"",
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                'test-image-builder:v2',
                [
                    'AIRFLOW_HOME',
                    'AWS_ACCOUNT_ID',
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY',
                    'BUILDKITE_SECRETS_BUCKET',
                ],
            )
            .build()
        )

        key = "dagster-core-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("core test images {version}".format(version=version), key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see .buildkite/images/test_image_builder/Dockerfile
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-1 | sh",
                # set the base image
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-unit:py"
                + version
                + "-"
                + UNIT_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-core-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/build_core.sh " + version + " $${TEST_IMAGE}",
                #
                # push the built image
                "echo -e \"--- \033[32m:docker: Pushing Docker image\033[0m\"",
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                'test-image-builder:v2',
                [
                    'AWS_ACCOUNT_ID',
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY',
                    'BUILDKITE_SECRETS_BUCKET',
                ],
            )
            .build()
        )
    return tests


def test_image_depends_fn(version):
    return ["dagster-test-images-{version}".format(version=TOX_MAP[version])]


def airflow_extra_cmds_fn(version):
    return [
        "export AIRFLOW_HOME=\"/airflow\"",
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
        "aws ecr get-login --no-include-email --region us-west-1 | sh",
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
    ]


def airline_demo_extra_cmds_fn(_):
    return [
        'pushd examples/airline_demo',
        # Run the postgres db. We are in docker running docker
        # so this will be a sibling container.
        'docker-compose up -d --remove-orphans',  # clean up in hooks/pre-exit
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container('postgres'),
        connect_sibling_docker_container(
            'postgres', 'test-postgres-db-airline', 'POSTGRES_TEST_DB_HOST'
        ),
        'popd',
    ]


def celery_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container('rabbitmq'),
        connect_sibling_docker_container('rabbitmq', 'test-rabbitmq', 'DAGSTER_CELERY_BROKER_HOST'),
        "popd",
    ]


def integration_suite_extra_cmds_fn(version):
    return [
        "export AIRFLOW_HOME=\"/airflow\"",
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
        "aws ecr get-login --no-include-email --region us-west-1 | sh",
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container('rabbitmq'),
        connect_sibling_docker_container('rabbitmq', 'test-rabbitmq', 'DAGSTER_CELERY_BROKER_HOST'),
        "popd",
    ]


def dagster_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
        "aws ecr get-login --no-include-email --region us-west-1 | sh",
        "export IMAGE_NAME=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-core-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
        + version,
        "pushd python_modules/dagster/dagster_tests",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        network_buildkite_container('dagster'),
        connect_sibling_docker_container('dagster', 'dagster-grpc-server', 'GRPC_SERVER_HOST'),
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
        network_buildkite_container('postgres'),
        connect_sibling_docker_container('postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'),
        "popd",
    ]


def k8s_extra_cmds_fn(version):
    return [
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
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
        network_buildkite_container('postgres'),
        connect_sibling_docker_container('postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'),
        network_buildkite_container('postgres_multi'),
        connect_sibling_docker_container(
            'postgres_multi', 'test-run-storage-db', 'POSTGRES_TEST_RUN_STORAGE_DB_HOST',
        ),
        connect_sibling_docker_container(
            'postgres_multi',
            'test-event-log-storage-db',
            'POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST',
        ),
        "popd",
    ]


def graphql_pg_extra_cmds_fn(_):
    return [
        "pushd python_modules/dagster-graphql/dagster_graphql_tests/graphql/",
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container('postgres'),
        connect_sibling_docker_container(
            'postgres', 'test-postgres-db-graphql', 'POSTGRES_TEST_DB_HOST'
        ),
        "popd",
    ]


# Some Dagster packages have more involved test configs or support only certain Python version;
# special-case those here
DAGSTER_PACKAGES_WITH_CUSTOM_TESTS = [
    # Examples: Airline Demo
    ModuleBuildSpec(
        'examples/airline_demo',
        supported_pythons=SupportedPython3s,
        extra_cmds_fn=airline_demo_extra_cmds_fn,
        buildkite_label='airline-demo',
    ),
    # Examples: Events Demo
    # TODO: https://github.com/dagster-io/dagster/issues/2617
    # ModuleBuildSpec(
    #     'examples',
    #     env_vars=['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION'],
    #     supported_pythons=SupportedPython3s,
    #     tox_file='tox_events.ini',
    #     buildkite_label='events-demo',
    # ),
    # Examples
    ModuleBuildSpec(
        'examples/legacy_examples',
        supported_pythons=SupportedPython3s,
        extra_cmds_fn=legacy_examples_extra_cmds_fn,
    ),
    ModuleBuildSpec(
        'examples/docs_snippets',
        extra_cmds_fn=legacy_examples_extra_cmds_fn,
        upload_coverage=False,
        supported_pythons=SupportedPython3s,
    ),
    ModuleBuildSpec('python_modules/dagit', extra_cmds_fn=dagit_extra_cmds_fn),
    ModuleBuildSpec('python_modules/automation', supported_pythons=SupportedPython3s),
    ModuleBuildSpec(
        'python_modules/dagster',
        extra_cmds_fn=dagster_extra_cmds_fn,
        env_vars=['AWS_ACCOUNT_ID'],
        depends_on_fn=test_image_depends_fn,
        tox_env_suffixes=[
            '-api_tests',
            '-cli_tests',
            '-cli_command_cli_api_tests',
            '-cli_command_grpc_tests',
            '-core_tests',
            '-general_tests',
        ],
    ),
    ModuleBuildSpec(
        'python_modules/dagster-graphql',
        tox_env_suffixes=[
            '-in_memory_instance_hosted_user_process_env',
            '-in_memory_instance_out_of_process_env',
            '-in_memory_instance_multi_location',
            '-in_memory_instance_grpc_env',
            '-sqlite_instance_hosted_user_process_env',
            '-sqlite_instance_out_of_process_env',
            '-sqlite_instance_multi_location',
            '-sqlite_instance_grpc_env',
            '-sqlite_instance_external_grpc_server_env',
        ],
    ),
    ModuleBuildSpec(
        'python_modules/dagster-graphql',
        extra_cmds_fn=graphql_pg_extra_cmds_fn,
        tox_file='tox_postgres.ini',
        buildkite_label='dagster-graphql-postgres',
        tox_env_suffixes=[
            '-not_graphql_context_test_suite',
            '-postgres_instance_hosted_user_process_env',
            '-postgres_instance_out_of_process_env',
            '-postgres_instance_multi_location',
            '-postgres_instance_grpc_env',
        ],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-airflow',
        env_vars=[
            'AIRFLOW_HOME',
            'AWS_ACCOUNT_ID',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'BUILDKITE_SECRETS_BUCKET',
            'GOOGLE_APPLICATION_CREDENTIALS',
        ],
        extra_cmds_fn=airflow_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
        tox_env_suffixes=['-default', '-requiresairflowdb'],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-aws',
        env_vars=['AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-azure', env_vars=['AZURE_STORAGE_ACCOUNT_KEY'],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-celery',
        env_vars=['AWS_ACCOUNT_ID', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'],
        extra_cmds_fn=celery_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-celery-docker',
        env_vars=['AWS_ACCOUNT_ID', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'],
        extra_cmds_fn=celery_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-dask',
        env_vars=['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION'],
        supported_pythons=SupportedPython3s,
    ),
    ModuleBuildSpec('python_modules/libraries/dagster-flyte', supported_pythons=SupportedPython3s),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-gcp',
        env_vars=[
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'BUILDKITE_SECRETS_BUCKET',
            'GCP_PROJECT_ID',
        ],
        extra_cmds_fn=gcp_extra_cmds_fn,
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    ModuleBuildSpec('python_modules/libraries/dagster-ge', supported_pythons=SupportedPython3s),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-k8s',
        env_vars=[
            'AWS_ACCOUNT_ID',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'BUILDKITE_SECRETS_BUCKET',
        ],
        extra_cmds_fn=k8s_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-postgres', extra_cmds_fn=postgres_extra_cmds_fn
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-twilio',
        env_vars=['TWILIO_TEST_ACCOUNT_SID', 'TWILIO_TEST_AUTH_TOKEN'],
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    ModuleBuildSpec('python_modules/libraries/lakehouse', supported_pythons=SupportedPython3s),
]


def extra_library_tests():
    '''Ensure we test any remaining libraries not explicitly listed above'''
    library_path = os.path.join(SCRIPT_PATH, '..', 'python_modules', 'libraries')
    library_packages = [
        os.path.join('python_modules', 'libraries', library) for library in os.listdir(library_path)
    ]

    dirs = set([pkg.directory for pkg in DAGSTER_PACKAGES_WITH_CUSTOM_TESTS])

    tests = []
    for library in library_packages:
        if library not in dirs:
            tests += ModuleBuildSpec(library).get_tox_build_steps()
    return tests


def integration_tests():
    tests = []
    tests += ModuleBuildSpec(
        os.path.join('integration_tests', 'python_modules', 'dagster-k8s-test-infra'),
        supported_pythons=SupportedPython3s,
        upload_coverage=True,
    ).get_tox_build_steps()

    integration_suites_root = os.path.join(SCRIPT_PATH, '..', 'integration_tests', 'test_suites')
    integration_suites = [
        os.path.join('integration_tests', 'test_suites', suite)
        for suite in os.listdir(integration_suites_root)
    ]

    for integration_suite in integration_suites:
        tox_env_suffixes = (
            ['-default', '-markscheduler']
            if integration_suite
            == os.path.join('integration_tests', 'test_suites', 'k8s-integration-test-suite')
            else None
        )
        tests += ModuleBuildSpec(
            integration_suite,
            env_vars=[
                'AIRFLOW_HOME',
                'AWS_ACCOUNT_ID',
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY',
                'BUILDKITE_SECRETS_BUCKET',
                'GOOGLE_APPLICATION_CREDENTIALS',
            ],
            supported_pythons=SupportedPython3s,
            upload_coverage=True,
            extra_cmds_fn=integration_suite_extra_cmds_fn,
            depends_on_fn=test_image_depends_fn,
            tox_env_suffixes=tox_env_suffixes,
            retries=2,
        ).get_tox_build_steps()
    return tests


def examples_tests():
    '''Auto-discover and test all new examples'''

    skip_examples = [
        # Skip these folders because they need custom build config
        'docs_snippets',
        'legacy_examples',
        'airline_demo',
    ]

    examples_root = os.path.join(SCRIPT_PATH, '..', 'examples')

    examples_packages = [
        os.path.join('examples', example)
        for example in os.listdir(examples_root)
        if example not in skip_examples and os.path.isdir(os.path.join(examples_root, example))
    ]

    tests = []
    for example in examples_packages:
        tests += ModuleBuildSpec(
            example, supported_pythons=SupportedPython3s, upload_coverage=False
        ).get_tox_build_steps()
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
        StepBuilder("pipenv smoke tests ({ver})".format(ver=TOX_MAP[version]))
        .run(*smoke_test_steps)
        .on_unit_image(version)
        .build()
        for version in SupportedPython3s
    ]


def coverage_step():
    return (
        StepBuilder("coverage")
        .run(
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            'buildkite-agent artifact download "lcov.*" tmp/',
            "cd tmp",
            "coverage debug sys",
            "coverage debug data",
            "coverage combine",
            "coveralls-lcov -v -n lcov.* > coverage.js.json",
            "coveralls",  # add '--merge=coverage.js.json' to report JS coverage
        )
        .on_python_image(
            'coverage-image:v1',
            [
                'COVERALLS_REPO_TOKEN',  # exported by /env in ManagedSecretsBucket
                'CI_NAME',
                'CI_BUILD_NUMBER',
                'CI_BUILD_URL',
                'CI_BRANCH',
                'CI_PULL_REQUEST',
            ],
        )
        .build()
    )


def pylint_steps():
    base_paths = ['.buildkite', 'bin', 'docs/next/src']
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
            "pylint -j 0 `git ls-files %s` --rcfile=.pylintrc" % ' '.join(base_paths_ext),
        )
        .on_integration_image(SupportedPython.V3_7)
        .build()
    ]


def next_docs_build_tests():
    return [
        StepBuilder("next docs build tests")
        .run(
            "pip install -e python_modules/automation",
            "pip install -r docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "cd docs",
            "make NODE_ENV=production VERSION=master full_docs_build",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("next docs tests")
        .run(
            "pip install -e python_modules/automation",
            "pip install -r docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "cd docs",
            "make buildnext",
            "cd next",
            "yarn test",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]


def version_equality_checks(version=SupportedPython.V3_7):
    return [
        StepBuilder("version equality checks for libraries")
        .on_integration_image(version)
        .run("pip install -e python_modules/automation", "dagster-release version")
        .build()
    ]


if __name__ == "__main__":
    steps = []
    steps += publish_test_images()

    steps += [
        StepBuilder("dagster-flyte build example")
        .run("cd python_modules/libraries/dagster-flyte/examples", "make docker_build")
        .on_integration_image(SupportedPython.V3_6)
        .build()
    ]

    steps += pylint_steps()
    steps += [
        StepBuilder("isort")
        .run("pip install isort>=4.3.21", "make isort", "git diff --exit-code",)
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("black")
        # See: https://github.com/dagster-io/dagster/issues/1999
        .run("make check_black").on_integration_image(SupportedPython.V3_7).build(),
        StepBuilder("docs snapshot test")
        .run(
            "pip install -r docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/libraries/dagstermill -qqq",
            "pytest -vv docs/test_doc_build.py",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("dagit webapp tests")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/dagster-graphql -qqq",
            "pip install -e python_modules/libraries/dagster-cron -qqq",
            "pip install -e python_modules/libraries/dagster-slack -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -e examples/legacy_examples -qqq",
            "cd js_modules/dagit",
            "yarn install",
            "yarn run ts",
            "yarn run jest",
            "yarn run check-prettier",
            "yarn run check-lint",
            "yarn run download-schema",
            "yarn run generate-types",
            "git diff --exit-code",
            "mv coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("mypy examples")
        .run(
            "pip install mypy",
            # start small by making sure the local code type checks
            "mypy examples/airline_demo/airline_demo "
            "examples/legacy_examples/dagster_examples/bay_bikes "
            "examples/docs_snippets/docs_snippets/intro_tutorial/basics/e04_quality/custom_types_mypy* "
            "--ignore-missing-imports",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("Validate Library Docs")
        .run('pip install -e python_modules/automation', 'dagster-docs validate-libraries')
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]

    for m in DAGSTER_PACKAGES_WITH_CUSTOM_TESTS:
        steps += m.get_tox_build_steps()

    steps += extra_library_tests()

    # https://github.com/dagster-io/dagster/issues/2785
    steps += pipenv_smoke_tests()
    steps += version_equality_checks()
    steps += next_docs_build_tests()
    steps += examples_tests()
    steps += integration_tests()

    if DO_COVERAGE:
        steps += [wait_step(), coverage_step()]

    print(  # pylint: disable=print-call
        yaml.dump(
            {
                "env": {
                    "CI_NAME": "buildkite",
                    "CI_BUILD_NUMBER": "$BUILDKITE_BUILD_NUMBER",
                    "CI_BUILD_URL": "$BUILDKITE_BUILD_URL",
                    "CI_BRANCH": "$BUILDKITE_BRANCH",
                    "CI_PULL_REQUEST": "$BUILDKITE_PULL_REQUEST",
                },
                "steps": steps,
            },
            default_flow_style=False,
        )
    )
