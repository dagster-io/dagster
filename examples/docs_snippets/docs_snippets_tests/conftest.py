import os

import boto3
import pytest
from dagster_dg_core.context import DG_UPDATE_CHECK_ENABLED_ENV_VAR
from moto import mock_s3

from dagster import file_relative_path


@pytest.fixture
def docs_snippets_folder():
    return file_relative_path(__file__, "../docs_snippets/")


@pytest.fixture
def mock_s3_resource():
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")


# ########################
# ##### SNIPPET CHECKS
# ########################


# Runs once before every test
def pytest_configure():
    # Disable the dg update check for all tests because we don't want to bomb the PyPI API.
    # Tests that specifically want to test the update check should set this env var to "1".
    os.environ[DG_UPDATE_CHECK_ENABLED_ENV_VAR] = "0"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-snippets",
        action="store_true",
    )
    parser.addoption(
        "--update-screenshots",
        action="store_true",
    )


@pytest.fixture
def update_snippets(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-snippets"))


@pytest.fixture
def update_screenshots(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-screenshots"))


@pytest.fixture(scope="session")
def get_selenium_driver():
    from selenium import webdriver

    driver = None

    try:

        def _get_driver():
            nonlocal driver
            if driver is None:
                driver = webdriver.Chrome()
            return driver

        yield _get_driver
    finally:
        if driver:
            driver.quit()
