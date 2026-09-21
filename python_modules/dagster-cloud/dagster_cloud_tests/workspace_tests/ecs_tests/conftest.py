from collections.abc import Generator

import moto
import pytest
from moto.backends import get_backend


@pytest.fixture(autouse=True)
def env(monkeypatch):
    # Prevent boto clients from actually connecting to AWS;
    # real connections should only happen in integration tests
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")


@pytest.fixture(scope="session")
def _session_mock_aws() -> Generator[None]:
    with moto.mock_aws():
        yield


# Services reset between test functions so each test sees a fresh state.
_SERVICES_TO_RESET = (
    "ses",
    "kms",
    "ec2",
    "cloudformation",
    "iam",
    "ecs",
    "logs",
    "servicediscovery",
)


@pytest.fixture
def aws_mock(_session_mock_aws: None) -> Generator[None]:
    yield
    for service_name in _SERVICES_TO_RESET:
        get_backend(service_name).reset()
