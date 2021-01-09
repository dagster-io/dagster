import os
import pickle
import tempfile

from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster.core.definitions.events import AssetStoreOperationType
from dagster.core.storage.fs_io_manager import fs_io_manager


def define_pipeline(io_manager):
    @solid
    def solid_a(_context):
        return [1, 2, 3]

    @solid
    def solid_b(_context, _df):
        return 1

    @pipeline(mode_defs=[ModeDefinition("local", resource_defs={"io_manager": io_manager})])
    def asset_pipeline():
        solid_b(solid_a())

    return asset_pipeline


def test_fs_io_manager():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})
        pipeline_def = define_pipeline(io_manager)

        result = execute_pipeline(pipeline_def)
        assert result.success

        asset_store_operation_events = list(
            filter(lambda evt: evt.is_asset_store_operation, result.event_list)
        )

        assert len(asset_store_operation_events) == 3
        # SET ASSET for step "solid_a" output "result"
        assert (
            asset_store_operation_events[0].event_specific_data.op
            == AssetStoreOperationType.SET_ASSET.value
        )
        filepath_a = os.path.join(tmpdir_path, result.run_id, "solid_a", "result")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        # GET ASSET for step "solid_b" input "_df"
        assert (
            asset_store_operation_events[1].event_specific_data.op
            == AssetStoreOperationType.GET_ASSET.value
        )
        assert "solid_a" == asset_store_operation_events[1].event_specific_data.step_key

        # SET ASSET for step "solid_b" output "result"
        assert (
            asset_store_operation_events[2].event_specific_data.op
            == AssetStoreOperationType.SET_ASSET.value
        )
        filepath_b = os.path.join(tmpdir_path, result.run_id, "solid_b", "result")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == 1
