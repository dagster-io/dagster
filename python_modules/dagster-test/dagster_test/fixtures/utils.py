import os
import signal

import pytest
import requests
from urllib3.util.retry import Retry

BUILDKITE = os.environ.get("BUILDKITE") is not None


@pytest.fixture(scope="session", autouse=True)
def sigterm_handler():
    # pytest finalizers don't run on SIGTERM; only SIGINT.
    # When Buildkite terminates, it sends a SIGTERM.
    # Intercept SIGTERM and send SIGINT instead.
    # https://github.com/pytest-dev/pytest/issues/5243
    original = signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))

    yield

    signal.signal(signal.SIGTERM, original)


@pytest.fixture
def retrying_requests():
    session = requests.Session()
    session.mount(
        "http://", requests.adapters.HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1))
    )
    yield session


@pytest.fixture
def test_directory(request):
    yield os.path.dirname(request.fspath)


@pytest.fixture
def test_id(testrun_uid):
    yield testrun_uid
