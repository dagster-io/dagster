from collections.abc import Iterator

import pytest
from dagster_prefect.resource import PrefectResource
from prefect.settings import get_current_settings
from prefect.testing.utilities import prefect_test_harness

from dagster_prefect_tests.deployed_flow import orders_summary


@pytest.fixture(scope="session")
def prefect_api_url() -> Iterator[str]:
    """Run a Prefect server backed by a temporary SQLite database, and yield its API URL.

    Session-scoped because the harness swaps global Prefect settings and takes a few seconds
    to come up.
    """
    with prefect_test_harness():
        api_url = get_current_settings().api.url
        assert api_url, "Prefect test harness did not set an API URL"
        yield api_url


@pytest.fixture
def prefect_resource(prefect_api_url: str) -> PrefectResource:
    return PrefectResource(api_url=prefect_api_url)


DEPLOYMENT = "orders-summary/test"


@pytest.fixture
def deployment(prefect_resource: PrefectResource) -> str:
    """Register a deployment with no work pool. Nothing executes its runs."""
    with prefect_resource.get_client() as client:
        flow_id = client.create_flow(orders_summary)
        client.create_deployment(flow_id, name="test")
    return DEPLOYMENT
