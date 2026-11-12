from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import sqlalchemy
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    Definitions,
    MetadataValue,
    Out,
    TableColumn,
    TableSchema,
    TimeWindowPartitionMapping,
    asset,
    build_input_context,
    build_output_context,
    graph,
    materialize,
    op,
)
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partitions.utils import MultiPartitionKey
from dagster._core.storage.db_io_manager import TableSlice
from dagster_postgres.io_manager import PostgresDbClient
from dagster_postgres.utils import create_pg_engine
from dagster_postgres_pandas import (
    PostgresPandasIOManager,
    PostgresPandasTypeHandler,
    postgres_pandas_io_manager,
)

if TYPE_CHECKING:
    from dagster._core.definitions.metadata.metadata_value import IntMetadataValue

SCHEMA = "dagster_pandas_test"

resource_config = {
    "hostname": "localhost",
    "username": "test",
    "password": "test",
    "db_name": "test",
}


def test_handle_output_empty_dataframe_creates_table():
    handler = PostgresPandasTypeHandler()
    df = pd.DataFrame({"a": pd.Series([], dtype="int64"), "b": pd.Series([], dtype="int64")})
    connection = MagicMock()
    output_context = build_output_context(resource_config=resource_config)

    with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
        metadata = handler.handle_output(
            output_context,
            TableSlice(table="my_table", schema="my_schema", database="my_db"),
            df,
            connection,
        )

    mock_to_sql.assert_called_once_with(
        name="my_table",
        schema="my_schema",
        con=connection,
        if_exists="append",
        index=False,
    )
    assert metadata["dagster/row_count"] == 0


def test_handle_output_dataframe_without_columns():
    handler = PostgresPandasTypeHandler()
    connection = MagicMock()
    output_context = build_output_context(resource_config=resource_config)

    with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
        metadata = handler.handle_output(
            output_context,
            TableSlice(table="my_table", schema="my_schema", database="my_db"),
            pd.DataFrame(),
            connection,
        )

    mock_to_sql.assert_not_called()
    connection.execute.assert_not_called()
    assert metadata["dagster/row_count"] == 0


def test_handle_output_then_load_input():
    handler = PostgresPandasTypeHandler()
    connection = MagicMock()
    df = pd.DataFrame([{"col1": "a", "col2": 1}])
    table_slice = TableSlice(table="my_table", schema="my_schema", database="my_db")
    output_context = build_output_context(resource_config=resource_config)

    with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
        metadata = handler.handle_output(output_context, table_slice, df, connection)

    mock_to_sql.assert_called_once_with(
        name="my_table",
        schema="my_schema",
        con=connection,
        if_exists="append",
        index=False,
    )
    assert metadata == {
        "dagster/row_count": 1,
        "dagster/storage_kind": "postgres",
        "dataframe_columns": MetadataValue.table_schema(
            TableSchema(
                columns=[
                    TableColumn(name="col1", type="object"),
                    TableColumn(name="col2", type="int64"),
                ]
            )
        ),
    }

    input_context = build_input_context(resource_config=resource_config)
    with patch("dagster_postgres_pandas.postgres_pandas_type_handler.pd.read_sql") as mock_read:
        mock_read.return_value = df
        loaded = handler.load_input(input_context, table_slice, connection)

    mock_read.assert_called_once_with(sql='SELECT * FROM "my_schema"."my_table"', con=connection)
    pd.testing.assert_frame_equal(loaded, df)


def test_load_input_no_partitions_returns_empty_dataframe():
    handler = PostgresPandasTypeHandler()
    connection = MagicMock()
    input_context = MagicMock()
    input_context.asset_partition_keys = []
    table_slice = TableSlice(
        table="my_table",
        schema="my_schema",
        database="my_db",
        partition_dimensions=[MagicMock()],
    )
    with patch("dagster_postgres_pandas.postgres_pandas_type_handler.pd.read_sql") as mock_read:
        loaded = handler.load_input(input_context, table_slice, connection)
    mock_read.assert_not_called()
    assert loaded.empty


def test_io_manager_config():
    io_manager = PostgresPandasIOManager(postgres_url="postgresql://u:p@h:5432/db", schema="s")
    assert io_manager.default_load_type() is pd.DataFrame
    assert isinstance(io_manager.type_handlers()[0], PostgresPandasTypeHandler)
    assert PostgresPandasIOManager._is_dagster_maintained()  # noqa: SLF001
    assert postgres_pandas_io_manager.config_schema is not None


# --- Integration tests: these need the postgres container started by the
# dagster_postgres.test_fixtures pytest plugin (see conftest.py).


@op(out=Out(metadata={"schema": SCHEMA}))
def a_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": SCHEMA}))
def add_one(df: pd.DataFrame) -> pd.DataFrame:
    return df + 1


@graph
def add_one_to_dataframe():
    add_one(a_df())


def _drop_schema(conn_str: str) -> None:
    engine = create_pg_engine(conn_str)
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
    finally:
        engine.dispose()


@pytest.fixture
def io_managers(postgres_conn_str):
    _drop_schema(postgres_conn_str)
    return [
        PostgresPandasIOManager(postgres_url=postgres_conn_str),
        postgres_pandas_io_manager.configured({"postgres_url": postgres_conn_str}),
    ]


def _read_table(conn_str: str, table: str) -> pd.DataFrame:
    engine = create_pg_engine(conn_str)
    try:
        with engine.connect() as conn:
            return pd.read_sql(f'SELECT * FROM "{SCHEMA}"."{table}"', con=conn)
    finally:
        engine.dispose()


@pytest.mark.integration
def test_postgres_io_manager_with_ops(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        job = add_one_to_dataframe.to_job(resource_defs={"io_manager": io_manager})

        # run the job twice to ensure that tables get properly deleted
        for _ in range(2):
            res = job.execute_in_process()
            assert res.success

            out_df = _read_table(postgres_conn_str, "a_df")
            assert out_df["a"].tolist() == [1, 2, 3]

            out_df = _read_table(postgres_conn_str, "add_one")
            assert out_df["a"].tolist() == [2, 3, 4]


@asset(key_prefix=[SCHEMA])
def b_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@asset(key_prefix=[SCHEMA])
def b_plus_one(b_df: pd.DataFrame) -> pd.DataFrame:
    return b_df + 1


@pytest.mark.integration
def test_postgres_io_manager_with_assets(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([b_df, b_plus_one], resources=resource_defs)
            assert res.success

            out_df = _read_table(postgres_conn_str, "b_df")
            assert out_df["a"].tolist() == [1, 2, 3]

            out_df = _read_table(postgres_conn_str, "b_plus_one")
            assert out_df["a"].tolist() == [2, 3, 4]

        materialization = next(
            event
            for event in res.all_events
            if event.event_type_value == "ASSET_MATERIALIZATION"
            and event.asset_key == AssetKey([SCHEMA, "b_df"])
        )
        metadata = materialization.materialization.metadata
        assert cast("IntMetadataValue", metadata["dagster/row_count"]).value == 3
        assert metadata["dagster/storage_kind"] == MetadataValue.text("postgres")
        assert metadata["dagster/table_name"] == MetadataValue.text(f"{SCHEMA}.b_df")


@asset(key_prefix=[SCHEMA])
def empty_df() -> pd.DataFrame:
    return pd.DataFrame({"a": pd.Series([], dtype="int64"), "b": pd.Series([], dtype="int64")})


@asset(key_prefix=[SCHEMA])
def empty_df_downstream(empty_df: pd.DataFrame) -> pd.DataFrame:
    assert empty_df.empty
    assert list(empty_df.columns) == ["a", "b"]
    return empty_df


@pytest.mark.integration
def test_empty_output_round_trip(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        res = materialize([empty_df, empty_df_downstream], resources={"io_manager": io_manager})
        assert res.success
        assert list(_read_table(postgres_conn_str, "empty_df_downstream").columns) == ["a", "b"]


@asset(key_prefix=[SCHEMA], ins={"b_df": AssetIn("b_df", metadata={"columns": ["a"]})})
def b_df_only_a(b_df: pd.DataFrame) -> pd.DataFrame:
    assert list(b_df.columns) == ["a"]
    return b_df


@pytest.mark.integration
def test_load_input_with_columns(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        res = materialize([b_df, b_df_only_a], resources={"io_manager": io_manager})
        assert res.success
        assert list(_read_table(postgres_conn_str, "b_df_only_a").columns) == ["a"]


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    key_prefix=[SCHEMA],
    metadata={"partition_expr": "time"},
    config_schema={"value": str},
)
def daily_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    partition = pd.Timestamp(context.partition_key)
    value = context.op_execution_context.op_config["value"]

    return pd.DataFrame(
        {
            "time": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


@pytest.mark.integration
def test_time_window_partitioned_asset(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        resource_defs = {"io_manager": io_manager}

        result = materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__daily_partitioned": {"config": {"value": "1"}}}},
        )
        materialization = next(
            event
            for event in result.all_events
            if event.event_type_value == "ASSET_MATERIALIZATION"
        )
        meta = materialization.materialization.metadata["dagster/partition_row_count"]
        assert cast("IntMetadataValue", meta).value == 3

        out_df = _read_table(postgres_conn_str, "daily_partitioned")
        assert out_df["a"].tolist() == ["1", "1", "1"]

        materialize(
            [daily_partitioned],
            partition_key="2022-01-02",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__daily_partitioned": {"config": {"value": "2"}}}},
        )

        out_df = _read_table(postgres_conn_str, "daily_partitioned")
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        # re-materializing a partition replaces only that partition's rows
        materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__daily_partitioned": {"config": {"value": "3"}}}},
        )

        out_df = _read_table(postgres_conn_str, "daily_partitioned")
        assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@asset(
    partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
    key_prefix=[SCHEMA],
    metadata={"partition_expr": "color"},
    config_schema={"value": str},
)
def static_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key
    value = context.op_execution_context.op_config["value"]
    return pd.DataFrame(
        {
            "color": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


@pytest.mark.integration
def test_static_partitioned_asset(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        resource_defs = {"io_manager": io_manager}

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__static_partitioned": {"config": {"value": "1"}}}},
        )

        out_df = _read_table(postgres_conn_str, "static_partitioned")
        assert out_df["a"].tolist() == ["1", "1", "1"]

        materialize(
            [static_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__static_partitioned": {"config": {"value": "2"}}}},
        )

        out_df = _read_table(postgres_conn_str, "static_partitioned")
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__static_partitioned": {"config": {"value": "3"}}}},
        )

        out_df = _read_table(postgres_conn_str, "static_partitioned")
        assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "time": DailyPartitionsDefinition(start_date="2022-01-01"),
            "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
        }
    ),
    key_prefix=[SCHEMA],
    metadata={"partition_expr": {"time": "CAST(time AS TIMESTAMP)", "color": "color"}},
    config_schema={"value": str},
)
def multi_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key.keys_by_dimension
    value = context.op_execution_context.op_config["value"]
    return pd.DataFrame(
        {
            "color": [partition["color"], partition["color"], partition["color"]],
            "time": [partition["time"], partition["time"], partition["time"]],
            "a": [value, value, value],
        }
    )


@pytest.mark.integration
def test_multi_partitioned_asset(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        resource_defs = {"io_manager": io_manager}

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__multi_partitioned": {"config": {"value": "1"}}}},
        )

        out_df = _read_table(postgres_conn_str, "multi_partitioned")
        assert out_df["a"].tolist() == ["1", "1", "1"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__multi_partitioned": {"config": {"value": "2"}}}},
        )

        out_df = _read_table(postgres_conn_str, "multi_partitioned")
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__multi_partitioned": {"config": {"value": "3"}}}},
        )

        out_df = _read_table(postgres_conn_str, "multi_partitioned")
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {f"{SCHEMA}__multi_partitioned": {"config": {"value": "4"}}}},
        )

        out_df = _read_table(postgres_conn_str, "multi_partitioned")
        assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    key_prefix=[SCHEMA],
    ins={
        "self_dependent_asset": AssetIn(
            key=AssetKey([SCHEMA, "self_dependent_asset"]),
            partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        ),
    },
    metadata={"partition_expr": "time"},
    config_schema={"value": str, "last_partition_key": str},
)
def self_dependent_asset(
    context: AssetExecutionContext, self_dependent_asset: pd.DataFrame
) -> pd.DataFrame:
    partition = pd.Timestamp(context.partition_key)
    config = context.op_execution_context.op_config

    if not self_dependent_asset.empty:
        assert len(self_dependent_asset.index) == 3
        assert (
            pd.to_datetime(self_dependent_asset["time"]).dt.strftime("%Y-%m-%d").tolist()
            == [config["last_partition_key"]] * 3
        )
    else:
        assert config["last_partition_key"] == "NA"

    return pd.DataFrame(
        {
            "time": [partition, partition, partition],
            "a": [config["value"]] * 3,
        }
    )


@pytest.mark.integration
def test_self_dependent_asset(postgres_conn_str, io_managers):
    for io_manager in io_managers:
        _drop_schema(postgres_conn_str)
        resource_defs = {"io_manager": io_manager}

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-01",
            resources=resource_defs,
            run_config={
                "ops": {
                    f"{SCHEMA}__self_dependent_asset": {
                        "config": {"value": "1", "last_partition_key": "NA"}
                    }
                }
            },
        )

        out_df = _read_table(postgres_conn_str, "self_dependent_asset")
        assert out_df["a"].tolist() == ["1", "1", "1"]

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-02",
            resources=resource_defs,
            run_config={
                "ops": {
                    f"{SCHEMA}__self_dependent_asset": {
                        "config": {"value": "2", "last_partition_key": "2023-01-01"}
                    }
                }
            },
        )

        out_df = _read_table(postgres_conn_str, "self_dependent_asset")
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]


@pytest.mark.integration
def test_definitions_with_io_manager(postgres_conn_str):
    defs = Definitions(
        assets=[b_df, b_plus_one],
        resources={"io_manager": PostgresPandasIOManager(postgres_url=postgres_conn_str)},
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey([SCHEMA, "b_df"]),
        AssetKey([SCHEMA, "b_plus_one"]),
    }
    assert (
        PostgresDbClient.get_select_statement(TableSlice(table="b_df", schema=SCHEMA, database=""))
        == f'SELECT * FROM "{SCHEMA}"."b_df"'
    )
