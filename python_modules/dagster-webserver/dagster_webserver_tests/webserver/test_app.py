import gc
import inspect

import objgraph
import pytest
from dagster import (
    DagsterInstance,
    __version__ as dagster_version,
    job,
    op,
)
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.events import DagsterEventType
from dagster._core.storage.event_log.base import (
    EventRecordsFilter,
)
from dagster._serdes import unpack_value
from dagster._seven import json
from dagster._utils.error import SerializableErrorInfo
from dagster_graphql.version import __version__ as dagster_graphql_version
from dagster_pipes import PipesContext
from dagster_webserver.graphql import GraphQLWS
from dagster_webserver.version import __version__ as dagster_webserver_version
from dagster_webserver.webserver import ReportAssetMatParam
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
    response = test_client.get(f"/download/{run_id}/{file_key}/stdout")
    assert response.status_code == 200
    assert "STDOUT RULEZ" in str(response.content)

    response = test_client.get(f"/download/{run_id}/jonx/stdout")
    assert response.status_code == 404


def test_runless_events(instance: DagsterInstance, test_client: TestClient):
    # base case
    my_asset_key = "my_asset"
    response = test_client.post(f"/report_asset_materialization/{my_asset_key}")
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt

    # empty asset key path
    response = test_client.post("/report_asset_materialization/")
    assert response.status_code == 400

    # multipart key
    long_key = AssetKey(["foo", "bar", "baz"])
    response = test_client.post(
        # url / delimiter for multipart keys
        "/report_asset_materialization/foo/bar/baz",  # long_key.to_user_string()
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(long_key)
    assert evt

    # slash in key (have to use query param)
    slash_key = AssetKey("slash/key")
    response = test_client.post(
        # have to urlencode / that are part of they key
        "/report_asset_materialization/",
        params={"asset_key": '["slash/key"]'},  # slash_key.to_string(),
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(slash_key)
    assert evt

    # multi part with slashes (have to use query param)
    nasty_key = AssetKey(["a/b", "c/d"])
    response = test_client.post(
        # have to urlencode / that are part of they key
        "/report_asset_materialization/",
        json={
            "asset_key": ["a/b", "c/d"],  # same args passed to AssetKey
        },
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(nasty_key)
    assert evt

    meta = {"my_metadata": "value"}
    mat = AssetMaterialization(
        asset_key=my_asset_key,
        partition="2021-09-23",
        description="cutest",
        metadata=meta,
        tags={
            DATA_VERSION_TAG: "new",
            DATA_VERSION_IS_USER_PROVIDED_TAG: "true",
        },
    )

    # kitchen sink json body
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        json={
            "description": mat.description,
            "partition": mat.partition,
            "metadata": meta,  # handled separately to avoid MetadataValue ish
            "data_version": "new",
        },
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt
    assert evt.asset_materialization
    assert evt.asset_materialization == mat

    # kitchen sink query params
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        params={
            "description": mat.description,
            "partition": mat.partition,
            "metadata": json.dumps(meta),
            "data_version": "new",
        },
    )
    assert response.status_code == 200, response.json()
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    assert evt
    assert evt.asset_materialization
    assert evt.asset_materialization == mat

    # bad metadata
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        params={
            "metadata": meta,  # not json encoded
        },  # type: ignore
    )
    assert response.status_code == 400
    assert "Error parsing metadata json" in response.json()["error"]

    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        json={
            "metadata": "im_just_a_string",
        },
    )
    assert response.status_code == 400
    assert (
        'Error constructing AssetMaterialization: Param "metadata" is not'
        in response.json()["error"]
    )


def test_report_asset_materialization_apis_consistent(
    instance: DagsterInstance, test_client: TestClient
):
    # ensure the ext report_asset_materialization and the API endpoint have the same capabilities
    sample_payload = {
        "asset_key": "sample_key",
        "metadata": {"meta": "data"},
        "data_version": "so_new",
        "partition": "2023-09-23",
        "description": "boo",
    }

    # sample has entry for all supported params (banking on usage of enum)
    assert set(sample_payload.keys()) == set(
        {v for k, v in vars(ReportAssetMatParam).items() if not k.startswith("__")}
    )

    response = test_client.post("/report_asset_materialization/", json=sample_payload)
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(sample_payload["asset_key"]))
    assert evt
    mat = evt.asset_materialization
    assert mat

    for k, v in sample_payload.items():
        if k == "asset_key":
            assert mat.asset_key == AssetKey(v)
        elif k == "metadata":
            assert mat.metadata.keys() == v.keys()
        elif k == "data_version":
            tags = mat.tags
            assert tags
            assert tags[DATA_VERSION_TAG] == v
            assert tags[DATA_VERSION_IS_USER_PROVIDED_TAG]
        elif k == "partition":
            assert mat.partition == v
        elif k == "description":
            assert mat.description == v
        else:
            assert (
                False
            ), "need to add validation that sample payload content was written successfully"

    # all ext report_asset_materialization kwargs should be in sample payload
    sig = inspect.signature(PipesContext.report_asset_materialization)
    skip_set = {"self"}
    params = [p for p in sig.parameters if p not in skip_set]

    KNOWN_DIFF = {"partition", "description"}

    assert set(sample_payload.keys()).difference(set(params)) == KNOWN_DIFF


def test_runless_events_idempotency(instance: DagsterInstance, test_client: TestClient):
    my_asset_key = "idempotent_asset_key"
    idempotency_headers = {"Idempotency-Key": "key/dt=2021-09-23"}
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        headers=idempotency_headers,
    )
    assert response.status_code == 200
    response = test_client.post(
        f"/report_asset_materialization/{my_asset_key}",
        headers=idempotency_headers,
    )
    assert response.status_code == 200
    evt = instance.get_latest_materialization_event(AssetKey(my_asset_key))
    evt = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=AssetKey.from_user_string(my_asset_key),
        ),
        limit=2,
    )
    assert len(evt) == 1
