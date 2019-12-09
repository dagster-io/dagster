import os
import subprocess
import sys

import yaml
from defines import SupportedPython, SupportedPython3s, SupportedPythons
from step_builder import StepBuilder

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


def wait_step():
    return "wait"


def network_buildkite_container(network_name):
    return [
        # hold onto your hats, this is docker networking at its best. First, we figure out
        # the name of the currently running container...
        "export CONTAINER_ID=`cut -c9- < /proc/1/cpuset`",
        r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
        # then, we dynamically bind this container into the dask user-defined bridge
        # network to make the dask containers visible...
        "docker network connect {network_name} \\${{CONTAINER_NAME}}".format(
            network_name=network_name
        ),
    ]


def connect_sibling_docker_container(network_name, container_name, env_variable):
    return [
        # Now, we grab the IP address of the dask-scheduler container from within the dask
        # bridge network and export it; this will let the tox tests talk to the scheduler.
        (
            "export {env_variable}=`docker inspect --format "
            "'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
            "{container_name}`".format(
                network_name=network_name, container_name=container_name, env_variable=env_variable
            )
        )
    ]


def wrap_with_docker_compose_steps(
    steps_to_execute, filename=None, remove_orphans=True
):  # pylint:disable=keyword-arg-before-vararg
    if filename is not None:
        filename_arg = '-f {filename} '.format(filename=filename)
    else:
        filename_arg = ''

    if remove_orphans:
        remove_orphans_arg = ' --remove-orphans'
    else:
        remove_orphans_arg = ''

    return (
        [
            "docker-compose {filename_arg}stop".format(filename_arg=filename_arg),
            "docker-compose {filename_arg}rm -f".format(filename_arg=filename_arg),
            "docker-compose {filename_arg}up -d{remove_orphans_arg}".format(
                filename_arg=filename_arg, remove_orphans_arg=remove_orphans_arg
            ),
        ]
        + steps_to_execute
        + [
            "docker-compose {filename_arg}stop".format(filename_arg=filename_arg),
            "docker-compose {filename_arg}rm -f".format(filename_arg=filename_arg),
        ]
    )


def python_modules_tox_tests(directory):
    label = directory.replace("/", "-")
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:

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
                "pip install tox",
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
                *wrap_with_docker_compose_steps(
                    # Can't use host networking on buildkite and communicate via localhost
                    # between these sibling containers, so pass along the ip.
                    network_buildkite_container('postgres')
                    + connect_sibling_docker_container(
                        'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                    )
                    + [
                        "tox -vv -c airline.tox -e {ver}".format(ver=TOX_MAP[version]),
                        "mv .coverage {file}".format(file=coverage),
                        "buildkite-agent artifact upload {file}".format(file=coverage),
                    ]
                )
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
                "mkdir -p /tmp/dagster/events",
                "pushd scala_modules",
                "sbt events/assembly",
                "cp ./events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar /tmp/dagster/events/",
                "popd",
                "pushd examples",
                "pip install tox",
                "tox -vv -c event.tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .build()
        )
    return tests


def publish_airflow_images():
    '''These images are used by the dagster-airflow tests. We build them here and not in the main
    build pipeline to speed it up, because they change very rarely.
    '''
    return [
        StepBuilder("[dagster-airflow] images", key="dagster-airflow-images")
        .run(
            "pip install awscli",
            "aws ecr get-login --no-include-email --region us-west-1 | sh",
            r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
            + GCP_CREDS_LOCAL_FILE,
            "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
            "export DAGSTER_AIRFLOW_DOCKER_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-airflow-demo:$${BUILDKITE_BUILD_ID}",
            # Build and deploy dagster-airflow docker images
            "pushd python_modules/dagster-airflow/dagster_airflow_tests/test_project",
            "./build.sh",
            "docker tag dagster-airflow-demo $${DAGSTER_AIRFLOW_DOCKER_IMAGE}",
            "docker push $${DAGSTER_AIRFLOW_DOCKER_IMAGE}",
            "popd",
        )
        .on_integration_image(
            SupportedPython.V3_7,
            [
                'AIRFLOW_HOME',
                'AWS_ACCOUNT_ID',
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY',
                'BUILDKITE_SECRETS_BUCKET',
            ],
        )
        .build()
    ]


def airflow_tests():
    tests = []
    # See: https://github.com/dagster-io/dagster/issues/1960
    for version in SupportedPythons + [SupportedPython.V3_8]:
        coverage = ".coverage.dagster-airflow.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("[dagster-airflow] ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pip install awscli",
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
                + GCP_CREDS_LOCAL_FILE,
                "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                "./.buildkite/scripts/dagster_airflow.sh {ver}".format(ver=TOX_MAP[version]),
                "pushd python_modules/dagster-airflow/",
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
                "popd",
            )
            .depends_on(["dagster-airflow-images"])
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
                *wrap_with_docker_compose_steps(
                    wrap_with_docker_compose_steps(
                        network_buildkite_container('postgres')
                        + connect_sibling_docker_container(
                            'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                        )
                        + network_buildkite_container('postgres_multi')
                        + connect_sibling_docker_container(
                            'postgres_multi',
                            'test-run-storage-db',
                            'POSTGRES_TEST_RUN_STORAGE_DB_HOST',
                        )
                        + connect_sibling_docker_container(
                            'postgres_multi',
                            'test-event-log-storage-db',
                            'POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST',
                        )
                        + [
                            "pushd ../",
                            "pip install tox",
                            "tox -e {ver}".format(ver=TOX_MAP[version]),
                            "mv .coverage {file}".format(file=coverage),
                            "buildkite-agent artifact upload {file}".format(file=coverage),
                            "popd",
                        ],
                        filename='docker-compose-multi.yml',
                        remove_orphans=False,
                    )
                )
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
                "pip install tox",
                *wrap_with_docker_compose_steps(
                    # Can't use host networking on buildkite and communicate via localhost
                    # between these sibling containers, so pass along the ip.
                    network_buildkite_container('postgres')
                    + connect_sibling_docker_container(
                        'postgres', 'test-postgres-db', 'POSTGRES_TEST_DB_HOST'
                    )
                    + [
                        "tox -e {ver}".format(ver=TOX_MAP[version]),
                        "mv .coverage {file}".format(file=coverage),
                        "buildkite-agent artifact upload {file}".format(file=coverage),
                    ]
                )
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
            "pip install tox",
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
                "pip install awscli",
                r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
                + GCP_CREDS_LOCAL_FILE,
                "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
                "pip install tox;",
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
    for version in SupportedPython3s:
        coverage = ".coverage.dagster-dask.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-dask tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd python_modules/dagster-dask/dagster_dask_tests/dask-docker",
                "./build.sh " + version,
                # Run the docker-compose dask cluster
                *wrap_with_docker_compose_steps(
                    network_buildkite_container('dask')
                    + connect_sibling_docker_container('dask', 'dask-scheduler', 'DASK_ADDRESS')
                    + [
                        "popd",
                        "pushd python_modules/dagster-dask/",
                        "pip install tox",
                        "tox -e {ver}".format(ver=TOX_MAP[version]),
                        "mv .coverage {file}".format(file=coverage),
                        "buildkite-agent artifact upload {file}".format(file=coverage),
                        "popd",
                        "pushd python_modules/dagster-dask/dagster_dask_tests/dask-docker",
                    ]
                )
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
    for library in library_modules:
        if library == 'dagster-gcp':
            tests += gcp_tests()
        elif library == 'dagster-postgres':
            tests += dagster_postgres_tests()
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
                "pip install tox;",
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
                "pip install tox;",
                "cd python_modules/lakehouse",
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
    for version in SupportedPythons + [SupportedPython.V3_8]:
        is_release = check_for_release()
        smoke_test_steps = (
            [
                "pip install pipenv",
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
    steps = pylint_steps() + [
        StepBuilder("isort")
        .run(
            "pip install isort>=4.3.21",
            "isort -rc examples python_modules",  # -sg seems to be broken
            "isort -rc -l 78 examples/dagster_examples/intro_tutorial",
            "git diff --exit-code",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("black")
        .run("pip install black==19.10b0", "make check_black")
        .on_integration_image(SupportedPython.V3_7)
        .build(),
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
            "pip install -r python_modules/dagit/dev-requirements.txt -qqq",
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
    ]
    steps += airline_demo_tests()
    steps += automation_tests()
    steps += events_demo_tests()
    steps += examples_tests()

    steps += publish_airflow_images()
    steps += airflow_tests()
    steps += dask_tests()

    steps += dagit_tests()
    steps += lakehouse_tests()
    steps += pipenv_smoke_tests()

    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests("dagstermill")
    steps += library_tests()

    steps += releasability_tests()

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
