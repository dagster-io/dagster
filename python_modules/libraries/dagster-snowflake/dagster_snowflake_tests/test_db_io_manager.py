from unittest.mock import MagicMock

from dagster_snowflake import DbTypeHandler
from dagster_snowflake.db_io_manager import DbClient, DbIOManager, TableSlice

from dagster import AssetKey, InputContext, OutputContext, build_input_context, build_output_context
from dagster.core.types.dagster_type import resolve_dagster_type

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

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: int) -> None:
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

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: str) -> None:
        self.handle_output_calls.append((context, table_slice, obj))

    def load_input(self, context: InputContext, table_slice: TableSlice) -> str:
        self.handle_input_calls.append((context, table_slice))
        return "8"

    @property
    def supported_types(self):
        return [str]


def test_asset_out():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient)
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        asset_key=AssetKey(["schema1", "table1"]), resource_config=resource_config
    )
    manager.handle_output(output_context, 5)
    input_context = build_input_context(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1:] == (
        TableSlice(database="database_abc", schema="schema1", table="table1"),
    )


def test_different_output_and_input_types():
    int_handler = IntHandler()
    str_handler = StringHandler()
    db_client = MagicMock(spec=DbClient)
    manager = DbIOManager(type_handlers=[int_handler, str_handler], db_client=db_client)
    output_context = build_output_context(
        asset_key=AssetKey(["schema1", "table1"]), resource_config=resource_config
    )
    manager.handle_output(output_context, 5)
    assert len(int_handler.handle_output_calls) == 1
    assert len(str_handler.handle_output_calls) == 0
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert int_handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    input_context = build_input_context(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(str),
    )
    assert manager.load_input(input_context) == "8"

    assert len(str_handler.handle_input_calls) == 1
    assert len(int_handler.handle_input_calls) == 0
    assert str_handler.handle_input_calls[0][1:] == (
        TableSlice(database="database_abc", schema="schema1", table="table1"),
    )


def test_non_asset_out():
    handler = IntHandler()
    db_client = MagicMock(spec=DbClient)
    manager = DbIOManager(type_handlers=[handler], db_client=db_client)
    output_context = build_output_context(
        name="table1", metadata={"schema": "schema1"}, resource_config=resource_config
    )
    manager.handle_output(output_context, 5)
    input_context = build_input_context(
        upstream_output=output_context,
        resource_config=resource_config,
        dagster_type=resolve_dagster_type(int),
    )
    assert manager.load_input(input_context) == 7

    assert len(handler.handle_output_calls) == 1
    table_slice = TableSlice(database="database_abc", schema="schema1", table="table1")
    assert handler.handle_output_calls[0][1:] == (table_slice, 5)
    db_client.delete_table_slice.assert_called_once_with(output_context, table_slice)

    assert len(handler.handle_input_calls) == 1
    assert handler.handle_input_calls[0][1:] == (
        TableSlice(database="database_abc", schema="schema1", table="table1"),
    )
