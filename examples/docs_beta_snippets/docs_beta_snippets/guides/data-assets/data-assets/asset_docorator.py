from typing import List

import dagster as dg


def load_data() -> str:
    # Load data from S3, the web, etc.
    ...


def transform_data(data: str) -> List[str]:
    # Transform the data some way
    ...


def store_data(files: List[str]):
    # Store the data somewhere
    ...


@dg.asset(
  owners=["bighead@hooli.com", "team:roof", "team:corpdev"],
)
def my_dataset():
    store_data(transform_data(load_data))


defs = dg.Definitions(assets=[my_dataset])