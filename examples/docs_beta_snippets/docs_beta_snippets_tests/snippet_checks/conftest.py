from collections.abc import Iterator

import pytest


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
