import os
import sys
import yaml

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)

from defines import SupportedPython, SupportedPythons, SupportedPython3s
from step_builder import StepBuilder

TOX_MAP = {
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}


def wait_step():
    return "wait"


def python_modules_tox_tests(directory, prereqs=None, env=None, integration=False):
    label = directory.replace("/", "-")
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
            label=label, version=version
        )
        tox_command = []
        if prereqs:
            tox_command += prereqs
        tox_command += [
            "pip install tox;",
            "cd python_modules/{directory}".format(directory=directory),
            "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
            "mv .coverage {file}".format(file=coverage),
            "buildkite-agent artifact upload {file}".format(file=coverage),
        ]

        env_vars = ['AWS_DEFAULT_REGION'] + (env or [])

        builder = StepBuilder(
            "{label} tests ({ver})".format(label=label, ver=TOX_MAP[version])
        ).run(*tox_command)

        if integration:
            builder = builder.on_integration_image(version, env_vars).on_medium_instance()
        else:
            builder = builder.on_python_image(version, env_vars)

        tests.append(builder.build())

    return tests


def airline_demo_tests():
    tests = []
    for version in SupportedPython3s:
        coverage = ".coverage.airline-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('airline-demo tests ({version})'.format(version=TOX_MAP[version]))
            .on_integration_image(version)
            .on_medium_instance()
            .run(
                "cd examples",
                # Build the image we use for airflow in the demo tests
                "./build_airline_demo_image.sh",
                "mkdir -p /home/circleci/airflow",
                # Run the postgres db. We are in docker running docker
                # so this will be a sibling container.
                "docker-compose stop",
                "docker-compose rm -f",
                "docker-compose up -d",
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                "export DAGSTER_AIRLINE_DEMO_DB_HOST=`docker inspect --format '{{ .NetworkSettings.IPAddress }}' airline-demo-db`",
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
            .on_medium_instance()
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


def airflow_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.dagster-airflow.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-airflow tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "cd python_modules/dagster-airflow/dagster_airflow_tests/test_project",
                "./build.sh",
                "mkdir -p /airflow",
                "export AIRFLOW_HOME=/airflow",
                "cd ../../",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version, ['AIRFLOW_HOME'])
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
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .on_medium_instance()
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
    # GCP tests need appropriate credentials
    creds_local_file = "/tmp/gcp-key-elementl-dev.json"

    return python_modules_tox_tests(
        "libraries/dagster-gcp",
        prereqs=[
            "pip install awscli",
            "aws s3 cp s3://${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
            + creds_local_file,
            "export GOOGLE_APPLICATION_CREDENTIALS=" + creds_local_file,
        ],
        env=['BUILDKITE_SECRETS_BUCKET', 'GCP_PROJECT_ID'],
    )


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
                "export PYTHON_VERSION=\"{ver}\"".format(ver=version),
                "docker-compose up -d --remove-orphans",
                # hold onto your hats, this is docker networking at its best. First, we figure out
                # the name of the currently running container...
                "export CONTAINER_ID=`cut -c9- < /proc/1/cpuset`",
                r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
                # then, we dynamically bind this container into the dask user-defined bridge
                # network to make the dask containers visible...
                r"docker network connect dask \${CONTAINER_NAME}",
                # Now, we grab the IP address of the dask-scheduler container from within the dask
                # bridge network and export it; this will let the tox tests talk to the scheduler.
                "export DASK_ADDRESS=`docker inspect --format '{{ .NetworkSettings.Networks.dask.IPAddress }}' dask-scheduler`",
                "popd",
                "pushd python_modules/dagster-dask/",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version, ['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION']
            )
            .on_medium_instance()
            .build()
        )
    return tests


def library_tests():
    library_path = os.path.join(SCRIPT_PATH, '..', 'python_modules/libraries/')
    library_modules = set(os.listdir(library_path))

    tests = []
    for library in library_modules:
        if library == 'dagster-pyspark':
            continue  # no tests :'(
        elif library == 'dagster-gcp':
            tests += gcp_tests()
        else:
            tests += python_modules_tox_tests("libraries/{library}".format(library=library))

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
        .on_python_image(
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


def deploy_trigger_step():
    return {'label': 'Deploy Trigger', 'trigger': 'deploy', 'branches': 'master', 'async': True}


if __name__ == "__main__":
    steps = [
        StepBuilder("pylint")
        .run("make install_dev_python_modules", "make pylint")
        .on_integration_image(SupportedPython.V3_7)
        .on_medium_instance()
        .build(),
        StepBuilder("black")
        # black 18.9b0 doesn't support py27-compatible formatting of the below invocation (omitting
        # the trailing comma after **check.opt_dict_param...) -- black 19.3b0 supports multiple
        # python versions, but currently doesn't know what to do with from __future__ import
        # print_function -- see https://github.com/ambv/black/issues/768
        .run("pip install black==18.9b0", "make check_black")
        .on_python_image(SupportedPython.V3_7)
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
            "pip install -e python_modules/libraries/dagster-slack -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -r python_modules/dagit/dev-requirements.txt -qqq",
            "pip install -e examples -qqq",
            "cd js_modules/dagit",
            "yarn install --offline",
            "yarn run ts",
            "yarn run jest",
            "yarn run check-prettier",
            "yarn run download-schema",
            "yarn run generate-types",
            "git diff --exit-code",
            "mv coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .on_medium_instance()
        .build(),
    ]
    steps += airline_demo_tests()
    steps += automation_tests()
    steps += events_demo_tests()
    steps += airflow_tests()
    steps += dask_tests()

    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests(
        "dagit",
        prereqs=[
            "apt-get update",
            "apt-get install -y xdg-utils",
            "pushd python_modules",
            "make rebuild_dagit",
            "popd",
        ],
        integration=True,
    )
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests("dagstermill")

    steps += library_tests()

    steps += examples_tests()
    steps += [wait_step(), coverage_step(), wait_step(), deploy_trigger_step()]

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
