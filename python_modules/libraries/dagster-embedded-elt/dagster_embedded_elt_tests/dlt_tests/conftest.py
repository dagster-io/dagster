import os
from typing import Generator, Tuple

import dlt
import pytest
from dlt import Pipeline
from dlt.extract.source import DltSource

from .constants import EXAMPLE_PIPELINE_DUCKDB
from .dlt_test_sources.duckdb_with_transformer import pipeline


@pytest.fixture(autouse=True, scope="module")
def setup_dlt_pipeline() -> Generator[Tuple[DltSource, Pipeline], None, None]:
    if os.path.exists(EXAMPLE_PIPELINE_DUCKDB):
        os.remove(EXAMPLE_PIPELINE_DUCKDB)

    dlt_source = pipeline()
    dlt_pipeline = dlt.pipeline(
        pipeline_name="example_pipeline",
        dataset_name="example",
        destination="duckdb",
    )

    yield dlt_source, dlt_pipeline

    if os.path.exists(EXAMPLE_PIPELINE_DUCKDB):
        os.remove(EXAMPLE_PIPELINE_DUCKDB)
