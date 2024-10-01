from unittest.mock import MagicMock

import pytest
from dagster import AssetKey, InputContext, OutputContext, asset, build_output_context
from dagster._check import CheckError
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition, TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._time import create_datetime

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}


def mock_relation_identifier(*args, **kwargs) -> str:
    return "relation_identifier"


class IntHandler(DbTypeHandler[int]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: int, connection):
        self.handle_output_calls.append((context, table_slice, obj))

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> int:
        self.handle_input_calls.append((context, table_slice))
        return 7

    @property
    def supported_types(self):
        return [int]


class StringHandler(DbTypeHandler[str]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: str, connection):
        self.handle_output_calls.append((context, table_slice, obj))

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> str:
        self.handle_input_calls.append((context, table_slice))
        return "8"

    @property
    def supported_types(self):
        return [str]


def build_db_io_manager(type_handlers, db_client, resource_config_override=None):
    conf = resource_config_override if resource_config_override else resource_config

    return DbIOManager(
        type_handlers=type_handlers,
        db_client=db_client,
        database=conf["database"],
        schema=conf.get("schema"),
    )


def test_asset_out():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_key=asset_key,
        has_asset_partitions=False,
        definition_metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc", schema="schema1", table="table1", partition_dimensions=[]
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_out_columns():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        has_asset_partitions=False,
        definition_metadata={"columns": ["apple", "banana"]},
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc", schema="schema1", table="table1", partition_dimensions=[]
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == TableSlice(
        database="database_abc",
        schema="schema1",
        table="table1",
        columns=["apple", "banana"],
        partition_dimensions=[],
    )


def test_asset_out_partitioned():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-02")
    partitions_def.time_window_for_partition_key = MagicMock(
        return_value=TimeWindow(create_datetime(2020, 1, 2), create_datetime(2020, 1, 3))
    )
    output_context = MagicMock(
        asset_key=asset_key,
        resource_config=resource_config,
        asset_partitions_time_window=TimeWindow(
            create_datetime(2020, 1, 2), create_datetime(2020, 1, 3)
        ),
        definition_metadata={"partition_expr": "abc"},
        asset_partitions_def=partitions_def,
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_partitions_time_window=TimeWindow(
            create_datetime(2020, 1, 2), create_datetime(2020, 1, 3)
        ),
        definition_metadata=None,
        asset_partitions_def=partitions_def,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc",
        schema="schema1",
        table="table1",
        partition_dimensions=[
            TablePartitionDimension(
                partitions=TimeWindow(create_datetime(2020, 1, 2), create_datetime(2020, 1, 3)),
                partition_expr="abc",
            )
        ],
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_out_static_partitioned():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])
    output_context = MagicMock(
        asset_key=asset_key,
        resource_config=resource_config,
        asset_partition_keys=["red"],
        definition_metadata={"partition_expr": "abc"},
        asset_partitions_def=partitions_def,
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_partition_keys=["red"],
        definition_metadata=None,
        asset_partitions_def=partitions_def,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc",
        schema="schema1",
        table="table1",
        partition_dimensions=[
            TablePartitionDimension(
                partitions=["red"],
                partition_expr="abc",
            )
        ],
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_out_multiple_static_partitions():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])
    output_context = MagicMock(
        asset_key=asset_key,
        resource_config=resource_config,
        asset_partition_keys=["red", "yellow"],
        definition_metadata={"partition_expr": "abc"},
        asset_partitions_def=partitions_def,
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        asset_partition_keys=["red", "yellow"],
        definition_metadata=None,
        asset_partitions_def=partitions_def,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc",
        schema="schema1",
        table="table1",
        partition_dimensions=[
            TablePartitionDimension(
                partitions=["red", "yellow"],
                partition_expr="abc",
            )
        ],
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1] == table_slice


def test_different_output_and_input_types():
    int_handler = IntHandler()
    str_handler = StringHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[int_handler, str_handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    manager.handle_output(output_context, 5)
    assert len(int_handler.handle_output_calls) == 1
    assert len(str_handler.handle_output_calls) == 0
    table_slice = TableSlice(
        database="database_abc", schema="schema1", table="table1", partition_dimensions=[]
    )
    assert int_handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    input_context = MagicMock(
        asset_key=asset_key,
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(str),
        has_asset_partitions=False,
        definition_metadata=None,
    )
    assert manager.load_input(input_context) == "8"

    assert len(str_handler.handle_input_calls) == 1
    assert len(int_handler.handle_input_calls) == 0
    assert str_handler.handle_input_calls[0][1] == table_slice


def test_non_asset_out():
    handler = IntHandler()
    connect_mock = MagicMock()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        connect=connect_mock,
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        name="table1",
        definition_metadata={"schema": "schema1"},
        resource_config=resource_config,
    )
    manager.handle_output(output_context, 5)
    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
        has_asset_key=False,
        has_asset_partitions=False,
        definition_metadata=None,
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(
        database="database_abc", schema="schema1", table="table1", partition_dimensions=[]
    )
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(
        output_context, table_slice, connect_mock().__enter__()
    )

    assert len(handler.handle_input_calls) == 1

    assert handler.handle_input_calls[0][1] == table_slice


def test_asset_schema_defaults():
    handler = IntHandler()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        get_relation_identifier=mock_relation_identifier,
    )
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "schema1"

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "public"

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(
        asset_key=asset_key,
        definition_metadata={"schema": "schema2"},
        resource_config=resource_config,
    )
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "schema2"

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(
        asset_key=asset_key,
        definition_metadata={"schema": "schema1"},
        resource_config=resource_config,
    )
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "schema1"

    resource_config_w_schema = {
        "database": "database_abc",
        "account": "account_abc",
        "user": "user_abc",
        "password": "password_abc",
        "warehouse": "warehouse_abc",
        "schema": "my_schema",
    }

    manager_w_schema = build_db_io_manager(
        type_handlers=[handler],
        db_client=db_client,
        resource_config_override=resource_config_w_schema,
    )

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(
        asset_key=asset_key, resource_config=resource_config_w_schema
    )
    table_slice = manager_w_schema._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "my_schema"

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(
        asset_key=asset_key, resource_config=resource_config_w_schema
    )
    table_slice = manager_w_schema._get_table_slice(output_context, output_context)  # noqa: SLF001
    assert table_slice.schema == "my_schema"

    asset_key = AssetKey(["table1"])
    output_context = build_output_context(
        asset_key=asset_key,
        definition_metadata={"schema": "schema1"},
        resource_config=resource_config_w_schema,
    )

    table_slice = manager_w_schema._get_table_slice(output_context, output_context)  # noqa: SLF001
    assert table_slice.schema == "schema1"


def test_output_schema_defaults():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        name="table1",
        definition_metadata={"schema": "schema1"},
        resource_config=resource_config,
    )
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "schema1"

    output_context = build_output_context(name="table1", resource_config=resource_config)
    table_slice = manager._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "public"

    resource_config_w_schema = {
        "database": "database_abc",
        "account": "account_abc",
        "user": "user_abc",
        "password": "password_abc",
        "warehouse": "warehouse_abc",
        "schema": "my_schema",
    }

    manager_w_schema = build_db_io_manager(
        type_handlers=[handler],
        db_client=db_client,
        resource_config_override=resource_config_w_schema,
    )

    output_context = build_output_context(name="table1", resource_config=resource_config_w_schema)
    table_slice = manager_w_schema._get_table_slice(output_context, output_context)  # noqa: SLF001

    assert table_slice.schema == "my_schema"

    output_context = build_output_context(
        name="table1",
        definition_metadata={"schema": "schema1"},
        resource_config=resource_config_w_schema,
    )
    table_slice = manager_w_schema._get_table_slice(output_context, output_context)  # noqa: SLF001
    assert table_slice.schema == "schema1"


def test_handle_none_output():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)

    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(
        asset_key=asset_key,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(type(None)),
        name="result",
    )

    with pytest.raises(DagsterInvariantViolationError):
        manager.handle_output(output_context, None)


def test_non_supported_type():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))
    manager = build_db_io_manager(type_handlers=[handler], db_client=db_client)
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(
        asset_key=asset_key,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(type(None)),
    )
    with pytest.raises(
        CheckError, match="DbIOManager does not have a handler for type '<class 'str'>'"
    ):
        manager.handle_output(output_context, "a_string")


def test_default_load_type():
    handler = IntHandler()
    db_client = MagicMock(
        spec=DbClient,
        get_select_statement=MagicMock(return_value=""),
        get_relation_identifier=mock_relation_identifier,
    )
    manager = DbIOManager(
        type_handlers=[handler],
        database=resource_config["database"],
        db_client=db_client,
        default_load_type=int,
    )
    asset_key = AssetKey(["schema1", "table1"])
    output_context = build_output_context(asset_key=asset_key, resource_config=resource_config)

    @asset
    def asset1(): ...

    input_context = MagicMock(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=asset1.op.outs["result"].dagster_type,
        asset_key=asset_key,
        has_asset_partitions=False,
        definition_metadata=None,
    )

    manager.handle_output(output_context, 1)
    assert len(handler.handle_output_calls) == 1

    assert manager.load_input(input_context) == 7

    assert len(handler.handle_input_calls) == 1

    assert handler.handle_input_calls[0][1] == TableSlice(
        database="database_abc", schema="schema1", table="table1", partition_dimensions=[]
    )


def test_default_load_type_determination():
    int_handler = IntHandler()
    string_handler = StringHandler()
    db_client = MagicMock(spec=DbClient, get_select_statement=MagicMock(return_value=""))

    manager = DbIOManager(
        type_handlers=[int_handler], database=resource_config["database"], db_client=db_client
    )
    assert manager._default_load_type == int  # noqa: SLF001

    manager = DbIOManager(
        type_handlers=[int_handler, string_handler],
        database=resource_config["database"],
        db_client=db_client,
    )
    assert manager._default_load_type is None  # noqa: SLF001

    manager = DbIOManager(
        type_handlers=[int_handler, string_handler],
        database=resource_config["database"],
        db_client=db_client,
        default_load_type=int,
    )
    assert manager._default_load_type == int  # noqa: SLF001
