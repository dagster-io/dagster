import os
import tempfile

import pandas
from dagster import execute_solid
from hacker_news.pipelines.download_pipeline import MODE_TEST
from hacker_news.solids.download_items import download_items
from hacker_news.utils.snapshot import SNAPSHOT_START_ID


def test_download_items():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "items-20200101000000_20200101010000.pq")

        execute_solid(
            download_items,
            mode_def=MODE_TEST,
            input_values={"id_range": (SNAPSHOT_START_ID, SNAPSHOT_START_ID + 2)},
            run_config={
                "resources": {
                    "partition_start": {"config": "2020-01-01 00:00:00"},
                    "partition_end": {"config": "2020-01-01 01:00:00"},
                    "parquet_io_manager": {"config": {"base_path": temp_dir}},
                }
            },
        )
        table = pandas.read_parquet(output_path)
        assert table.shape[0] == 2
