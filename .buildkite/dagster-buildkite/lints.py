"""Lints that enforce certain assumptions our build makes"""

import configparser
import os

import pytest


def find_tox_ini():
    tox_files = []
    for root, dirs, files in os.walk("."):
        if "tox.ini" in files:
            tox_file = os.path.join(root, "tox.ini")
            tox_files.append(tox_file)
    return tox_files


@pytest.fixture(params=find_tox_ini(), ids=lambda i: i)
def tox_config(request):
    config = configparser.ConfigParser()
    config.read(request.param)
    return config


def test_tox_passenv(tox_config):
    PASSENV_ENV = [
        "BUILDKITE*",
        "PYTEST_PLUGINS",
    ]

    assert "testenv" in tox_config
    assert "passenv" in tox_config["testenv"]

    missing_env = []
    for env in PASSENV_ENV:
        if env not in tox_config["testenv"]["passenv"].split("\n"):
            missing_env.append(env)

    assert not missing_env, f"tox.ini missing passenv {missing_env}"


def test_no_subdirectory_pytest_ini():
    pytest_ini_files = []
    for root, dirs, files in os.walk("."):
        if "pytest.ini" in files:
            pytest_ini_file = os.path.join(root, "tox.ini")
            pytest_ini_files.append(pytest_ini_file)

    assert (
        not pytest_ini_files
    ), f"Subdirectory pytest.ini conflict with root pyproject.toml {pytest_ini_files}"
