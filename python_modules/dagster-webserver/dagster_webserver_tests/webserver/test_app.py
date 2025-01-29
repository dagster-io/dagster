import gc

import objgraph
import pytest
from dagster import (
    __version__ as dagster_version,
    job,
    op,
)
from dagster._core.events import DagsterEventType
from dagster._serdes import unpack_value
from dagster._seven import json
from dagster._utils.error import SerializableErrorInfo
from dagster_graphql.version import __version__ as dagster_graphql_version
from dagster_webserver.graphql import GraphQLWS
from dagster_webserver.version import __version__ as dagster_webserver_version
from starlette.testclient import TestClient

EVENT_LOG_SUBSCRIPTION = """
subscription PipelineRunLogsSubscription($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
    }
}
"""

RUN_QUERY = """
query RunQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
        __typename
        ... on Run {
            id
        }
        ... on PythonError {
            message
        }
    }
}
"""


def _add_run(instance):
    @op
    def my_op():
        print("STDOUT RULEZ")  # noqa: T201

    @job
    def _simple_job():
        my_op()

    result = _simple_job.execute_in_process(instance=instance)
    assert result.success
    return result.run_id


@pytest.mark.parametrize("path", ["/server_info", "/dagit_info"])
def test_dagster_webserver_info(path: str, test_client: TestClient):
    response = test_client.get(path)
    assert response.status_code == 200
    assert response.json() == {
        "dagster_webserver_version": dagster_webserver_version,
        "dagster_version": dagster_version,
        "dagster_graphql_version": dagster_graphql_version,
    }


def test_static_resources(test_client: TestClient):
    # make sure we did not fallback to the index html
    # for static resources at /
    for address in [
        "/manifest.json",
        "/favicon.ico",
        "/favicon.png",
        "/favicon.svg",
        "/favicon-run-pending.svg",
        "/favicon-run-failed.svg",
        "/favicon-run-success.svg",
        "/robots.txt",
    ]:
        response = test_client.get(address)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] != "text/html"

    response = test_client.get("/vendor/graphql-playground/middleware.js")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] != "application/js"


# https://graphql.org/learn/serving-over-http/


def test_graphql_get(instance, test_client: TestClient):
    # base case
    response = test_client.get(
        "/graphql",
        params={"query": "{__typename}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}

    # missing
    response = test_client.get("/graphql")
    assert response.status_code == 400, response.text

    # variables
    var_str = json.dumps({"runId": "missing"})
    response = test_client.get(
        "/graphql",
        params={"query": RUN_QUERY, "variables": var_str},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"pipelineRunOrError": {"__typename": "RunNotFoundError"}}}

    # malformed vars
    response = test_client.get(
        "/graphql",
        params={
            "query": RUN_QUERY,
            "variables": var_str[:-2],  # malform by trimming
        },
    )
    assert response.status_code == 400, response.text


def test_graphql_invalid_json(instance, test_client: TestClient):
    # base case
    response = test_client.post(
        "/graphql",
        content='{"query": "foo}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400, response.text
    assert 'GraphQL request is invalid JSON:\n{"query": "foo}' in response.text


def test_graphql_post(test_client: TestClient):
    # base case
    response = test_client.post(
        "/graphql",
        params={"query": "{__typename}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}

    # missing
    response = test_client.post("/graphql")
    assert response.status_code == 400, response.text

    # variables
    var_str = json.dumps({"runId": "missing"})
    response = test_client.post(
        "/graphql",
        params={"query": RUN_QUERY, "variables": var_str},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"pipelineRunOrError": {"__typename": "RunNotFoundError"}}}

    # malformed vars
    response = test_client.post(
        "/graphql",
        params={
            "query": RUN_QUERY,
            "variables": var_str[:-2],  # malform by trimming
        },
    )
    assert response.status_code == 400, response.text

    # application/json
    response = test_client.post(
        "/graphql",
        json={"query": RUN_QUERY, "variables": {"runId": "missing"}},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"pipelineRunOrError": {"__typename": "RunNotFoundError"}}}

    # application/graphql
    response = test_client.post(
        "/graphql",
        content="{__typename}",
        headers={"Content-type": "application/graphql"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}

    # non existent field
    response = test_client.post(
        "/graphql",
        params={"query": "{__invalid}"},
    )
    assert response.status_code == 400, response.text


def test_graphql_error(test_client: TestClient):
    response = test_client.post(
        "/graphql",
        params={"query": "{test{alwaysException}}"},
    )
    assert response.status_code == 500, response.text
    error = response.json()["errors"][0]
    serdes_err = error["extensions"]["errorInfo"]
    original_err = unpack_value(serdes_err)
    assert isinstance(original_err, SerializableErrorInfo)


def test_graphql_ws_error(test_client: TestClient):
    # wtf pylint

    with test_client.websocket_connect("/graphql", str(GraphQLWS.PROTOCOL)) as ws:
        ws.send_json({"type": GraphQLWS.CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWS.START,
                "id": "1",
                "payload": {"query": "subscription { oops }"},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GraphQLWS.CONNECTION_ACK

        response = ws.receive_json()

        assert response["id"] == "1"
        assert response["type"] == GraphQLWS.ERROR


def test_graphql_ws_success(instance, test_client: TestClient):
    gc.collect()
    # verify no leaks from other tests
    assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 0

    run_id = _add_run(instance)
    # wtf pylint

    with test_client.websocket_connect("/graphql", GraphQLWS.PROTOCOL) as ws:
        ws.send_json({"type": GraphQLWS.CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWS.START,
                "id": "1",
                "payload": {"query": EVENT_LOG_SUBSCRIPTION, "variables": {"runId": run_id}},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GraphQLWS.CONNECTION_ACK

        response = ws.receive_json()
        assert response["id"] == "1"

        assert response["type"] == GraphQLWS.DATA

        gc.collect()
        assert len(objgraph.by_type("async_generator")) == 1

    # after exiting the context manager and closing the connection
    gc.collect()
    assert len(objgraph.by_type("async_generator")) == 0


def test_download_debug_file(instance, test_client: TestClient):
    run_id = _add_run(instance)

    response = test_client.get(f"/download_debug/{run_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/gzip"


def test_download_compute(instance, test_client: TestClient):
    run_id = _add_run(instance)
    logs = instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
    entry = logs[0]
    file_key = entry.dagster_event.logs_captured_data.file_key
    response = test_client.get(f"/logs/{run_id}/compute_logs/{file_key}/out")
    assert response.status_code == 200
    assert "STDOUT RULEZ" in str(response.content)

    response = test_client.get(f"/logs/{run_id}/compute_logs/jonx/stdout")
    assert response.status_code == 404


def test_async(test_client: TestClient):
    response = test_client.post(
        "/graphql",
        params={"query": "{test{one: asyncString, two: asyncString}}"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["data"]["test"]["one"] == "slept", result
    assert result["data"]["test"]["two"] == "slept concurrently", result


def test_download_captured_logs_not_found(test_client: TestClient):
    response = test_client.get("/logs/does-not-exist/stdout")
    assert response.status_code == 404


def test_download_captured_logs_invalid_path(test_client: TestClient):
    with pytest.raises(ValueError, match="Invalid path"):
        test_client.get("/logs/%2e%2e/secret/txt")


def test_no_leak(test_client: TestClient):
    res = test_client.get("/test_request_context")
    assert res.status_code == 200
    data = res.json()
    assert data
    gc.collect()
    assert len(objgraph.by_type(data["name"])) == 0
