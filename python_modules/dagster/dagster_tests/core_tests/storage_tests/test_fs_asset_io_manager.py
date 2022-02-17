import os
import pickle
import tempfile

from dagster.core.asset_defs import AssetIn, asset, build_assets_job
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager


def get_assets_job(io_manager_def):
    asset1_namespace = ["one", "two", "three"]

    @asset(namespace=["one", "two", "three"])
    def asset1():
        return [1, 2, 3]

    @asset(namespace=["four", "five"], ins={"asset1": AssetIn(namespace=asset1_namespace)})
    def asset2(asset1):
        return asset1 + [4]

    return build_assets_job(
        name="a", assets=[asset1, asset2], resource_defs={"io_manager": io_manager_def}
    )


def test_fs_asset_io_manager():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_asset_io_manager.configured({"base_dir": tmpdir_path})
        job_def = get_assets_job(io_manager_def)

        result = job_def.execute_in_process()
        assert result.success

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 2

        filepath_a = os.path.join(tmpdir_path, "one", "two", "three", "asset1")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.all_node_events))
        assert len(loaded_input_events) == 1
        assert loaded_input_events[0].event_specific_data.upstream_step_key.endswith("asset1")

        filepath_b = os.path.join(tmpdir_path, "four", "five", "asset2")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4]
