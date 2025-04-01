import os
import uuid
from collections.abc import Generator

import dlt
import pytest
from dlt import Pipeline


@pytest.fixture(name="dlt_pipeline", autouse=True, scope="function")
def dlt_pipeline_fixture() -> Generator[Pipeline, None, None]:
    # `pipeline_name` must match the `id` used in the `temporary_duckdb_file` path, as that is how
    # dlt determines the file name of the destination
    id = uuid.uuid4()
    temporary_duckdb_file = f"{id}.duckdb"

    dlt_pipeline = dlt.pipeline(
        pipeline_name=str(id),
        dataset_name="example",
        destination="duckdb",
    )

    yield dlt_pipeline

    if os.path.exists(temporary_duckdb_file):
        os.remove(temporary_duckdb_file)
