import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster_prefect.pipes import PrefectRun
from dagster_prefect.pipes_deployment import PipesPrefectDeploymentClient
from dagster_prefect.resource import PrefectResource
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.client.schemas.objects import State
from prefect.states import Completed

from dagster_prefect_tests.deployed_flow import orders_summary

DEPLOYMENT = "orders-summary/test"
WORK_POOL = "dagster-prefect-tests"
WORKER_STARTUP_SECONDS = 8


class RecordingDeploymentClient(PipesPrefectDeploymentClient):
    """Records what was launched, and reports success without waiting for a worker."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.launched: list[PrefectRun] = []

    def _launch(self, **kwargs) -> PrefectRun:
        prefect_run = super()._launch(**kwargs)
        self.launched.append(prefect_run)
        return prefect_run

    def _read_state(self, prefect_run: PrefectRun) -> State | None:
        return Completed()


@pytest.fixture
def deployment(prefect_resource: PrefectResource) -> str:
    """Register a deployment with no work pool. Nothing executes its runs."""
    with prefect_resource.get_client() as client:
        flow_id = client.create_flow(orders_summary)
        client.create_deployment(flow_id, name="test")
    return DEPLOYMENT


def materialize_with(client: PipesPrefectDeploymentClient, **run_kwargs):
    @asset
    def orders_summary_asset(context: AssetExecutionContext):
        return client.run(
            context=context, deployment=DEPLOYMENT, **run_kwargs
        ).get_materialize_result()

    return materialize([orders_summary_asset], raise_on_error=True)


def test_pipes_payload_rides_in_job_variable_env(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    assert materialize_with(client, parameters={"as_of": "2026-09-01"}).success

    launched = client.launched[0]
    assert launched.kind == "flow-run"

    flow_run = prefect_resource.get_flow_run(launched.id)
    assert flow_run.parameters == {"as_of": "2026-09-01"}
    assert flow_run.job_variables is not None
    env = flow_run.job_variables["env"]
    assert "DAGSTER_PIPES_CONTEXT" in env
    assert "DAGSTER_PIPES_MESSAGES" in env


def test_caller_job_variables_are_preserved(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    assert materialize_with(
        client,
        job_variables={"env": {"MY_VAR": "kept"}, "stream_output": False},
    ).success

    flow_run = prefect_resource.get_flow_run(client.launched[0].id)
    assert flow_run.job_variables is not None
    assert flow_run.job_variables["stream_output"] is False
    assert flow_run.job_variables["env"]["MY_VAR"] == "kept"
    assert "DAGSTER_PIPES_CONTEXT" in flow_run.job_variables["env"]


def test_tags_are_forwarded(prefect_resource: PrefectResource, deployment: str) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    assert materialize_with(client, tags=["dagster"]).success

    assert "dagster" in prefect_resource.get_flow_run(client.launched[0].id).tags


@pytest.fixture
def deployment_on_a_work_pool(
    prefect_resource: PrefectResource, prefect_api_url: str
) -> Iterator[str]:
    """A deployment on a process work pool, with a real worker executing its runs.

    The worker runs as a subprocess because it imports the flow's entrypoint in a fresh
    interpreter, which is also what makes this a genuine test of environment injection:
    nothing is shared with the test process except the filesystem.
    """
    tests_dir = Path(__file__).parent
    with prefect_resource.get_client() as client:
        client.create_work_pool(WorkPoolCreate(name=WORK_POOL, type="process"))
        flow_id = client.create_flow(orders_summary)
        client.create_deployment(
            flow_id,
            name="test",
            work_pool_name=WORK_POOL,
            entrypoint="deployed_flow.py:orders_summary",
            path=str(tests_dir),
        )

    worker = subprocess.Popen(
        ["prefect", "worker", "start", "--pool", WORK_POOL, "--type", "process"],
        env={**os.environ, "PREFECT_API_URL": prefect_api_url},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(WORKER_STARTUP_SECONDS)
        yield DEPLOYMENT
    finally:
        worker.terminate()
        worker.wait(timeout=30)


def test_flow_reports_back_through_pipes(
    prefect_resource: PrefectResource, deployment_on_a_work_pool: str
) -> None:
    """The flow's signature is untouched: it only calls `open_dagster_pipes()`."""
    client = PipesPrefectDeploymentClient(prefect=prefect_resource, poll_interval_seconds=1)

    result = materialize_with(client, parameters={"as_of": "2026-09-01"})

    assert result.success
    materialization = result.get_asset_materialization_events()[0].materialization
    assert materialization.metadata["rows"].value == 100
    assert materialization.metadata["as_of"].value == "2026-09-01"
    # The link back to Prefect survives on the asset, alongside what the flow reported.
    assert "/runs/flow-run/" in str(materialization.metadata["Prefect Run URL"].value)
