import os
import pickle
import tempfile

import pytest

from dagster import MetadataValue, ModeDefinition, execute_pipeline, graph, op, pipeline, solid
from dagster.core.definitions.version_strategy import VersionStrategy
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.fs_io_manager import fs_io_manager
from dagster.core.test_utils import instance_for_test


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
        result_metadata_entry_a = handled_output_events[0].event_specific_data.metadata_entries[0]
        assert result_metadata_entry_a.label == "path"
        assert result_metadata_entry_a.value == MetadataValue.path(filepath_a)
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.event_list))
        input_metadata_entry_a = loaded_input_events[0].event_specific_data.metadata_entries[0]
        assert input_metadata_entry_a.label == "path"
        assert input_metadata_entry_a.value == MetadataValue.path(filepath_a)
        assert len(loaded_input_events) == 1
        assert "solid_a" == loaded_input_events[0].event_specific_data.upstream_step_key

        filepath_b = os.path.join(tmpdir_path, result.run_id, "solid_b", "result")
        result_metadata_entry_b = handled_output_events[1].event_specific_data.metadata_entries[0]
        assert result_metadata_entry_b.label == "path"
        assert result_metadata_entry_b.value == MetadataValue.path(filepath_b)
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
            os.path.join(instance.storage_directory(), result.run_id, "solid_a", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]


def test_fs_io_manager_memoization():
    recorder = []

    @op
    def my_op():
        recorder.append("entered")

    @graph
    def my_graph():
        my_op()

    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, _):
            return "foo"

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            my_job = my_graph.to_job(version_strategy=MyVersionStrategy())

            unmemoized_plan = create_execution_plan(my_job, instance_ref=instance.get_ref())
            assert len(unmemoized_plan.step_keys_to_execute) == 1

            result = my_job.execute_in_process(instance=instance)
            assert result.success
            assert len(recorder) == 1

            execution_plan = create_execution_plan(my_job, instance_ref=instance.get_ref())
            assert len(execution_plan.step_keys_to_execute) == 0

            result = my_job.execute_in_process(instance=instance)
            assert result.success
            assert len(recorder) == 1


# lamdba functions can't be pickled (pickle.PicklingError)
l = lambda x: x * x


def test_fs_io_manager_unpicklable():
    @op
    def unpicklable_local_func_output():
        # locally defined functions can't be pickled (AttributeError)
        def local_func():
            return 1

        return local_func

    @op
    def unpicklable_lambda_output():
        return l

    @op
    def recursion_limit_output():
        # a will exceed the recursion limit of 1000 and can't be pickled (RecursionError)
        a = []
        for _ in range(2000):
            a = [a]
        return a

    @op
    def op_b(_i):
        return 1

    @graph
    def local_func_graph():
        op_b(unpicklable_local_func_output())

    @graph
    def lambda_graph():
        op_b(unpicklable_lambda_output())

    @graph
    def recursion_limit_graph():
        op_b(recursion_limit_output())

    with tempfile.TemporaryDirectory() as tmp_dir:
        with instance_for_test(temp_dir=tmp_dir) as instance:
            io_manager = fs_io_manager.configured({"base_dir": tmp_dir})

            local_func_job = local_func_graph.to_job(resource_defs={"io_manager": io_manager})
            with pytest.raises(
                DagsterInvariantViolationError, match=r"Object .* is not picklable. .*"
            ):
                local_func_job.execute_in_process(instance=instance)

            lambda_job = lambda_graph.to_job(resource_defs={"io_manager": io_manager})
            with pytest.raises(
                DagsterInvariantViolationError, match=r"Object .* is not picklable. .*"
            ):
                lambda_job.execute_in_process(instance=instance)

            recursion_job = recursion_limit_graph.to_job(resource_defs={"io_manager": io_manager})
            with pytest.raises(
                DagsterInvariantViolationError,
                match=r"Object .* exceeds recursion limit and is not picklable. .*",
            ):
                recursion_job.execute_in_process(instance=instance)
