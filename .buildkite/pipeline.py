import yaml

DOCKER_PLUGIN = "docker#v3.1.0"


# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_7 = "3.7"
    V3_6 = "3.6"
    V3_5 = "3.5"
    V2_7 = "2.7"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

PY_IMAGE_MAP = {
    SupportedPython.V3_7: "python:3.7",
    SupportedPython.V3_6: "python:3.6",
    SupportedPython.V3_5: "python:3.5",
    SupportedPython.V2_7: "python:2.7",
}

INTEGRATION_IMAGE_MAP = {
    SupportedPython.V3_7: "dagster/buildkite-integration:py3.7.3",
    SupportedPython.V3_6: "dagster/buildkite-integration:py3.6.8",
    SupportedPython.V3_5: "dagster/buildkite-integration:py3.5.7",
    SupportedPython.V2_7: "dagster/buildkite-integration:py2.7.16",
}

TOX_MAP = {
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}


class StepBuilder:
    def __init__(self, label):
        self._step = {"label": label}

    def run(self, *argc):
        self._step["command"] = "\n".join(argc)
        return self

    def on_python_image(self, ver, env=None):
        settings = {"always-pull": True, "image": PY_IMAGE_MAP[ver]}
        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]

        return self

    def on_integration_image(self, ver, env=None):
        settings = {
            "always-pull": True,
            "image": INTEGRATION_IMAGE_MAP[ver],
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
        }

        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]
        return self

    def build(self):
        return self._step


def wait_step():
    return "wait"


def python_modules_tox_tests(directory, prereqs=None):
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
            "tox -e {ver}".format(ver=TOX_MAP[version]),
            "mv .coverage {file}".format(file=coverage),
            "buildkite-agent artifact upload {file}".format(file=coverage),
        ]
        tests.append(
            StepBuilder("{label} tests ({ver})".format(label=label, ver=TOX_MAP[version]))
            .run(*tox_command)
            .on_python_image(version, ['AWS_DEFAULT_REGION'])
            .build()
        )

    return tests


def airline_demo_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.airline-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('airline-demo tests ({version})'.format(version=TOX_MAP[version]))
            .run(
                "cd examples/airline-demo",
                # Build the image we use for airflow in the demo tests
                "./build.sh",
                "mkdir -p /home/circleci/airflow",
                # Run the postgres db. We are in docker running docker
                # so this will be a sibling container.
                "docker-compose up -d --remove-orphans",
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                "export DAGSTER_AIRLINE_DEMO_DB_HOST=`docker inspect --format '{{ .NetworkSettings.IPAddress }}' airline-demo-db`",
                "pip install tox",
                "apt-get update",
                "apt-get -y install libpq-dev",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )
    return tests


def events_demo_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.events-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('events-demo tests ({version})'.format(version=TOX_MAP[version]))
            .run(
                "mkdir -p /tmp/dagster/events",
                "cd scala_modules",
                "sbt events/assembly",
                "cp ./events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar /tmp/dagster/events/",
                "cd ../examples/event-pipeline-demo",
                "pip install tox",
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


def airflow_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.dagster-airflow.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-airflow tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "cd python_modules/dagster-airflow/dagster_airflow_tests/test_project",
                "./build.sh",
                "mkdir -p /home/circleci/airflow",
                "cd ../../",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )
    return tests


if __name__ == "__main__":
    steps = [
        StepBuilder("pylint")
        .run("make install_dev_python_modules", "make pylint")
        .on_python_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("black")
        # black 18.9b0 doesn't support py27-compatible formatting of the below invocation (omitting
        # the trailing comma after **check.opt_dict_param...) -- black 19.3b0 supports multiple python
        # versions, but currently doesn't know what to do with from __future__ import print_function --
        # see https://github.com/ambv/black/issues/768
        .run("pip install black==18.9b0", "make check_black")
        .on_python_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("docs snapshot test")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pytest -vv python_modules/dagster/docs",
        )
        .on_python_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("dagit webapp tests")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/dagster-graphql -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -r python_modules/dagit/dev-requirements.txt -qqq",
            "cd js_modules/dagit",
            "yarn install --offline",
            "yarn run ts",
            "yarn run jest",
            "yarn run check-prettier",
            "yarn generate-types",
            "git diff --exit-code",
            "mv coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests("dagit", ["apt-get update", "apt-get install -y xdg-utils"])
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests("dagstermill")
    steps += python_modules_tox_tests("libraries/dagster-pandas")
    steps += python_modules_tox_tests("libraries/dagster-ge")
    steps += python_modules_tox_tests("libraries/dagster-aws")
    steps += python_modules_tox_tests("libraries/dagster-snowflake")
    steps += python_modules_tox_tests("libraries/dagster-spark")
    steps += airline_demo_tests()
    steps += events_demo_tests()
    steps += airflow_tests()
    steps += [
        wait_step(),  # wait for all previous steps to finish
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
            "coveralls-merge coverage.js.json",
        )
        .on_python_image(
            SupportedPython.V3_7,
            # COVERALLS_REPO_TOKEN exported by /env in ManagedSecretsBucket
            ['COVERALLS_REPO_TOKEN', 'BUILDKITE_PULL_REQUEST', 'BUILDKITE_JOB_ID', 'BUILDKITE'],
        )
        .build(),
    ]

    print(yaml.dump({"steps": steps}, default_flow_style=False, default_style="|"))
