import threading
import time
from collections.abc import Iterator
from unittest import mock
from uuid import uuid4

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster_pipes import PipesMappingParamsLoader, open_dagster_pipes
from dagster_prefect.pipes import PrefectRun
from dagster_prefect.pipes_task import PIPES_PARAMS_TASK_ARGUMENT, PipesPrefectTaskClient
from dagster_prefect.resource import PrefectResource
from prefect import task
from prefect.client.schemas.objects import State
from prefect.settings import PREFECT_API_URL, temporary_settings
from prefect.states import Completed
from prefect.task_worker import serve

WORKER_STARTUP_SECONDS = 5
WORKER_LIFETIME_SECONDS = 60
UNREACHABLE_API_URL = "http://127.0.0.1:1/api"


@task
def summarize(as_of: str, dagster_pipes_params: dict[str, str] | None = None) -> None:
    with open_dagster_pipes(
        params_loader=PipesMappingParamsLoader(dagster_pipes_params or {})
    ) as pipes:
        pipes.report_asset_materialization(metadata={"rows": 100, "as_of": as_of})


class RecordingTaskClient(PipesPrefectTaskClient):
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


def materialize_with(client: PipesPrefectTaskClient, **run_kwargs):
    @asset
    def orders_summary(context: AssetExecutionContext):
        return client.run(context=context, task=summarize, **run_kwargs).get_materialize_result()

    return materialize([orders_summary], raise_on_error=True)


def test_pipes_payload_rides_in_a_task_argument(prefect_resource: PrefectResource) -> None:
    client = RecordingTaskClient(prefect=prefect_resource, poll_interval_seconds=0)
    task_run_id = uuid4()

    with mock.patch.object(summarize, "delay") as delay:
        delay.return_value = mock.Mock(task_run_id=task_run_id)
        assert materialize_with(client, parameters={"as_of": "2026-09-01"}).success

    _, kwargs = delay.call_args
    assert kwargs["as_of"] == "2026-09-01"
    payload = kwargs[PIPES_PARAMS_TASK_ARGUMENT]
    # What the task side hands to PipesMappingParamsLoader.
    assert "DAGSTER_PIPES_CONTEXT" in payload
    assert "DAGSTER_PIPES_MESSAGES" in payload

    assert client.launched[0] == PrefectRun(kind="task-run", id=task_run_id)


def test_positional_args_are_forwarded(prefect_resource: PrefectResource) -> None:
    client = RecordingTaskClient(prefect=prefect_resource, poll_interval_seconds=0)

    with mock.patch.object(summarize, "delay") as delay:
        delay.return_value = mock.Mock(task_run_id=uuid4())
        assert materialize_with(client, args=["2026-09-02"]).success

    args, kwargs = delay.call_args
    assert args == ("2026-09-02",)
    assert PIPES_PARAMS_TASK_ARGUMENT in kwargs


def test_launch_targets_the_resources_server(prefect_resource: PrefectResource) -> None:
    """`.delay()` reads the ambient Prefect settings, so the client has to override them."""
    client = RecordingTaskClient(prefect=prefect_resource, poll_interval_seconds=0)

    with temporary_settings({PREFECT_API_URL: UNREACHABLE_API_URL}):
        assert materialize_with(client, parameters={"as_of": "latest"}).success

    # Readable from the resource's server, which is not the one the ambient settings named.
    assert prefect_resource.get_task_run(client.launched[0].id) is not None


@pytest.fixture
def task_worker(prefect_api_url: str) -> Iterator[None]:
    """Serve `summarize` from a background thread.

    The thread needs `PREFECT_API_URL` set inside it: Prefect settings are context-local, so
    a new thread inherits none of the harness's, and a task worker refuses to run against
    the ephemeral API.
    """

    def run_worker() -> None:
        with temporary_settings({PREFECT_API_URL: prefect_api_url}):
            serve(summarize, timeout=WORKER_LIFETIME_SECONDS)

    threading.Thread(target=run_worker, daemon=True).start()
    time.sleep(WORKER_STARTUP_SECONDS)
    yield


def test_task_reports_back_through_pipes(
    prefect_resource: PrefectResource, task_worker: None
) -> None:
    client = PipesPrefectTaskClient(prefect=prefect_resource, poll_interval_seconds=1)

    result = materialize_with(client, parameters={"as_of": "2026-09-01"})

    assert result.success
    materialization = result.get_asset_materialization_events()[0].materialization
    assert materialization.metadata["rows"].value == 100
    assert materialization.metadata["as_of"].value == "2026-09-01"
