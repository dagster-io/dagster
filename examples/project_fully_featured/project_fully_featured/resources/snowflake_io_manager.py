from contextlib import contextmanager
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from dagster import (
    ConfigurableIOManager,
    InputContext,
    MetadataValue,
    OutputContext,
    TableColumn,
    TableSchema,
)
from pandas import (
    DataFrame as PandasDataFrame,
    read_sql,
)
from pyspark.sql import DataFrame as SparkDataFrame
from snowflake.connector.pandas_tools import pd_writer
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine

SNOWFLAKE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@contextmanager
def connect_snowflake(config, schema="public"):
    url = URL(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        warehouse=config["warehouse"],
        schema=schema,
        timezone="UTC",
    )

    conn = None
    try:
        conn = create_engine(url).connect()
        yield conn
    finally:
        if conn:
            conn.close()


class SnowflakeIOManager(ConfigurableIOManager):
    """This IOManager can handle outputs that are either Spark or Pandas DataFrames. In either case,
    the data will be written to a Snowflake table specified by metadata on the relevant Out.
    """

    account: str
    user: str
    password: str
    database: str
    warehouse: str

    @property
    def _config(self):
        return self.dict()

    def handle_output(self, context: OutputContext, obj: Union[PandasDataFrame, SparkDataFrame]):
        schema, table = context.asset_key.path[-2], context.asset_key.path[-1]

        time_window = context.asset_partitions_time_window if context.has_asset_partitions else None
        with connect_snowflake(config=self._config, schema=schema) as con:
            con.execute(self._get_cleanup_statement(table, schema, time_window))

        if isinstance(obj, SparkDataFrame):
            metadata = self._handle_spark_output(obj, schema, table)
        elif isinstance(obj, PandasDataFrame):
            metadata = self._handle_pandas_output(obj, schema, table)
        elif obj is None:  # dbt
            config = dict(self._config)
            config["schema"] = schema
            with connect_snowflake(config=config) as con:
                df = read_sql(f"SELECT * FROM {context.name} LIMIT 5", con=con)
                num_rows = con.execute(f"SELECT COUNT(*) FROM {context.name}").fetchone()

            metadata = {
                "data_sample": MetadataValue.md(df.to_markdown()),
                "rows": num_rows,
            }
        else:
            raise Exception(
                "SnowflakeIOManager only supports pandas DataFrames and spark DataFrames"
            )

        context.add_output_metadata(
            dict(
                query=self._get_select_statement(
                    table,
                    schema,
                    None,
                    time_window,
                ),
                **metadata,
            )
        )

    def _handle_pandas_output(
        self, obj: PandasDataFrame, schema: str, table: str
    ) -> Mapping[str, Any]:
        from snowflake import connector

        connector.paramstyle = "pyformat"
        with connect_snowflake(config=self._config, schema=schema) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table,
                con=con,
                if_exists="append",
                index=False,
                method=pd_writer,
            )

        return {
            "rows": obj.shape[0],
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=name, type=str(dtype))  # type: ignore  # (bad stubs)
                        for name, dtype in obj.dtypes.items()
                    ]
                )
            ),
        }

    def _handle_spark_output(
        self, df: SparkDataFrame, schema: str, table: str
    ) -> Mapping[str, Any]:
        options = {
            "sfURL": f"{self._config['account']}.snowflakecomputing.com",
            "sfUser": self._config["user"],
            "sfPassword": self._config["password"],
            "sfDatabase": self._config["database"],
            "sfSchema": schema,
            "sfWarehouse": self._config["warehouse"],
            "dbtable": table,
        }

        df.write.format("net.snowflake.spark.snowflake").options(**options).mode("append").save()

        return {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=field.name, type=field.dataType.typeName())
                        for field in df.schema.fields
                    ]
                )
            )
        }

    def _get_cleanup_statement(
        self, table: str, schema: str, time_window: Optional[Tuple[datetime, datetime]]
    ) -> str:
        """Returns a SQL statement that deletes data in the given table to make way for the output data
        being written.
        """
        if time_window:
            return f"DELETE FROM {schema}.{table} {self._time_window_where_clause(time_window)}"
        else:
            return f"DELETE FROM {schema}.{table}"

    def load_input(self, context: InputContext) -> PandasDataFrame:
        asset_key = context.asset_key
        schema, table = asset_key.path[-2], asset_key.path[-1]
        with connect_snowflake(config=self._config) as con:
            result = read_sql(
                sql=self._get_select_statement(
                    table,
                    schema,
                    (context.metadata or {}).get("columns"),
                    context.asset_partitions_time_window if context.has_asset_partitions else None,
                ),
                con=con,
            )
            result.columns = map(str.lower, result.columns)  # type: ignore  # (bad stubs)
            return result

    def _get_select_statement(
        self,
        table: str,
        schema: str,
        columns: Optional[Sequence[str]],
        time_window: Optional[Tuple[datetime, datetime]],
    ):
        col_str = ", ".join(columns) if columns else "*"
        if time_window:
            return (
                f"""SELECT {col_str} FROM {self._config["database"]}.{schema}.{table}\n"""
                + self._time_window_where_clause(time_window)
            )
        else:
            return f"""SELECT {col_str} FROM {schema}.{table}"""

    def _time_window_where_clause(self, time_window: Tuple[datetime, datetime]) -> str:
        start_dt, end_dt = time_window
        return f"""WHERE TO_TIMESTAMP(time::INT) BETWEEN '{start_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)}' AND '{end_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)}'"""
