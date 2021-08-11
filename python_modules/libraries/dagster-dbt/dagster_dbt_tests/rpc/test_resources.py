import pytest
import responses
from dagster import ModeDefinition, execute_solid, solid
from dagster_dbt import (
    DbtRpcClient,
    DbtRpcOutput,
    DbtRpcSyncClient,
    dbt_rpc_resource,
    dbt_rpc_sync_resource,
    local_dbt_rpc_resource,
)


def test_url(client):
    assert client.url == "http://0.0.0.0:8580/jsonrpc"


@pytest.mark.parametrize("method", ["status", "poll", "kill", "cli_args"])
def test_default_request(client, method):
    expected = {"jsonrpc": client.jsonrpc_version, "method": method, "params": {}}
    resp = client._default_request(method=method)  # pylint: disable=protected-access
    assert resp["jsonrpc"] == expected["jsonrpc"]
    assert resp["method"] == expected["method"]
    assert resp["params"] == expected["params"]


def test_format_params(client):
    expected = {
        "models": "@model_1 +model_2+ model_3+",
        "select": "snapshot_1 snapshot_2 snapshot_3",
        "exclude": "model_4+",
    }
    data = client._format_params(  # pylint: disable=protected-access
        dict(
            models=["@model_1", "+model_2+", "model_3+", "model_3+"],
            select=["snapshot_1", "snapshot_2", "snapshot_3"],
            exclude=["model_4+"],
            other=None,
        )
    )

    assert set(data["models"].split(" ")) == set(expected["models"].split(" "))
    assert set(data["select"].split(" ")) == set(expected["select"].split(" "))
    assert set(data["exclude"].split(" ")) == set(expected["exclude"].split(" "))
    assert "other" not in data


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

        rpc_output = client.status()
        assert rpc_output.response_dict == expected
        assert rpc_output.result == expected["result"]


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

        rpc_output = client.poll(request_token="f86926fa-6535-4891-8d24-2cfc65d2a347")
        assert rpc_output.response_dict == expected
        assert rpc_output.result == expected["result"]


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


def test_dbt_rpc_sync_resource():
    it = {}

    @solid(required_resource_keys={"dbt_rpc"})
    def a_solid(context):
        assert isinstance(context.resources.dbt_rpc, DbtRpcSyncClient)
        assert context.resources.dbt_rpc.host == "<default host>"
        assert context.resources.dbt_rpc.port == 8580
        it["ran"] = True

    execute_solid(
        a_solid,
        ModeDefinition(resource_defs={"dbt_rpc": dbt_rpc_sync_resource}),
        None,
        None,
        {"resources": {"dbt_rpc": {"config": {"host": "<default host>", "poll_interval": 5}}}},
    )
    assert it["ran"]


@pytest.mark.parametrize(
    "client_class,resource",
    [(DbtRpcClient, dbt_rpc_resource), (DbtRpcSyncClient, dbt_rpc_sync_resource)],
)
def test_dbt_rpc_resource_status(
    dbt_rpc_server, client_class, resource
):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def compile_solid(context):
        assert isinstance(context.resources.dbt_rpc, client_class)
        out = context.resources.dbt_rpc.status()
        return out

    result = execute_solid(
        compile_solid,
        ModeDefinition(resource_defs={"dbt_rpc": resource.configured({"host": "localhost"})}),
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


def test_dbt_rpc_resource_is_not_waiting(dbt_rpc_server):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def cli_solid(context):
        assert isinstance(context.resources.dbt_rpc, DbtRpcClient)
        out = context.resources.dbt_rpc.cli("run")
        return out

    result = execute_solid(
        cli_solid,
        ModeDefinition(
            resource_defs={"dbt_rpc": dbt_rpc_resource.configured({"host": "localhost"})}
        ),
    )

    assert result.success
    result = result.output_value("result")
    assert isinstance(result, DbtRpcOutput)

    response = result.response_dict.get("result", {})
    assert "elapsed" not in response
    assert "request_token" in response


def test_dbt_rpc_sync_resource_is_waiting(dbt_rpc_server):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def cli_solid(context):
        assert isinstance(context.resources.dbt_rpc, DbtRpcSyncClient)
        out = context.resources.dbt_rpc.cli("run")
        return out

    result = execute_solid(
        cli_solid,
        ModeDefinition(
            resource_defs={"dbt_rpc": dbt_rpc_sync_resource.configured({"host": "localhost"})}
        ),
    )

    assert result.success
    result = result.output_value("result")
    assert isinstance(result, DbtRpcOutput)

    response = result.response_dict.get("result", {})
    assert "elapsed" in response
    assert "request_token" not in response


@pytest.mark.parametrize(
    "client_class,resource",
    [(DbtRpcClient, dbt_rpc_resource), (DbtRpcSyncClient, dbt_rpc_sync_resource)],
)
def test_dbt_rpc_resource_cli(
    dbt_rpc_server, client_class, resource
):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def cli_solid(context):
        assert isinstance(context.resources.dbt_rpc, client_class)
        out = context.resources.dbt_rpc.cli("run")
        return out

    result = execute_solid(
        cli_solid,
        ModeDefinition(resource_defs={"dbt_rpc": resource.configured({"host": "localhost"})}),
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


@pytest.mark.parametrize(
    "client_class,resource",
    [(DbtRpcClient, dbt_rpc_resource), (DbtRpcSyncClient, dbt_rpc_sync_resource)],
)
def test_dbt_rpc_resource_run(
    dbt_rpc_server, client_class, resource
):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def cli_solid(context):
        assert isinstance(context.resources.dbt_rpc, client_class)
        out = context.resources.dbt_rpc.run(["sort_by_calories"])
        return out

    result = execute_solid(
        cli_solid,
        ModeDefinition(resource_defs={"dbt_rpc": resource.configured({"host": "localhost"})}),
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


@pytest.mark.parametrize(
    "client_class,resource",
    [(DbtRpcClient, dbt_rpc_resource), (DbtRpcSyncClient, dbt_rpc_sync_resource)],
)
def test_dbt_rpc_resource_generate_docs(
    dbt_rpc_server, client_class, resource
):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def compile_solid(context):
        assert isinstance(context.resources.dbt_rpc, client_class)
        out = context.resources.dbt_rpc.generate_docs(True)
        return out

    result = execute_solid(
        compile_solid,
        ModeDefinition(resource_defs={"dbt_rpc": resource.configured({"host": "localhost"})}),
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


@pytest.mark.parametrize(
    "client_class,resource",
    [(DbtRpcClient, dbt_rpc_resource), (DbtRpcSyncClient, dbt_rpc_sync_resource)],
)
def test_dbt_rpc_resource_run_operation(
    dbt_rpc_server, client_class, resource
):  # pylint: disable=unused-argument
    @solid(required_resource_keys={"dbt_rpc"})
    def compile_solid(context):
        assert isinstance(context.resources.dbt_rpc, client_class)
        out = context.resources.dbt_rpc.run_operation("log_macro", {"msg": "hello world"})
        return out

    result = execute_solid(
        compile_solid,
        ModeDefinition(resource_defs={"dbt_rpc": resource.configured({"host": "localhost"})}),
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)
