from pathlib import Path
from typing import Any

RAW_DATA_DIR = Path("path")
TABLE_URI = "blah"


def contents_as_df(path: Path) -> Any:
    pass


def upload_to_db(df):
    pass


# start_asset
from dagster import asset


@asset(key=TABLE_URI)
def write_to_db() -> None:
    for raw_file in RAW_DATA_DIR.iterdir():
        df = contents_as_df(raw_file)
        upload_to_db(df)


# end_asset
