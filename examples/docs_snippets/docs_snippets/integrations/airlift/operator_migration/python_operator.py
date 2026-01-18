# type: ignore
from pathlib import Path
from typing import Any

RAW_DATA_DIR = Path("path")


def contents_as_df(path: Path) -> Any:
    pass


def upload_to_db(df: Any):
    pass


# start_op
from airflow.operators.python import PythonOperator


def write_to_db() -> None:
    for raw_file in RAW_DATA_DIR.iterdir():
        df = contents_as_df(raw_file)
        upload_to_db(df)


PythonOperator(python_callable=write_to_db, task_id="db_upload", dag=...)

# end_op

# start_shared
from airflow.operators.python import PythonOperator
from shared_module import write_to_db

PythonOperator(python_callable=write_to_db, task_id="db_upload", dag=...)
# end_shared
