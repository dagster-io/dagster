import json
import os
import subprocess
import threading
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

import pytest
from dagster import AssetExecutionContext, DagsterInstance, asset, materialize
from dagster_pipes import (
    PipesContext,
    PipesMappingParamsLoader,
    PipesPrefectLogsMessageWriter,
    _make_message,
    open_dagster_pipes,
)
from dagster_prefect.message_readers import LOOKBACK, PipesPrefectLogsMessageReader
from dagster_prefect.pipes_deployment import PipesPrefectDeploymentClient
from dagster_prefect.pipes_task import PipesPrefectTaskClient
from dagster_prefect.resource import PrefectResource
from prefect import task
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.client.schemas.objects import Log
from prefect.settings import PREFECT_API_URL, temporary_settings
from prefect.task_worker import serve

from dagster_prefect_tests.logs_flows import (
    PLAIN_LOG_LINE,
    no_pipes,
    reports_through_logs,
    reports_too_much,
)

WORK_POOL = "dagster-prefect-logs-tests"
WORKER_STARTUP_SECONDS = 8
WORKER_LIFETIME_SECONDS = 60


@pytest.fixture(autouse=True)
def fresh_pipes_context() -> Iterator[None]:
    # `open_dagster_pipes` hands back an existing context, even a closed one, and the task
    # test opens one in this process.
    PipesContext._instance = None  # noqa: SLF001
    yield
    PipesContext._instance = None  # noqa: SLF001


@pytest.fixture(scope="module")
def flow_worker(prefect_api_url: str) -> Iterator[None]:
    """Deploy the flows in `logs_flows.py` on a process work pool, with a worker running them."""
    with PrefectResource(api_url=prefect_api_url).get_client() as client:
        client.create_work_pool(WorkPoolCreate(name=WORK_POOL, type="process"))
        for entrypoint, flow in (
            ("reports_through_logs", reports_through_logs),
            ("reports_too_much", reports_too_much),
            ("no_pipes", no_pipes),
        ):
            flow_id = client.create_flow(flow)
            client.create_deployment(
                flow_id,
                name="test",
                work_pool_name=WORK_POOL,
                entrypoint=f"logs_flows.py:{entrypoint}",
                path=str(Path(__file__).parent),
            )

    worker = subprocess.Popen(
        ["prefect", "worker", "start", "--pool", WORK_POOL, "--type", "process"],
        env={**os.environ, "PREFECT_API_URL": prefect_api_url, "PREFECT_WORKER_QUERY_SECONDS": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(WORKER_STARTUP_SECONDS)
        yield
    finally:
        worker.terminate()
        worker.wait(timeout=30)


def run_deployment(prefect_resource: PrefectResource, deployment: str):
    client = PipesPrefectDeploymentClient(
        prefect=prefect_resource,
        message_reader=PipesPrefectLogsMessageReader(prefect=prefect_resource, interval=1),
        poll_interval_seconds=1,
    )

    @asset
    def orders_summary(context: AssetExecutionContext):
        return client.run(context=context, deployment=deployment).get_materialize_result()

    instance = DagsterInstance.ephemeral()
    result = materialize([orders_summary], instance=instance, raise_on_error=True)
    assert result.success
    log_messages = [entry.user_message for entry in instance.all_logs(result.run_id)]
    return result, log_messages


def test_flow_reports_back_through_its_logs(
    prefect_resource: PrefectResource, flow_worker: None, capsys
) -> None:
    result, _ = run_deployment(prefect_resource, "reports-through-logs/test")

    materialization = result.get_asset_materialization_events()[0].materialization
    assert materialization.metadata["rows"].value == 100
    # The flow's other logs are forwarded to the step's stdout.
    assert PLAIN_LOG_LINE in capsys.readouterr().out


def test_oversize_message_is_reported_instead_of_lost(
    prefect_resource: PrefectResource, flow_worker: None
) -> None:
    result, log_messages = run_deployment(prefect_resource, "reports-too-much/test")

    materialization = result.get_asset_materialization_events()[0].materialization
    assert "blob" not in materialization.metadata
    assert any("Dropped a `report_asset_materialization`" in m for m in log_messages)


def test_flow_without_pipes_explains_what_is_missing(
    prefect_resource: PrefectResource, flow_worker: None
) -> None:
    _, log_messages = run_deployment(prefect_resource, "no-pipes/test")

    [warning] = [m for m in log_messages if "did not receive any messages" in m]
    assert "PipesPrefectLogsMessageWriter" in warning


@task
def summarize_through_logs(dagster_pipes_params: dict[str, str] | None = None) -> None:
    with open_dagster_pipes(
        params_loader=PipesMappingParamsLoader(dagster_pipes_params or {}),
        message_writer=PipesPrefectLogsMessageWriter(),
    ) as pipes:
        pipes.report_asset_materialization(metadata={"rows": 100})


@pytest.fixture
def task_worker(prefect_api_url: str) -> Iterator[None]:
    """Serve `summarize_through_logs` from a background thread, as `test_pipes_task.py` does."""

    def run_worker() -> None:
        with temporary_settings({PREFECT_API_URL: prefect_api_url}):
            serve(summarize_through_logs, timeout=WORKER_LIFETIME_SECONDS)

    threading.Thread(target=run_worker, daemon=True).start()
    time.sleep(5)
    yield


def test_background_task_reports_back_through_its_logs(
    prefect_resource: PrefectResource, task_worker: None
) -> None:
    client = PipesPrefectTaskClient(
        prefect=prefect_resource,
        message_reader=PipesPrefectLogsMessageReader(prefect=prefect_resource, interval=1),
        poll_interval_seconds=1,
    )

    @asset
    def orders_summary(context: AssetExecutionContext):
        return client.run(context=context, task=summarize_through_logs).get_materialize_result()

    result = materialize([orders_summary], raise_on_error=True)

    assert result.success
    materialization = result.get_asset_materialization_events()[0].materialization
    assert materialization.metadata["rows"].value == 100


def _log(message: str, seconds: float) -> Log:
    return Log(
        name="prefect.flow_runs",
        level=20,
        message=message,
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds),
        flow_run_id=uuid4(),
    )


def test_rereads_are_deduped_and_late_logs_picked_up(prefect_resource: PrefectResource) -> None:
    reader = PipesPrefectLogsMessageReader(prefect=prefect_resource)
    opened = _log(json.dumps(_make_message("opened", {})), 0)
    first = _log("hello", 1)
    late = _log(json.dumps(_make_message("log", {})), 0.5)

    with mock.patch.object(reader, "_read_logs", return_value=[opened, first]) as read_logs:
        cursor, chunk = reader.download_messages(None, {}) or pytest.fail("expected messages")
    read_logs.assert_called_once_with(None)
    assert chunk == opened.message

    # The next read goes back past the cursor, sees both again, and a log that landed late.
    with mock.patch.object(reader, "_read_logs", return_value=[opened, late, first]) as read_logs:
        _, chunk = reader.download_messages(cursor, {}) or pytest.fail("expected messages")
    read_logs.assert_called_once_with(first.timestamp - LOOKBACK)
    assert chunk == late.message

    with mock.patch.object(reader, "_read_logs", return_value=[opened, first]):
        assert reader.download_messages(cursor, {}) is None


def test_seen_ids_outside_the_lookback_are_dropped(prefect_resource: PrefectResource) -> None:
    reader = PipesPrefectLogsMessageReader(prefect=prefect_resource)
    old, recent = _log("old", 0), _log("recent", 60)

    with mock.patch.object(reader, "_read_logs", return_value=[old, recent]):
        cursor, _ = reader.download_messages(None, {}) or pytest.fail("expected messages")

    assert set(cursor.seen) == {recent.id}
