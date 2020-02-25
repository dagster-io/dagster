import os
import subprocess
import sys

import yaml
from defines import SupportPython3sEx35, SupportedPython, SupportedPython3s, SupportedPythons
from step_builder import StepBuilder, wait_step

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


TOX_MAP = {
    SupportedPython.V3_8: "py38",
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}

# https://github.com/dagster-io/dagster/issues/1662
DO_COVERAGE = True

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = "/tmp/gcp-key-elementl-dev.json"


def check_for_release():
    try:
        git_tag = str(
            subprocess.check_output(
                ['git', 'describe', '--exact-match', '--abbrev=0'], stderr=subprocess.STDOUT
            )
        ).strip('\'b\\n')
    except subprocess.CalledProcessError:
        return False

    version = {}
    with open('python_modules/dagster/dagster/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if git_tag == version['__version__']:
        return True

    return False


def network_buildkite_container(network_name):
    return [
        # hold onto your hats, this is docker networking at its best. First, we figure out
        # the name of the currently running container...
        "export CONTAINER_ID=`cut -c9- < /proc/1/cpuset`",
        r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
        # then, we dynamically bind this container into the user-defined bridge
        # network to make the target containers visible...
        "docker network connect {network_name} \\${{CONTAINER_NAME}}".format(
            network_name=network_name
        ),
    ]


def connect_sibling_docker_container(network_name, container_name, env_variable):
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        (
            "export {env_variable}=`docker inspect --format "
            "'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
            "{container_name}`".format(
                network_name=network_name, container_name=container_name, env_variable=env_variable
            )
        )
    ]


def publish_test_images():
    '''This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests
    '''
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        key = "dagster-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("test images {version}".format(version=version), key=key)
            .run(
                # credentials
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                "export GOOGLE_APPLICATION_CREDENTIALS=\"/tmp/gcp-key-elementl-dev.json\"",
                "aws s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
                #
                # build test image
                "./.buildkite/images/docker/test_project/build.sh " + version,
                #
                # tag and push the built image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
                + version,
                "docker tag dagster-docker-buildkite $${TEST_IMAGE}",
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


def python_modules_tox_tests(directory, supported_pythons=None):
    label = directory.replace("/", "-")
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    supported_pythons = supported_pythons or SupportedPythons + [SupportedPython.V3_8]
    for version in supported_pythons:

        # pyspark doesn't support Python 3.8 yet
        # See: https://github.com/dagster-io/dagster/issues/1960
        if ('pyspark' in label or 'aws' in label) and version == SupportedPython.V3_8:
            continue

        coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
            label=label, version=version
        )
        tests.append(
            StepBuilder("{label} tests ({ver})".format(label=label, ver=TOX_MAP[version]))
            .run(
                "eval $(ssh-agent)",
                "cd python_modules/{directory}".format(directory=directory),
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version, ['AWS_DEFAULT_REGION', 'TWILIO_TEST_ACCOUNT_SID', 'TWILIO_TEST_AUTH_TOKEN']
            )
            .build()
        )

    return tests


def airline_demo_tests():
    tests = []
    for version in SupportedPython3s:
        coverage = ".coverage.airline-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('airline-demo tests ({version})'.format(version=TOX_MAP[version]))
            .on_integration_image(version)
            .run(
                "cd examples",
                # Build the image we use for airflow in the demo tests
                "./build_airline_demo_image.sh",
                "mkdir -p /home/circleci/airflow",
                # Run the postgres db. We are in docker running docker
                # so this will be a sibling container.
                "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                network_buildkite_container('postgres'),
                connect_sibling_docker_container(
                    'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                ),
                "tox -vv -c airline.tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .build()
        )

    return tests


def events_demo_tests():
    tests = []
    for version in SupportedPython3s:
        coverage = ".coverage.events-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('events-demo tests ({version})'.format(version=TOX_MAP[version]))
            .on_integration_image(
                version, ['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION']
            )
            .run(
                "pushd examples",
                "tox -vv -c event.tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .build()
        )
    return tests


def airflow_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons:
        coverage = ".coverage.dagster-airflow.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-airflow ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
                + GCP_CREDS_LOCAL_FILE,
                "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
                "./.buildkite/scripts/dagster_airflow.sh %s %s" % (version, TOX_MAP[version]),
                "pushd python_modules/libraries/dagster-airflow/",
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
                "popd",
            )
            .depends_on(["dagster-test-images-{version}".format(version=TOX_MAP[version])])
            .on_integration_image(
                version,
                [
                    'AIRFLOW_HOME',
                    'AWS_ACCOUNT_ID',
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY',
                    'BUILDKITE_SECRETS_BUCKET',
                    'GOOGLE_APPLICATION_CREDENTIALS',
                ],
            )
            .build()
        )
    return tests


def k8s_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        coverage = ".coverage.dagster-k8s.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-k8s ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
                "export DAGSTER_DOCKER_REPOSITORY=\"$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com\"",
                "pushd python_modules/libraries/dagster-k8s/",
                "tox -vv -e {ver} -- -s".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
                "popd",
            )
            .depends_on(["dagster-test-images-{version}".format(version=TOX_MAP[version])])
            .on_integration_image(
                version,
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


def celery_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        coverage = ".coverage.dagster-celery.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("[dagster-celery] ({ver})".format(ver=TOX_MAP[version]))
            .on_integration_image(version)
            .run(
                "pushd python_modules/libraries/dagster-celery",
                # Run the rabbitmq db. We are in docker running docker
                # so this will be a sibling container.
                "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                network_buildkite_container('rabbitmq'),
                connect_sibling_docker_container(
                    'rabbitmq', 'test-rabbitmq', 'DAGSTER_CELERY_BROKER_HOST'
                ),
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .build()
        )
    return tests


def dagster_postgres_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        coverage = ".coverage.dagster-postgres.{version}.$BUILDKITE_BUILD_ID".format(
            version=version
        )
        tests.append(
            StepBuilder("libraries/dagster-postgres tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "cd python_modules/libraries/dagster-postgres/dagster_postgres_tests/",
                "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
                "docker-compose -f docker-compose-multi.yml up -d",  # clean up in hooks/pre-exit,
                network_buildkite_container('postgres'),
                connect_sibling_docker_container(
                    'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                ),
                network_buildkite_container('postgres_multi'),
                connect_sibling_docker_container(
                    'postgres_multi', 'test-run-storage-db', 'POSTGRES_TEST_RUN_STORAGE_DB_HOST',
                ),
                connect_sibling_docker_container(
                    'postgres_multi',
                    'test-event-log-storage-db',
                    'POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST',
                ),
                "pushd ../",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
                "popd",
            )
            .on_integration_image(version)
            .build()
        )
    return tests


def examples_tests():
    tests = []
    for version in SupportedPython3s:
        coverage = ".coverage.examples.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("examples tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd examples",
                "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                network_buildkite_container('postgres'),
                connect_sibling_docker_container(
                    'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                ),
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )
    return tests


def automation_tests():
    tests = []
    version = SupportedPython.V3_7
    coverage = ".coverage.automation.{version}.$BUILDKITE_BUILD_ID".format(version=version)
    tests.append(
        StepBuilder("automation tests ({ver})".format(ver=TOX_MAP[version]))
        .run(
            "pushd python_modules/automation",
            "tox -e {ver}".format(ver=TOX_MAP[version]),
            "mv .coverage {file}".format(file=coverage),
            "buildkite-agent artifact upload {file}".format(file=coverage),
        )
        .on_integration_image(version)
        .build()
    )
    return tests


def gcp_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.libraries-dagster-gcp.{version}.$BUILDKITE_BUILD_ID".format(
            version=version
        )
        tests.append(
            StepBuilder("libraries-dagster-gcp tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
                + GCP_CREDS_LOCAL_FILE,
                "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
                "cd python_modules/libraries/dagster-gcp",
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version,
                [
                    'BUILDKITE_SECRETS_BUCKET',
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY',
                    'GCP_PROJECT_ID',
                ],
            )
            .build()
        )

    return tests


def dask_tests():
    tests = []
    # We don't test dagster-dask against Python 3.5 because Dask dropped support
    # for 3.5 with Dask 2.7.0 (2019-11-08)
    for version in SupportPython3sEx35:
        coverage = ".coverage.dagster-dask.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-dask tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd python_modules/libraries/dagster-dask/dagster_dask_tests/dask-docker",
                "./build.sh " + version,
                # Run the docker-compose dask cluster
                "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit
                network_buildkite_container('dask'),
                connect_sibling_docker_container('dask', 'dask-scheduler', 'DASK_ADDRESS'),
                "popd",
                "pushd python_modules/libraries/dagster-dask/",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version, ['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION']
            )
            .build()
        )
    return tests


def library_tests():
    library_path = os.path.join(SCRIPT_PATH, '..', 'python_modules/libraries/')
    library_modules = set(os.listdir(library_path))

    tests = []

    # Some libraries have more involved tests, which must be explicitly defined here
    extra_test_libraries = {
        'dagster-airflow': airflow_tests(),
        'dagster-celery': celery_tests(),
        'dagster-dask': dask_tests(),
        'dagster-gcp': gcp_tests(),
        'dagster-k8s': k8s_tests(),
        'dagster-postgres': dagster_postgres_tests(),
        'lakehouse': lakehouse_tests(),
    }

    for library in library_modules:
        if library in extra_test_libraries:
            tests += extra_test_libraries[library]
        else:
            tests += python_modules_tox_tests("libraries/{library}".format(library=library))

    return tests


def dagit_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        coverage = ".coverage.dagit.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagit tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd python_modules",
                "make rebuild_dagit",
                "popd",
                "cd python_modules/dagit",
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )

    return tests


def lakehouse_tests():
    tests = []
    for version in SupportedPython3s:
        coverage = ".coverage.lakehouse.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("lakehouse tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "cd python_modules/libraries/lakehouse",
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )

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
    res = []

    base_paths = ['.buildkite', 'bin', 'docs', 'examples']
    base_paths_ext = ['"%s/*.py"' % p for p in base_paths]

    res.append(
        StepBuilder("pylint misc")
        .run(
            "make install_dev_python_modules",
            "pylint -j 0 `git ls-files %s` --rcfile=.pylintrc" % ' '.join(base_paths_ext),
        )
        .on_integration_image(SupportedPython.V3_7)
        .build()
    )

    python_modules = [
        'python_modules/%s' % path
        for path in os.listdir('python_modules/')
        if os.path.isdir('python_modules/%s' % path)
    ]

    for path in python_modules:
        res.append(
            StepBuilder("pylint %s" % path)
            .run(
                "make install_dev_python_modules",
                "pylint -j 0 `git ls-files '%s/*.py'` --rcfile=.pylintrc" % path,
            )
            .on_integration_image(SupportedPython.V3_7)
            .build()
        )
    return res


def gatsby_docs_build_tests():
    tests = []
    for version in [SupportedPython.V3_7]:
        tests.append(
            StepBuilder("gatsby docs build tests")
            .run(
                "pip install -r bin/requirements.txt -qqq",
                "pip install -r bin/dev-requirements.txt -qqq",
                "pip install -r .read-the-docs-requirements.txt -qqq",
                "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
                "cd docs/gatsby",
                "yarn install",
                "yarn sphinx -v latest",
                "yarn build",
            )
            .on_integration_image(
                version, ['ALGOLIA_APP_ID', 'ALGOLIA_SEARCH_KEY', 'ALGOLIA_ADMIN_KEY']
            )
            .build()
        )

    return tests


def releasability_tests():
    tests = []
    for version in [SupportedPython.V3_7]:
        tests.append(
            StepBuilder("releasibility tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pip install -r bin/requirements.txt",
                "pip install -r bin/dev-requirements.txt",
                "cd bin",
                "SLACK_RELEASE_BOT_TOKEN='dummy' pytest",
            )
            .on_integration_image(version)
            .build()
        )

    return tests


if __name__ == "__main__":
    steps = []
    steps += publish_test_images()
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
            "pip install -r .read-the-docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/dagstermill -qqq",
            "pytest -vv docs",
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
            "examples/dagster_examples/intro_tutorial/custom_types_mypy* "
            "--ignore-missing-imports",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]

    steps += airline_demo_tests()
    steps += automation_tests()
    steps += events_demo_tests()
    steps += examples_tests()

    steps += dagit_tests()
    steps += pipenv_smoke_tests()

    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests(
        "dagstermill",
        # Disabled 3.5 https://github.com/dagster-io/dagster/issues/2034
        supported_pythons=[
            SupportedPython.V2_7,
            SupportedPython.V3_6,
            SupportedPython.V3_7,
            SupportedPython.V3_8,
        ],
    )
    steps += library_tests()

    steps += releasability_tests()

    steps += gatsby_docs_build_tests()

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
