import os
import pickle

from dagster import execute_pipeline, seven

from ..pickled_object import model_pipeline


def test_pickled_object():
    with seven.TemporaryDirectory() as tmpdir_path:

        run_config = {
            "resources": {"default_fs_asset_store": {"config": {"base_dir": tmpdir_path}}},
        }

        result = execute_pipeline(model_pipeline, run_config=run_config, mode="test")

        assert result.success

        filepath_call_api = os.path.join(tmpdir_path, result.run_id, "call_api.compute", "result")
        assert os.path.isfile(filepath_call_api)
        with open(filepath_call_api, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        filepath_parse_df = os.path.join(tmpdir_path, result.run_id, "parse_df.compute", "result")
        assert os.path.isfile(filepath_parse_df)
        with open(filepath_parse_df, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5]
