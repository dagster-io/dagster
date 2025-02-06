import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-snippets",
        action="store_true",
    )


@pytest.fixture
def update_snippets(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-snippets"))
