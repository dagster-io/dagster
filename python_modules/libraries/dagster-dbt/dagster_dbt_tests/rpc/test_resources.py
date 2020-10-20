import pytest
import responses
from dagster import ModeDefinition, execute_solid, solid
from dagster_dbt import DbtRpcClient, dbt_rpc_resource, local_dbt_rpc_resource


def test_url(client):
    assert client.url == "http://0.0.0.0:8580/jsonrpc"


@pytest.mark.parametrize("method", ["status", "poll", "kill", "cli_args"])
def test_default_request(client, method):
    expected = {"jsonrpc": client.jsonrpc_version, "method": method, "params": {}}
    resp = client._default_request(method=method)  # pylint: disable=protected-access
    assert resp["jsonrpc"] == expected["jsonrpc"]
    assert resp["method"] == expected["method"]
    assert resp["params"] == expected["params"]


def test_selection(client):
    expected = {
        "models": "@model_1 +model_2+ model_3+",
        "select": "snapshot_1 snapshot_2 snapshot_3",
        "exclude": "model_4+",
    }
    data = client._selection(  # pylint: disable=protected-access
        models=["@model_1", "+model_2+", "model_3+", "model_3+"],
        select=["snapshot_1", "snapshot_2", "snapshot_3"],
        exclude=["model_4+"],
    )

    assert set(data["models"].split(" ")) == set(expected["models"].split(" "))
    assert set(data["select"].split(" ")) == set(expected["select"].split(" "))
    assert set(data["exclude"].split(" ")) == set(expected["exclude"].split(" "))


def test_status(client):
    with responses.RequestsMock() as rsps:
        expected = {
            "result": {
                "status": "ready",
                "error": "null",
                "logs": [],
                "timestamp": "2019-10-07T16:30:09.875534Z",
                "pid": 76715,
            },
            "id": "2db9a2fe-9a39-41ef-828c-25e04dd6b07d",
            "jsonrpc": client.jsonrpc_version,
        }
        rsps.add(responses.POST, client.url, json=expected, status=202)

        resp = client.status()
        assert resp.json() == expected


def test_poll(client):
    with responses.RequestsMock() as rsps:
        expected = {
            "result": {
                "results": [],
                "generated_at": "2019-10-11T18:25:22.477203Z",
                "elapsed_time": 0.8381369113922119,
                "logs": [],
                "tags": {"command": "run --models my_model", "branch": "abc123"},
                "status": "success",
            },
            "id": "2db9a2fe-9a39-41ef-828c-25e04dd6b07d",
            "jsonrpc": client.jsonrpc_version,
        }
        rsps.add(responses.POST, client.url, json=expected, status=202)

        resp = client.poll(request_token="f86926fa-6535-4891-8d24-2cfc65d2a347")
        assert resp.json() == expected


def test_dbt_rpc_resource():
    it = {}

    @solid(required_resource_keys={"dbt_rpc"})
    def a_solid(context):
        assert isinstance(context.resources.dbt_rpc, DbtRpcClient)
        assert context.resources.dbt_rpc.host == "<default host>"
        assert context.resources.dbt_rpc.port == 8580
        it["ran"] = True

    execute_solid(
        a_solid,
        ModeDefinition(resource_defs={"dbt_rpc": dbt_rpc_resource}),
        None,
        None,
        {"resources": {"dbt_rpc": {"config": {"host": "<default host>"}}}},
    )
    assert it["ran"]


def test_local_dbt_rpc_resource():
    it = {}

    @solid(required_resource_keys={"dbt_rpc"})
    def a_solid(context):
        assert isinstance(context.resources.dbt_rpc, DbtRpcClient)
        assert context.resources.dbt_rpc.host == "0.0.0.0"
        assert context.resources.dbt_rpc.port == 8580
        it["ran"] = True

    execute_solid(a_solid, ModeDefinition(resource_defs={"dbt_rpc": local_dbt_rpc_resource}))
    assert it["ran"]
