import time
from collections.abc import Iterator

import pytest
from dagster_prefect.resource import PrefectResource, is_final_state
from prefect import flow, task
from prefect.exceptions import ObjectNotFound
from prefect.runtime import task_run as task_run_runtime
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


@task
def report_task_run_id() -> str:
    return task_run_runtime.id


@flow(name="with-a-task")
def with_a_task() -> str:
    return report_task_run_id()


def _is_finished(prefect_resource: PrefectResource, task_run_id: str) -> bool:
    try:
        task_run = prefect_resource.get_task_run(task_run_id)
    except ObjectNotFound:
        return False
    return is_final_state(task_run.state)


@pytest.fixture
def finished_task_run_id(prefect_resource: PrefectResource) -> str:
    """Run a flow with one task, and wait until the API reports that task's final state.

    The flow returns as soon as the task does, but Prefect records task runs asynchronously,
    so for a moment the API can report the task run as missing or still Running.
    """
    task_run_id = with_a_task()
    deadline = time.monotonic() + 30
    while not _is_finished(prefect_resource, task_run_id):
        assert time.monotonic() < deadline, f"task run {task_run_id} never reached a final state"
        time.sleep(0.2)
    return task_run_id
