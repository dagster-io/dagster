from typing import List

import dagster as dg


def download_files() -> str:
    # Download files from S3, the web, etc.
    ...


def unzip_files(zipfile: str) -> list[str]:
    # Unzip files to local disk or persistent storage
    ...


def load_data(files: list[str]):
    # Read data previously written and store in a data warehouse
    ...


@dg.asset
def my_dataset():
    zipped_files = download_files()
    files = unzip_files(zipped_files)
    load_data(files)
