from airflow.models.operator import BaseOperator

# start_load
# Completed versions of utilities can be found in tutorial_example/shared/complete/load_csv_to_duckdb.py
from tutorial_example.shared.complete.load_csv_to_duckdb import (
    LoadCsvToDuckDbArgs,
    load_csv_to_duckdb,
)


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
        load_csv_to_duckdb(self.loader_args)


# end_load
