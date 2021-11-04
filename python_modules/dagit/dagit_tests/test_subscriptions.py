import gc
from contextlib import contextmanager
from unittest import mock

import objgraph
import pytest
from dagit.subscription_server import DagsterSubscriptionServer
from dagster import execute_pipeline, pipeline, solid
from dagster.core.test_utils import environ, instance_for_test
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster.core.workspace.load_target import WorkspaceFileTarget
from dagster.utils import file_relative_path
from dagster_graphql.schema import create_schema
from graphql_ws.constants import GQL_CONNECTION_INIT, GQL_CONNECTION_TERMINATE, GQL_START, GQL_STOP
from graphql_ws.gevent import GeventConnectionContext

EVENT_LOG_SUBSCRIPTION = """
    subscription PipelineRunLogsSubscription($runId: ID!) {
        pipelineRunLogs(runId: $runId) {
            __typename
        }
    }
"""

COMPUTE_LOG_SUBSCRIPTION = """
    subscription ComputeLogsSubscription(
        $runId: ID!
        $stepKey: String!
        $ioType: ComputeIOType!
    ) {
        computeLogs(runId: $runId, stepKey: $stepKey, ioType: $ioType) {
            __typename
        }
    }
"""


@contextmanager
def create_subscription_context(instance):
    ws = mock.Mock()
    yaml_paths = [file_relative_path(__file__, "./workspace.yaml")]

    with WorkspaceProcessContext(
        instance=instance,
        workspace_load_target=WorkspaceFileTarget(paths=yaml_paths),
        version="",
        read_only=True,
    ) as process_context:
        yield GeventConnectionContext(ws, process_context)


def send_subscription_message(server, context, op, payload=None):
    server.on_message(context, {"id": 1, "type": op, "payload": payload or {}})


def start_subscription(server, context, query=None, variables=None):
    if query:
        start_payload = {
            "query": query,
            "variables": variables or {},
        }
    else:
        start_payload = {}

    send_subscription_message(server, context, GQL_CONNECTION_INIT)
    send_subscription_message(server, context, GQL_START, start_payload)


def end_subscription(server, context):
    send_subscription_message(server, context, GQL_STOP)
    send_subscription_message(server, context, GQL_CONNECTION_TERMINATE)


@solid
def example_solid():
    return 1


@pipeline
def example_pipeline():
    example_solid()


def test_generic_subscriptions():
    server = DagsterSubscriptionServer(schema=None)
    with instance_for_test() as instance:
        with create_subscription_context(instance) as context:
            start_subscription(server, context)
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 1
            end_subscription(server, context)
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 0


def test_event_log_subscription():
    schema = create_schema()
    server = DagsterSubscriptionServer(schema=schema)

    with instance_for_test() as instance:
        run = execute_pipeline(example_pipeline, instance=instance)
        assert run.success
        assert run.run_id

        with create_subscription_context(instance) as context:
            start_subscription(server, context, EVENT_LOG_SUBSCRIPTION, {"runId": run.run_id})
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 1
            assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 1
            end_subscription(server, context)
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 0
            assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 0


@pytest.mark.skip(
    "PipelineRunObservableSubscribe GC check is flaky - see https://github.com/dagster-io/dagster/issues/4917"
)
def test_event_log_subscription_chunked():
    schema = create_schema()
    server = DagsterSubscriptionServer(schema=schema)

    with instance_for_test() as instance, environ({"DAGIT_EVENT_LOAD_CHUNK_SIZE": "2"}):
        run = execute_pipeline(example_pipeline, instance=instance)
        assert run.success
        assert run.run_id

        with create_subscription_context(instance) as context:
            start_subscription(server, context, EVENT_LOG_SUBSCRIPTION, {"runId": run.run_id})
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 1
            subs = objgraph.by_type("PipelineRunObservableSubscribe")
            assert len(subs) == 1
            subscription_obj = subs[0]
            end_subscription(server, context)
            subscription_obj.stopped.wait(30)
            subs = None
            subscription_obj = None
            gc.collect()

            assert len(objgraph.by_type("SubscriptionObserver")) == 0
            assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 0


@mock.patch(
    "dagster.core.storage.local_compute_log_manager.LocalComputeLogManager.is_watch_completed"
)
def test_compute_log_subscription(mock_watch_completed):
    mock_watch_completed.return_value = False

    schema = create_schema()
    server = DagsterSubscriptionServer(schema=schema)

    with instance_for_test() as instance:
        run = execute_pipeline(example_pipeline, instance=instance)
        assert run.success
        assert run.run_id

        with create_subscription_context(instance) as context:
            start_subscription(
                server,
                context,
                COMPUTE_LOG_SUBSCRIPTION,
                {"runId": run.run_id, "stepKey": "example_solid", "ioType": "STDERR",},
            )
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 1
            assert len(objgraph.by_type("ComputeLogSubscription")) == 1
            end_subscription(server, context)
            gc.collect()
            assert len(objgraph.by_type("SubscriptionObserver")) == 0
            assert len(objgraph.by_type("ComputeLogSubscription")) == 0
