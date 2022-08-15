# pylint: disable=protected-access
from unittest.mock import MagicMock

import pytest
from dagster_snowflake import DbTypeHandler
from dagster_snowflake.db_io_manager import DbClient, DbIOManager, TablePartition, TableSlice
from pendulum import datetime

from dagster import AssetKey, InputContext, OutputContext, asset, build_output_context
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import resolve_dagster_type

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}


class IntHandler(DbTypeHandler[int]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: int):
        self.handle_output_calls.append((context, table_slice, obj))

    def load_input(self, context: InputContext, table_slice: TableSlice) -> int:
        self.handle_input_calls.append((context, table_slice))
        return 7

    @property
    def supported_types(self):
        return [int]


class StringHandler(DbTypeHandler[str]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: str):
        self.handle_output_calls.append((context, table_slice, obj))

    def load_input(self, context: InputContext, table_slice: TableSlice) -> str:
        self.handle_input_calls.append((context, table_slice))
        return "8"

    @property
    def supported_types(self):
        return [str]


def test_asset_out():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_key=asset_key,
        has_asset_partitions=False,
        metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_out_columns():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        has_asset_partitions=False,
        metadata={"columns": ["apple", "banana"]},
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == TableSlice(
        database="database_abc", schema="schema1", table="table1", columns=["apple", "banana"]
    )


def test_asset_out_partitioned():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = MagicMock(
        asset_key=asset_key,
        resource_config=resource_config,
        asset_partition_key="2020-01-02",
        asset_partitions_time_window=TimeWindow(datetime(2020, 1, 2), datetime(2020, 1, 3)),
        metadata={"partition_expr": "abc"},
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_partition_key="2020-01-02",
        asset_partitions_time_window=TimeWindow(datetime(2020, 1, 2), datetime(2020, 1, 3)),
        metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc",
        schema="schema1",
        table="table1",
        partition=TablePartition(
            time_window=TimeWindow(datetime(2020, 1, 2), datetime(2020, 1, 3)), partition_expr="abc"
        ),
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_different_output_and_input_types():
    int_handler = IntHandler()
    str_handler = StringHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[int_handler, str_handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    assert len(int_handler.handle_output_calls) == 1
    assert len(str_handler.handle_output_calls) == 0
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert int_handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(str),
        has_asset_partitions=False,
        metadata=None,
    )
    assert manager.load_input(input_context) == "8"

    assert len(str_handler.handle_input_calls) == 1
    assert len(int_handler.handle_input_calls) == 0
    assert str_handler.handle_input_calls[0][1] == table_slice


def test_non_asset_out():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        name="table1", metadata={"schema": "schema1"}, resource_config=resource_config
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        has_asset_key=False,
        has_asset_partitions=False,
        metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_schema_defaults():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "schema1"

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "public"

    resource_config_w_schema = {
        "database": "database_abc",
        "account": "account_abc",
        "user": "user_abc",
        "password": "password_abc",
        "warehouse": "warehouse_abc",
        "schema": "my_schema",
    }

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(
        asset_key=asset_key, resource_config=resource_config_w_schema
    )
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "my_schema"

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(
        asset_key=asset_key, resource_config=resource_config_w_schema
    )
    with pytest.raises(DagsterInvalidDefinitionError):
        table_slice = manager._get_table_slice(output_context, output_context)


def test_output_schema_defaults():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        name="table1", metadata={"schema": "schema1"}, resource_config=resource_config
    )
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "schema1"

    output_context = build_output_context(name="table1", resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "public"

    resource_config_w_schema = {
        "database": "database_abc",
        "account": "account_abc",
        "user": "user_abc",
        "password": "password_abc",
        "warehouse": "warehouse_abc",
        "schema": "my_schema",
    }

    output_context = build_output_context(name="table1", resource_config=resource_config_w_schema)
    table_slice = manager._get_table_slice(output_context, output_context)

    assert table_slice.schema == "my_schema"

    output_context = build_output_context(
        name="table1", metadata={"schema": "schema1"}, resource_config=resource_config_w_schema
    )
    with pytest.raises(DagsterInvalidDefinitionError):
        table_slice = manager._get_table_slice(output_context, output_context)


def test_default_load_type():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = DbIOManager(type_handlers=[handler], db_client=db_client, default_load_type=int)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)

    @asset
    def asset1():
        ...

    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=asset1.op.outs["result"].dagster_type,
        asset_key=asset_key,
        has_asset_partitions=False,
        metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == TableSlice(
        database="database_abc", schema="schema1", table="table1"
    )
