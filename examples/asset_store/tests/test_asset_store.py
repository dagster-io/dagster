import os
import pickle

from dagster import DagsterInstance, execute_pipeline, reexecute_pipeline, seven

from ..builtin_custom_path import custom_path_pipeline
from ..builtin_default import model_pipeline


def test_builtin_default():
    with seven.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral()

        run_config = {
            "resources": {"fs_asset_store": {"config": {"base_dir": tmpdir_path}}},
            "storage": {"filesystem": None},
        }

        result = execute_pipeline(
            model_pipeline, run_config=run_config, mode="test", instance=instance
        )

        assert result.success

        filepath_call_api = os.path.join(tmpdir_path, result.run_id, "call_api.compute", "result")
        assert os.path.isfile(filepath_call_api)
        with open(filepath_call_api, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        filepath_parse_df = os.path.join(tmpdir_path, result.run_id, "parse_df.compute", "result")
        assert os.path.isfile(filepath_parse_df)
        with open(filepath_parse_df, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5]

        assert reexecute_pipeline(
            model_pipeline,
            result.run_id,
            run_config=run_config,
            mode="test",
            instance=instance,
            step_selection=["parse_df.compute"],
        ).success


def test_custom_path_asset_store():
    with seven.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.ephemeral()

        run_config = {
            "resources": {"fs_asset_store": {"config": {"base_dir": tmpdir_path}}},
            "storage": {"filesystem": None},
        }

        result = execute_pipeline(
            custom_path_pipeline, run_config=run_config, mode="test", instance=instance
        )

        assert result.success

        filepath_call_api = os.path.join(tmpdir_path, "call_api_output")
        assert os.path.isfile(filepath_call_api)
        with open(filepath_call_api, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        filepath_parse_df = os.path.join(tmpdir_path, "parse_df_output")
        assert os.path.isfile(filepath_parse_df)
        with open(filepath_parse_df, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4, 5]

        assert reexecute_pipeline(
            custom_path_pipeline,
            result.run_id,
            run_config=run_config,
            mode="test",
            instance=instance,
            step_selection=["parse_df.compute*"],
        ).success
