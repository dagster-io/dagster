import gc
import sys
from contextlib import contextmanager
from typing import Iterator
from unittest import mock

import objgraph
import pytest
from dagster import job, op
from dagster._core.test_utils import environ, instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import WorkspaceFileTarget
from dagster._utils import file_relative_path
from dagster_webserver.graphql import GraphQLWS
from dagster_webserver.webserver import DagsterWebserver
from starlette.testclient import TestClient

EVENT_LOG_SUBSCRIPTION = """
    subscription PipelineRunLogsSubscription($runId: ID!) {
        pipelineRunLogs(runId: $runId) {
            __typename
        }
    }
"""

CAPTURED_LOGS_SUBSCRIPTION = """
  subscription CapturedLogsSubscription($logKey: [String!]!) {
    capturedLogs(logKey: $logKey) {
      stdout
      stderr
      cursor
    }
  }
"""


@contextmanager
def create_asgi_client(instance) -> Iterator[TestClient]:
    yaml_paths = [file_relative_path(__file__, "./workspace.yaml")]

    with WorkspaceProcessContext(
        instance=instance,
        workspace_load_target=WorkspaceFileTarget(paths=yaml_paths),
        version="",
        read_only=True,
    ) as process_context:
        yield TestClient(DagsterWebserver(process_context).create_asgi_app())


def send_subscription_message(ws, op, payload=None):
    ws.send_json({"id": 1, "type": op, "payload": payload or {}})


def start_connection(ws):
    send_subscription_message(ws, GraphQLWS.CONNECTION_INIT)
    ws.receive_json()


def end_connection(ws):
    send_subscription_message(ws, GraphQLWS.CONNECTION_TERMINATE)
    ws.close()


def start_subscription(ws, query, variables=None):
    start_payload = {
        "query": query,
        "variables": variables or {},
    }

    send_subscription_message(ws, GraphQLWS.START, start_payload)


def end_subscription(ws):
    send_subscription_message(ws, GraphQLWS.STOP)


@op
def example_op():
    return 1


@job
def example_job():
    example_op()


@pytest.fixture(scope="module")
def instance():
    with instance_for_test() as instance:
        yield instance


@pytest.fixture(scope="module")
def asgi_client(instance):
    with create_asgi_client(instance) as client:
        yield client


@pytest.fixture(scope="module")
def run_id(instance):
    run = example_job.execute_in_process(instance=instance)
    assert run.success
    assert run.run_id
    return run.run_id


def test_event_log_subscription(asgi_client, run_id) -> None:
    with asgi_client.websocket_connect("/graphql", GraphQLWS.PROTOCOL) as ws:
        assert str(ws.accepted_subprotocol) == "graphql-ws"
        start_connection(ws)
        start_subscription(ws, EVENT_LOG_SUBSCRIPTION, {"runId": run_id})

        rx = ws.receive_json()
        assert rx["type"] != GraphQLWS.ERROR, rx

        start_subscription(
            ws, EVENT_LOG_SUBSCRIPTION, {"runId": run_id}
        )  # duplicate starts ignored

        gc.collect()
        assert len(objgraph.by_type("async_generator")) == 1
        end_subscription(ws)

        # can restart on the same connection
        start_subscription(ws, EVENT_LOG_SUBSCRIPTION, {"runId": run_id})
        rx = ws.receive_json()
        assert rx["type"] != GraphQLWS.ERROR, rx
        end_subscription(ws)

        end_connection(ws)

    gc.collect()
    assert len(objgraph.by_type("async_generator")) == 0


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Inconsistent GC on the async_generator in 3.7",
)
def test_event_log_subscription_chunked(asgi_client, run_id):
    with (
        environ({"DAGSTER_WEBSERVER_EVENT_LOAD_CHUNK_SIZE": "2"}),
        asgi_client.websocket_connect("/graphql", GraphQLWS.PROTOCOL) as ws,
    ):
        start_connection(ws)
        start_subscription(ws, EVENT_LOG_SUBSCRIPTION, {"runId": run_id})
        rx = ws.receive_json()
        assert rx["type"] != GraphQLWS.ERROR, rx
        gc.collect()
        assert len(objgraph.by_type("async_generator")) == 1

        end_subscription(ws)
        end_connection(ws)

    gc.collect()
    assert len(objgraph.by_type("async_generator")) == 0


@mock.patch(
    "dagster._core.storage.local_compute_log_manager.LocalComputeLogManager.is_capture_complete"
)
def test_captured_log_subscription(mock_capture_completed, asgi_client, run_id):
    mock_capture_completed.return_value = False

    with asgi_client.websocket_connect("/graphql", GraphQLWS.PROTOCOL) as ws:
        start_connection(ws)
        start_subscription(
            ws,
            CAPTURED_LOGS_SUBSCRIPTION,
            {
                "logKey": [run_id, "compute_logs", "example_op"],
            },
        )
        rx = ws.receive_json()
        assert rx["type"] != GraphQLWS.ERROR, rx

        gc.collect()
        assert len(objgraph.by_type("CapturedLogSubscription")) == 1
        end_subscription(ws)

    gc.collect()
    assert len(objgraph.by_type("CapturedLogSubscription")) == 0
