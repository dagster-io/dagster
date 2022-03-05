import gc

import objgraph
from dagit.graphql import GraphQLWS
from dagit.version import __version__ as dagit_version
from dagit.webserver import ROOT_ADDRESS_STATIC_RESOURCES
from dagster_graphql.version import __version__ as dagster_graphql_version
from starlette.testclient import TestClient

from dagster import __version__ as dagster_version
from dagster import job, op
from dagster.seven import json

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
        print("STDOUT RULEZ")  # pylint: disable=print-call

    @job
    def _simple_job():
        my_op()

    result = _simple_job.execute_in_process(instance=instance)
    assert result.success
    return result.run_id


def test_dagit_info(test_client: TestClient):
    response = test_client.get("/dagit_info")
    assert response.status_code == 200
    assert response.json() == {
        "dagit_version": dagit_version,
        "dagster_version": dagster_version,
        "dagster_graphql_version": dagster_graphql_version,
    }


def test_static_resources(test_client: TestClient):
    # make sure we did not fallback to the index html
    # for static resources at /
    for address in ROOT_ADDRESS_STATIC_RESOURCES:
        response = test_client.get(address)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] != "text/html"

    response = test_client.get("/vendor/graphql-playground/middleware.js")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] != "application/js"


# https://graphql.org/learn/serving-over-http/


def test_graphql_get(instance, test_client: TestClient):  # pylint: disable=unused-argument
    # base case
    response = test_client.get(
        "/graphql",
        params={"query": "{__typename}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "DagitQuery"}}

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


def test_graphql_post(test_client: TestClient):
    # base case
    response = test_client.post(
        "/graphql",
        params={"query": "{__typename}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "DagitQuery"}}

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
        data="{__typename}",
        headers={"Content-type": "application/graphql"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "DagitQuery"}}


def test_graphql_ws_error(test_client: TestClient):
    # wtf pylint
    # pylint: disable=not-context-manager
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
    run_id = _add_run(instance)
    # wtf pylint
    # pylint: disable=not-context-manager
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
        assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 1

    # after exiting the context manager and closing the connection
    gc.collect()
    assert len(objgraph.by_type("PipelineRunObservableSubscribe")) == 0


def test_download_debug_file(instance, test_client: TestClient):
    run_id = _add_run(instance)

    response = test_client.get(f"/download_debug/{run_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/gzip"


def test_download_compute(instance, test_client: TestClient):
    run_id = _add_run(instance)

    response = test_client.get(f"/download/{run_id}/my_op/stdout")
    assert response.status_code == 200
    assert "STDOUT RULEZ" in str(response.content)

    response = test_client.get(f"/download/{run_id}/jonx/stdout")
    assert response.status_code == 404
