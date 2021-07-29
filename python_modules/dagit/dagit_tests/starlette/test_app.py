import gc

import objgraph
from dagit.starlette import ROOT_ADDRESS_STATIC_RESOURCES, GraphQLWS
from dagster import execute_pipeline, pipeline, op, graph, reconstructable
from starlette.testclient import TestClient

EVENT_LOG_SUBSCRIPTION = """
    subscription PipelineRunLogsSubscription($runId: ID!) {
        pipelineRunLogs(runId: $runId) {
            __typename
        }
    }
"""


def test_dagit_info(empty_app):
    client = TestClient(empty_app)
    response = client.get("/dagit_info")
    assert response.status_code == 200
    assert response.json() == {
        "dagit_version": "dev",
        "dagster_version": "dev",
        "dagster_graphql_version": "dev",
    }


def test_static_resources(empty_app):
    client = TestClient(empty_app)

    # make sure we did not fallback to the index html
    # for static resources at /
    for address in ROOT_ADDRESS_STATIC_RESOURCES:
        response = client.get(address)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] != "text/html"

    response = client.get("/vendor/graphql-playground/middleware.js")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] != "application/js"


def test_graphql_get(empty_app):
    client = TestClient(empty_app)
    response = client.get(
        "/graphql?query={__typename}",
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}


def test_graphql_post(empty_app):
    client = TestClient(empty_app)
    response = client.post(
        "/graphql?query={__typename}",
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}

    response = client.post(
        "/graphql",
        json={"query": "{__typename}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"data": {"__typename": "Query"}}


def test_graphql_ws_error(empty_app):
    # wtf pylint
    # pylint: disable=not-context-manager
    with TestClient(empty_app).websocket_connect("/graphql", str(GraphQLWS.PROTOCOL)) as ws:
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


def test_graphql_ws_success(instance, empty_app):
    @pipeline
    def _test():
        pass

    result = execute_pipeline(_test, instance=instance)
    run_id = result.run_id
    # wtf pylint
    # pylint: disable=not-context-manager
    with TestClient(empty_app).websocket_connect("/graphql", GraphQLWS.PROTOCOL) as ws:
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


def test_download_debug_file(instance, empty_app):
    @pipeline
    def _test():
        pass

    result = execute_pipeline(_test, instance=instance)
    run_id = result.run_id

    response = TestClient(empty_app).get(f"/download_debug/{run_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/gzip"


def _simple_job():
    @op
    def my_op():
        print("STDOUT RULEZ")  # pylint: disable=print-call

    @graph
    def my_graph():
        my_op()

    return my_graph.to_job()


def test_download_compute(instance, empty_app):
    result = execute_pipeline(reconstructable(_simple_job), instance=instance)
    run_id = result.run_id

    response = TestClient(empty_app).get(f"/download/{run_id}/my_op/stdout")
    assert response.status_code == 200
    assert "STDOUT RULEZ" in str(response.content)

    response = TestClient(empty_app).get(f"/download/{run_id}/jonx/stdout")
    assert response.status_code == 404
