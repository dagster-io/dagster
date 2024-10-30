from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import duckdb
import pandas as pd
from airflow.models.operator import BaseOperator


# start_load
# from tutorial_example/airflow_dags/csv_operators.py
@dataclass
class LoadCsvToDuckDbArgs:
    table_name: str
    csv_path: Path
    duckdb_path: Path
    names: List[str]
    duckdb_schema: str
    duckdb_database_name: str


class LoadCSVToDuckDB(BaseOperator):
    def __init__(
        self,
        loader_args: LoadCsvToDuckDbArgs,
        *args,
        **kwargs,
    ):
        self.loader_args = loader_args
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        args = self.loader_args
        # Ensure that path exists
        if not args.csv_path.exists():
            raise ValueError(f"CSV file not found at {args.csv_path}")
        if not args.duckdb_path.exists():
            raise ValueError(f"DuckDB database not found at {args.duckdb_path}")
        # Duckdb database stored in airflow home
        df = pd.read_csv(  # noqa: F841 # used by duckdb
            args.csv_path,
            names=args.names,
        )

        # Connect to DuckDB and create a new table
        con = duckdb.connect(str(args.duckdb_path))
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {args.duckdb_schema}").fetchall()
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {args.duckdb_database_name}.{args.duckdb_schema}.{args.table_name} AS SELECT * FROM df"
        ).fetchall()
        con.close()


# end_load


# start_shared_function
def load_csv_to_duckdb(args: LoadCsvToDuckDbArgs) -> None:
    # Ensure that path exists
    if not args.csv_path.exists():
        raise ValueError(f"CSV file not found at {args.csv_path}")
    if not args.duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {args.duckdb_path}")
    # Duckdb database stored in airflow home
    df = pd.read_csv(  # noqa: F841 # used by duckdb
        args.csv_path,
        names=args.names,
    )

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(args.duckdb_path))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {args.duckdb_schema}").fetchall()
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {args.duckdb_database_name}.{args.duckdb_schema}.{args.table_name} AS SELECT * FROM df"
    ).fetchall()
    con.close()


# end_shared_function


@dataclass
class ExportDuckDbToCsvArgs:
    table_name: str
    csv_path: Path
    duckdb_path: Path
    duckdb_database_name: str
    duckdb_schema: Optional[str] = None


def export_duckdb_to_csv(args: ExportDuckDbToCsvArgs) -> None:
    duckdb_path, table_name = args.duckdb_path, args.table_name
    if not duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {duckdb_path}")

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(duckdb_path))
    qualified_table = (
        f"{args.duckdb_schema}.{args.table_name}" if args.duckdb_schema else table_name
    )
    df = con.execute(f"SELECT * FROM {args.duckdb_database_name}.{qualified_table}").df()
    con.close()

    # Write the dataframe to a CSV file
    df.to_csv(args.csv_path, index=False)


class ExportDuckDBToCSV(BaseOperator):
    def __init__(
        self,
        table_name: str,
        csv_path: Path,
        duckdb_path: Path,
        duckdb_database_name: str,
        *args,
        duckdb_schema: Optional[str] = None,
        **kwargs,
    ):
        self._table_name = table_name
        self._csv_path = csv_path
        self._duckdb_path = duckdb_path
        self._duckdb_schema = duckdb_schema
        self._duckdb_database_name = duckdb_database_name
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        export_duckdb_to_csv(
            ExportDuckDbToCsvArgs(
                table_name=self._table_name,
                csv_path=self._csv_path,
                duckdb_path=self._duckdb_path,
                duckdb_database_name=self._duckdb_database_name,
            )
        )
