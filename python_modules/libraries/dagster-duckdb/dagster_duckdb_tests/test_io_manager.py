import os

import duckdb
import pytest
from dagster_duckdb.io_manager import DbTypeHandler, build_duckdb_io_manager

from dagster import asset, graph, materialize, op
from dagster._check import CheckError


class IntHandler(DbTypeHandler[int]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context, obj: int, conn: duckdb.DuckDBPyConnection, base_path: str):
        self.handle_output_calls.append((context, obj))

    def load_input(self, context, conn: duckdb.DuckDBPyConnection) -> int:
        self.handle_input_calls.append((context))
        return 7

    def _get_path(self, context, base_path: str):
        return ""

    @property
    def supported_input_types(self):
        return [int]

    @property
    def supported_output_types(self):
        return [int]


class StringHandler(DbTypeHandler[str]):
    def __init__(self):
        self.handle_input_calls = []
        self.handle_output_calls = []

    def handle_output(self, context, obj: str, conn: duckdb.DuckDBPyConnection, base_path: str):
        self.handle_output_calls.append((context, obj))

    def load_input(self, context, conn: duckdb.DuckDBPyConnection) -> str:
        self.handle_input_calls.append((context))
        return "8"

    def _get_path(self, context, base_path: str):
        return ""

    @property
    def supported_input_types(self):
        return []

    @property
    def supported_output_types(self):
        return [str]


@op
def an_int() -> int:
    return 4


@op
def add_one(x: int):
    return x + 1


@graph
def add_one_to_int():
    add_one(an_int())


def test_duckdb_io_manager_with_ops(tmp_path):
    handler = IntHandler()
    duckdb_io_manager = build_duckdb_io_manager([handler])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = add_one_to_int.to_job(resource_defs=resource_defs)

    res = job.execute_in_process()

    assert res.success
    assert len(handler.handle_output_calls) == 2
    assert handler.handle_output_calls[0][1] == 4
    assert len(handler.handle_input_calls) == 1


@asset(key_prefix=["my_schema"])
def int_asset() -> int:
    return 2


@asset(key_prefix=["my_schema"])
def int_asset_plus_one(int_asset: int):
    return int_asset + 1


def test_duckdb_io_manager_with_assets(tmp_path):
    handler = IntHandler()
    duckdb_io_manager = build_duckdb_io_manager([handler])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    res = materialize([int_asset, int_asset_plus_one], resources=resource_defs)
    assert res.success
    assert len(handler.handle_output_calls) == 2
    assert handler.handle_output_calls[0][1] == 2
    assert len(handler.handle_input_calls) == 1


@op
def non_supported_type() -> float:
    return 1.1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([IntHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = not_supported.to_job(resource_defs=resource_defs)

    with pytest.raises(
        CheckError,
        match="DuckDBIOManager does not have a handler that supports outputs of type '<class 'float'>'",
    ):
        job.execute_in_process()


@asset
def string_asset() -> str:
    return "hi"


@asset
def accepts_string(string_asset: str) -> str:
    return string_asset + " world"


def test_not_supported_input_type(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([StringHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    with pytest.raises(
        CheckError,
        match="DuckDBIOManager does not have a handler that supports inputs of type '<class 'str'>'",
    ):
        materialize([string_asset, accepts_string], resources=resource_defs)
