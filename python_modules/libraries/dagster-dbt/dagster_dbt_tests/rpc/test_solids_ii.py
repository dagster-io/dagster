import responses
from dagster import ModeDefinition, execute_solid
from dagster_dbt import (
    DbtRpcOutput,
    dbt_rpc_resource,
    dbt_rpc_run,
    dbt_rpc_run_and_wait,
    dbt_rpc_run_operation,
    dbt_rpc_run_operation_and_wait,
    dbt_rpc_snapshot,
    dbt_rpc_snapshot_and_wait,
    dbt_rpc_snapshot_freshness,
    dbt_rpc_snapshot_freshness_and_wait,
    dbt_rpc_test,
    dbt_rpc_test_and_wait,
)


def test_dbt_rpc_snapshot(rsps):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    result = execute_solid(
        dbt_rpc_snapshot,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
        },
    )

    assert result.success
    assert result.output_value("request_token") == "1234-xo-xo"


def test_dbt_rpc_run(rsps):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    result = execute_solid(
        dbt_rpc_run,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
        },
    )

    assert result.success
    assert result.output_value("request_token") == "1234-xo-xo"


def test_dbt_rpc_test(rsps):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    result = execute_solid(
        dbt_rpc_test,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
        },
    )

    assert result.success
    assert result.output_value("request_token") == "1234-xo-xo"


def test_dbt_rpc_run_operation(rsps):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    result = execute_solid(
        dbt_rpc_run_operation,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {"dbt_rpc_run_operation": {"config": {"macro": "my_test_macro"}}},
        },
    )

    assert result.success
    assert result.output_value("request_token") == "1234-xo-xo"


def test_dbt_rpc_snapshot_freshness(rsps):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    result = execute_solid(
        dbt_rpc_snapshot_freshness,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={"resources": {"dbt_rpc": {"config": {"host": host, "port": port}}}},
    )

    assert result.success
    assert result.output_value("request_token") == "1234-xo-xo"


def test_dbt_rpc_run_and_wait(rsps, non_terminal_poll_result, terminal_poll_result):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=non_terminal_poll_result,
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=terminal_poll_result,
    )

    result = execute_solid(
        dbt_rpc_run_and_wait,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {"dbt_rpc_run_and_wait": {"config": {"interval": 1}}},
        },
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


def test_dbt_rpc_snapshot_and_wait(rsps, non_terminal_poll_result, terminal_poll_result):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=non_terminal_poll_result,
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=terminal_poll_result,
    )

    result = execute_solid(
        dbt_rpc_snapshot_and_wait,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {"dbt_rpc_snapshot_and_wait": {"config": {"interval": 1}}},
        },
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


def test_dbt_rpc_snapshot_freshness_and_wait(rsps, non_terminal_poll_result, terminal_poll_result):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=non_terminal_poll_result,
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=terminal_poll_result,
    )

    result = execute_solid(
        dbt_rpc_snapshot_freshness_and_wait,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {"dbt_rpc_snapshot_freshness_and_wait": {"config": {"interval": 1}}},
        },
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


def test_dbt_rpc_run_operation_and_wait(rsps, non_terminal_poll_result, terminal_poll_result):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=non_terminal_poll_result,
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=terminal_poll_result,
    )

    result = execute_solid(
        dbt_rpc_run_operation_and_wait,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {
                "dbt_rpc_run_operation_and_wait": {"config": {"macro": "test_macro", "interval": 1}}
            },
        },
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)


def test_dbt_rpc_test_and_wait(rsps, non_terminal_poll_result, terminal_poll_result):
    host = "0.0.0.0"
    port = 8580

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json={"result": {"request_token": "1234-xo-xo"}},
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=non_terminal_poll_result,
    )

    rsps.add(
        method=responses.POST,
        url=f"http://{host}:{port}/jsonrpc",
        status=201,
        json=terminal_poll_result,
    )

    result = execute_solid(
        dbt_rpc_test_and_wait,
        mode_def=ModeDefinition(name="unittest", resource_defs={"dbt_rpc": dbt_rpc_resource}),
        input_values={"start_after": None},
        run_config={
            "resources": {"dbt_rpc": {"config": {"host": host, "port": port}}},
            "solids": {"dbt_rpc_test_and_wait": {"config": {"interval": 1}}},
        },
    )

    assert result.success
    assert isinstance(result.output_value("result"), DbtRpcOutput)
