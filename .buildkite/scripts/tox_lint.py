import configparser
import os

PASSENV_ENV = [
    "BUILDKITE*",
    "PYTEST_PLUGINS",
]


def report_failure(failure: str) -> bool:
    print(f"    {failure}")  # noqa
    return True


def lint_passenv(tox_config: configparser.ConfigParser) -> bool:
    failures = False

    if "testenv" not in tox_config:
        failures |= report_failure('Missing "testenv" section')

    try:
        if "passenv" not in tox_config["testenv"]:
            failures |= report_failure('Missing "passenv" section')
    except KeyError:
        pass

    try:
        configured_env = tox_config["testenv"]["passenv"].split("\n")
        for env in PASSENV_ENV:
            if env not in configured_env:
                failures |= report_failure(f"{env} is not set")
    except KeyError:
        pass

    return not failures


if __name__ == "__main__":
    passing = True
    for root, dirs, files in os.walk("."):
        if "tox.ini" in files:
            tox_file = os.path.join(root, "tox.ini")

            config = configparser.ConfigParser()
            config.read(tox_file)

            print(f"Linting {tox_file}")  # noqa

            passing &= lint_passenv(config)

    assert passing
