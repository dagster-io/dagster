import os
import pickle
import tempfile

from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster.core.instance import DagsterInstance
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

        handled_output_events = list(filter(lambda evt: evt.is_handled_output, result.event_list))
        assert len(handled_output_events) == 2

        filepath_a = os.path.join(tmpdir_path, result.run_id, "solid_a", "result")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.event_list))
        assert len(loaded_input_events) == 1
        assert "solid_a" == loaded_input_events[0].event_specific_data.upstream_step_key

        filepath_b = os.path.join(tmpdir_path, result.run_id, "solid_b", "result")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == 1


def test_fs_io_manager_base_dir():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral(tempdir=tmpdir_path)
        io_manager = fs_io_manager
        pipeline_def = define_pipeline(io_manager)

        result = execute_pipeline(pipeline_def, instance=instance)
        assert result.success
        assert result.result_for_solid("solid_a").output_value() == [1, 2, 3]

        with open(
            os.path.join(instance.storage_directory(), result.run_id, "solid_a", "result"), "rb"
        ) as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]
