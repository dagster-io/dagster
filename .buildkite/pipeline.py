import os

import yaml
from defines import (
    TOX_MAP,
    SupportedPython,
    SupportedPython3s,
    SupportedPython3sNo38,
    SupportedPythons,
    SupportedPythonsNo38,
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
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons:
        key = "dagster-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("test images {version}".format(version=version), key=key)
            .run(
                # credentials
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                "export GOOGLE_APPLICATION_CREDENTIALS=\"/tmp/gcp-key-elementl-dev.json\"",
                "aws s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
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
            .on_integration_image(
                version,
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
        'pushd examples',
        # Build the image we use for airflow in the demo tests
        './build_airline_demo_image.sh',
        'mkdir -p /home/circleci/airflow',
        # Run the postgres db. We are in docker running docker
        # so this will be a sibling container.
        'docker-compose up -d --remove-orphans',  # clean up in hooks/pre-exit
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container('postgres'),
        connect_sibling_docker_container('postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'),
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


def dagit_extra_cmds_fn(_):
    return ["make rebuild_dagit"]


def dask_extra_cmds_fn(version):
    return [
        "pushd python_modules/libraries/dagster-dask/dagster_dask_tests/dask-docker",
        "./build.sh " + version,
        # Run the docker-compose dask cluster
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
        network_buildkite_container('dask'),
        connect_sibling_docker_container('dask', 'dask-scheduler', 'DASK_ADDRESS'),
        "popd",
    ]


def examples_extra_cmds_fn(_):
    return [
        "pushd examples",
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
        connect_sibling_docker_container(
            'postgres_multi', 'test-schedule-storage-db', 'POSTGRES_TEST_SCHEDULE_STORAGE_DB_HOST',
        ),
        "popd",
    ]


# Some Dagster packages have more involved test configs or support only certain Python version;
# special-case those here
DAGSTER_PACKAGES_WITH_CUSTOM_TESTS = [
    # Examples: Airline Demo
    ModuleBuildSpec(
        'examples',
        supported_pythons=SupportedPython3sNo38,
        extra_cmds_fn=airline_demo_extra_cmds_fn,
        tox_file='tox_airline.ini',
        buildkite_label='airline-demo',
    ),
    # Examples: Events Demo
    # TODO: https://github.com/dagster-io/dagster/issues/2617
    # ModuleBuildSpec(
    #     'examples',
    #     env_vars=['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION'],
    #     supported_pythons=SupportedPython3sNo38,
    #     tox_file='tox_events.ini',
    #     buildkite_label='events-demo',
    # ),
    # Examples
    ModuleBuildSpec(
        'examples',
        # See: https://github.com/dagster-io/dagster/issues/1960
        # Also, examples are py3-only
        supported_pythons=SupportedPython3sNo38,
        extra_cmds_fn=examples_extra_cmds_fn,
    ),
    ModuleBuildSpec('examples/docs_snippets', upload_coverage=False),
    ModuleBuildSpec('python_modules/dagit', extra_cmds_fn=dagit_extra_cmds_fn),
    ModuleBuildSpec(
        'python_modules/automation', supported_pythons=[SupportedPython.V3_7, SupportedPython.V3_8]
    ),
    ModuleBuildSpec('python_modules/dagster'),
    ModuleBuildSpec(
        'python_modules/dagster-graphql',
        tox_env_suffixes=[
            '-not_graphql_context_test_suite',
            '-in_memory_instance_hosted_user_process_env',
            '-in_memory_instance_out_of_process_env',
            '-in_memory_instance_multi_location',
            '-sqlite_instance_hosted_user_process_env',
            '-sqlite_instance_out_of_process_env',
            '-sqlite_instance_multi_location',
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
        supported_pythons=SupportedPythonsNo38,
        extra_cmds_fn=airflow_extra_cmds_fn,
        depends_on_fn=test_image_depends_fn,
        tox_env_suffixes=['-default', '-requiresk8s', '-requiresairflowdb'],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-aws',
        env_vars=['AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'],
        # See: https://github.com/dagster-io/dagster/issues/1960
        supported_pythons=SupportedPythonsNo38,
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
        'python_modules/libraries/dagster-dask',
        env_vars=['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION'],
        supported_pythons=[SupportedPython.V3_6, SupportedPython.V3_7],
        extra_cmds_fn=dask_extra_cmds_fn,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-databricks',
        # See: https://github.com/dagster-io/dagster/issues/1960
        supported_pythons=SupportedPythonsNo38,
    ),
    ModuleBuildSpec('python_modules/libraries/dagster-flyte', supported_pythons=SupportedPython3s,),
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
        'python_modules/libraries/dagster-pyspark',
        # See: https://github.com/dagster-io/dagster/issues/1960
        supported_pythons=SupportedPythonsNo38,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-spark',
        # See: https://github.com/dagster-io/dagster/issues/1960
        supported_pythons=SupportedPythonsNo38,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagster-twilio',
        env_vars=['TWILIO_TEST_ACCOUNT_SID', 'TWILIO_TEST_AUTH_TOKEN'],
        # Remove once https://github.com/dagster-io/dagster/issues/2511 is resolved
        retries=2,
    ),
    ModuleBuildSpec(
        'python_modules/libraries/dagstermill',
        supported_pythons=[
            SupportedPython.V2_7,
            # Disabled 3.5 https://github.com/dagster-io/dagster/issues/2034
            SupportedPython.V3_6,
            SupportedPython.V3_7,
            SupportedPython.V3_8,
        ],
    ),
    ModuleBuildSpec(
        'python_modules/libraries/lakehouse',
        supported_pythons=[SupportedPython.V3_5, SupportedPython.V3_6, SupportedPython.V3_7],
    ),
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


def pipenv_smoke_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    # See: https://github.com/dagster-io/dagster/issues/2079
    for version in SupportedPython3s:
        is_release = check_for_release()
        smoke_test_steps = (
            [
                "mkdir /tmp/pipenv_smoke_tests",
                "pushd /tmp/pipenv_smoke_tests",
                "pipenv install -e /workdir/python_modules/dagster",
                "pipenv install -e /workdir/python_modules/dagit",
            ]
            if not is_release
            else []
        )
        tests.append(
            StepBuilder("pipenv smoke tests ({ver})".format(ver=TOX_MAP[version]))
            .run(*smoke_test_steps)
            .on_integration_image(version)
            .build()
        )

    return tests


def coverage_step():
    return (
        StepBuilder("coverage")
        .run(
            "apt-get update",
            "apt-get -qq -y install lcov ruby-full",
            "pip install coverage coveralls coveralls-merge",
            "gem install coveralls-lcov",
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            'buildkite-agent artifact download "lcov.*" tmp/',
            "cd tmp",
            "coverage combine",
            "coveralls-lcov -v -n lcov.* > coverage.js.json",
            "coveralls",  # add '--merge=coverage.js.json' to report JS coverage
        )
        .on_integration_image(
            SupportedPython.V3_7,
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
                -e python_modules/libraries/dagstermill \
                -e python_modules/libraries/dagster-celery \
                -e python_modules/libraries/dagster-dask \
                -e examples
            """,
            "pylint -j 0 `git ls-files %s` --rcfile=.pylintrc" % ' '.join(base_paths_ext),
        )
        .on_integration_image(SupportedPython.V3_7)
        .build()
    ]


def next_docs_build_tests():
    tests = []
    for version in [SupportedPython.V3_7]:
        tests.append(
            StepBuilder("next docs build tests")
            .run(
                "pip install -r bin/requirements.txt -qqq",
                "pip install -r bin/dev-requirements.txt -qqq",
                "pip install -r docs-requirements.txt -qqq",
                "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
                "cd docs",
                "make buildnext",
                "make root_build",
            )
            .on_integration_image(version)
            .build()
        )

        tests.append(
            StepBuilder("next docs tests")
            .run(
                "pip install -r bin/requirements.txt -qqq",
                "pip install -r bin/dev-requirements.txt -qqq",
                "pip install -r docs-requirements.txt -qqq",
                "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
                "cd docs",
                "make buildnext",
                "cd next",
                "yarn test",
            )
            .on_integration_image(version)
            .build()
        )

    return tests


def releasability_tests(version=SupportedPython.V3_7):
    return [
        StepBuilder("releasibility test")
        .run(
            "pip install -r bin/requirements.txt",
            "pip install -r bin/dev-requirements.txt",
            "cd bin",
            "SLACK_RELEASE_BOT_TOKEN='dummy' pytest",
        )
        .on_integration_image(version)
        .build()
    ]


def version_equality_checks(version=SupportedPython.V3_7):
    return [
        StepBuilder("version equality checks for libraries")
        .on_integration_image(version)
        .run("pip install -r bin/requirements.txt", "python bin/version_check.py")
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
            "pip install -e examples -qqq",
            "cd js_modules/dagit",
            "yarn install --offline",
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
            "mypy examples/dagster_examples/airline_demo "
            "examples/dagster_examples/bay_bikes "
            "examples/dagster_examples/intro_tutorial/basics/e04_quality/custom_types_mypy* "
            "--ignore-missing-imports",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("Validate Library Docs")
        .run('python .buildkite/scripts/check_library_docs.py')
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]

    for m in DAGSTER_PACKAGES_WITH_CUSTOM_TESTS:
        steps += m.get_tox_build_steps()

    steps += extra_library_tests()

    steps += pipenv_smoke_tests()
    steps += version_equality_checks()
    steps += releasability_tests()
    steps += next_docs_build_tests()

    if DO_COVERAGE:
        steps += [wait_step(), coverage_step()]

    print(
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
