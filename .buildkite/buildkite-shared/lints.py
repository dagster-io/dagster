"""Lints that enforce certain assumptions our build makes."""

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

    assert "testenv" in config
    assert "passenv" in config["testenv"]

    return config


def test_tox_passenv(tox_config):
    PASSENV_ENV = [
        "BUILDKITE*",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    ]

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

    assert not pytest_ini_files, (
        f"Subdirectory pytest.ini files conflict with our root pyproject.toml settings and conftest.py discovery. Please remove: {pytest_ini_files}"
    )


def test_no_tox_pytest_config_override(tox_config):
    if "commands" in tox_config["testenv"]:
        assert "pyproject.toml" not in tox_config["testenv"]["commands"], (
            "We use a global PYTEST_CONFIG that uses the root directory's pyproject.toml. Remove any -c overrides in pytest commands in tox.ini"
        )
