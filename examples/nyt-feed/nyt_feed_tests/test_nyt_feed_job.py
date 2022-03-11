import os
import tempfile

import pandas as pd
from nyt_feed.nyt_feed_job import df_to_csv_io_manager, process_nyt_feed

from dagster import build_init_resource_context, build_input_context, build_output_context
from dagster._core.test_utils import instance_for_test


def test_nyt_feed_job():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with instance_for_test(temp_dir=tmp_dir) as instance:
            assert process_nyt_feed.execute_in_process(
                instance=instance,
                run_config={
                    "ops": {
                        "all_csv": {"config": f"{tmp_dir}/all_articles.csv"},
                        "nyc_csv": {"config": f"{tmp_dir}/nyc_articles.csv"},
                    },
                    "resources": {"slack": {"config": {"token": "nonce"}}},
                },
            ).success


def test_df_to_csv_io_manager():
    with tempfile.TemporaryDirectory() as temp_dir:
        my_io_manager = df_to_csv_io_manager(
            build_init_resource_context(config={"base_dir": temp_dir})
        )
        test_df = pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})
        # test handle_output
        output_context = build_output_context(name="abc", step_key="123")
        my_io_manager.handle_output(output_context, test_df)
        output_path = my_io_manager._get_path(output_context)  # pylint:disable=protected-access
        assert os.path.exists(output_path)
        assert test_df.equals(pd.read_csv(output_path))

        # test load_input
        input_context = build_input_context(upstream_output=output_context)
        assert test_df.equals(my_io_manager.load_input(input_context))
