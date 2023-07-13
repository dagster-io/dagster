import os
import pickle
import shutil
import tempfile
from datetime import datetime
from typing import Optional, Tuple

import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterInstance,
    DailyPartitionsDefinition,
    In,
    MetadataValue,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Nothing,
    Output,
    PartitionMapping,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    define_asset_job,
    graph,
    job,
    materialize,
    op,
    with_resources,
)
from dagster._core.definitions import AssetIn, asset, build_assets_job, multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.definitions.partition_mapping import UpstreamPartitionsResult
from dagster._core.definitions.version_strategy import VersionStrategy
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.api import create_execution_plan
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path


def define_job(io_manager: IOManagerDefinition):
    @op
    def op_a(_context):
        return [1, 2, 3]

    @op
    def op_b(_context, _df):
        return 1

    @job(resource_defs={"io_manager": io_manager})
    def asset_job():
        op_b(op_a())

    return asset_job


def test_fs_io_manager():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager = fs_io_manager.configured({"base_dir": tmpdir_path})
        job_def = define_job(io_manager)

        result = job_def.execute_in_process()
        assert result.success

        handled_output_events = list(filter(lambda evt: evt.is_handled_output, result.all_events))
        assert len(handled_output_events) == 2

        filepath_a = os.path.join(tmpdir_path, result.run_id, "op_a", "result")
        metadata = handled_output_events[0].event_specific_data.metadata
        assert metadata["path"] == MetadataValue.path(filepath_a)
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.all_events))
        metadata = loaded_input_events[0].event_specific_data.metadata
        assert metadata["path"] == MetadataValue.path(filepath_a)
        assert len(loaded_input_events) == 1
        assert loaded_input_events[0].event_specific_data.upstream_step_key == "op_a"

        filepath_b = os.path.join(tmpdir_path, result.run_id, "op_b", "result")
        metadata = handled_output_events[1].event_specific_data.metadata
        assert metadata["path"] == MetadataValue.path(filepath_b)
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == 1


def test_fs_io_manager_base_dir():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral(tempdir=tmpdir_path)
        io_manager = fs_io_manager
        job_def = define_job(io_manager)

        result = job_def.execute_in_process(instance=instance)
        assert result.success
        assert result.output_for_node("op_a") == [1, 2, 3]

        with open(
            os.path.join(instance.storage_directory(), result.run_id, "op_a", "result"),
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
        def get_op_version(self, _):
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
lam = lambda x: x * x


def test_fs_io_manager_unpicklable():
    @op
    def unpicklable_local_func_output():
        # locally defined functions can't be pickled (AttributeError)
        def local_func():
            return 1

        return local_func

    @op
    def unpicklable_lambda_output():
        return lam

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


def get_assets_job(io_manager_def, partitions_def=None):
    asset1_key_prefix = ["one", "two", "three"]

    @asset(key_prefix=["one", "two", "three"], partitions_def=partitions_def)
    def asset1():
        return [1, 2, 3]

    @asset(
        key_prefix=["four", "five"],
        ins={"asset1": AssetIn(key_prefix=asset1_key_prefix)},
        partitions_def=partitions_def,
    )
    def asset2(asset1):
        return asset1 + [4]

    return build_assets_job(
        name="a", assets=[asset1, asset2], resource_defs={"io_manager": io_manager_def}
    )


def test_fs_io_manager_handles_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})
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


def test_fs_io_manager_partitioned():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})
        job_def = get_assets_job(
            io_manager_def,
            partitions_def=DailyPartitionsDefinition(start_date="2020-02-01"),
        )

        result = job_def.execute_in_process(partition_key="2020-05-03")
        assert result.success

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 2

        filepath_a = os.path.join(tmpdir_path, "one", "two", "three", "asset1", "2020-05-03")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3]

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.all_node_events))
        assert len(loaded_input_events) == 1
        assert loaded_input_events[0].event_specific_data.upstream_step_key.endswith("asset1")

        filepath_b = os.path.join(tmpdir_path, "four", "five", "asset2", "2020-05-03")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == [1, 2, 3, 4]


def test_fs_io_manager_partitioned_no_partitions():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        class NoPartitionsPartitionMapping(PartitionMapping):
            def get_upstream_mapped_partitions_result_for_partitions(
                self,
                downstream_partitions_subset: Optional[PartitionsSubset],
                upstream_partitions_def: PartitionsDefinition,
                current_time: Optional[datetime] = None,
                dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
            ) -> UpstreamPartitionsResult:
                return UpstreamPartitionsResult(upstream_partitions_def.empty_subset(), [])

            def get_downstream_partitions_for_partitions(
                self,
                upstream_partitions_subset,
                downstream_partitions_def,
                current_time: Optional[datetime] = None,
                dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
            ):
                raise NotImplementedError()

        partitions_def = DailyPartitionsDefinition(start_date="2020-02-01")

        @asset(partitions_def=partitions_def)
        def asset1():
            ...

        @asset(
            partitions_def=partitions_def,
            ins={"asset1": AssetIn(partition_mapping=NoPartitionsPartitionMapping())},
        )
        def asset2(asset1):
            assert asset1 is None

        assert materialize(
            [asset1.to_source_assets()[0], asset2],
            partition_key="2020-02-01",
            resources={"io_manager": io_manager_def},
        ).success


def test_fs_io_manager_partitioned_multi_asset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        partitions = StaticPartitionsDefinition(["A"])

        @multi_asset(
            partitions_def=partitions,
            outs={
                "out_1": AssetOut(key=AssetKey("upstream_asset_1")),
                "out_2": AssetOut(key=AssetKey("upstream_asset_2")),
            },
        )
        def upstream_asset() -> Tuple[Output[int], Output[int]]:
            return (Output(1, output_name="out_1"), Output(2, output_name="out_2"))

        @asset(
            partitions_def=partitions,
        )
        def downstream_asset(upstream_asset_1: int) -> int:
            del upstream_asset_1
            return 2

        foo_job = Definitions(
            assets=[upstream_asset, downstream_asset],
            resources={"io_manager": io_manager_def},
            jobs=[define_asset_job("TheJob")],
        ).get_job_def("TheJob")

        result = foo_job.execute_in_process(partition_key="A")
        assert result.success

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 3


def test_fs_io_manager_partitioned_graph_backed_asset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})
        partitions_def = StaticPartitionsDefinition(["A"])

        @asset(key_prefix=["the", "cool", "prefix"], partitions_def=partitions_def)
        def one():
            return 1

        @op
        def add_1(inp):
            return inp + 1

        @graph
        def four(inp):
            return add_1(add_1(add_1(inp)))

        four_asset = AssetsDefinition.from_graph(
            four,
            keys_by_input_name={"inp": AssetKey(["the", "cool", "prefix", "one"])},
            partitions_def=partitions_def,
        )

        job_def = build_assets_job(
            name="a",
            assets=[one, four_asset],
            resource_defs={"io_manager": io_manager_def},
        )

        result = job_def.execute_in_process(partition_key="A")
        assert result.success

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 4

        filepath_a = os.path.join(tmpdir_path, "the", "cool", "prefix", "one", "A")
        assert os.path.isfile(filepath_a)
        with open(filepath_a, "rb") as read_obj:
            assert pickle.load(read_obj) == 1

        loaded_input_events = list(filter(lambda evt: evt.is_loaded_input, result.all_node_events))
        assert len(loaded_input_events) == 3
        assert loaded_input_events[0].event_specific_data.upstream_step_key.endswith("one")

        filepath_b = os.path.join(tmpdir_path, "four", "A")
        assert os.path.isfile(filepath_b)
        with open(filepath_b, "rb") as read_obj:
            assert pickle.load(read_obj) == 4


def test_fs_io_manager_partitioned_self_dep():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        @asset(
            partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
            ins={
                "a": AssetIn(
                    partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
                )
            },
        )
        def a(a: Optional[int]) -> int:
            return 1 if a is None else a + 1

        result = materialize(
            [a], partition_key="2020-01-01", resources={"io_manager": io_manager_def}
        )
        assert result.success
        assert result.output_for_node("a") == 1

        result2 = materialize(
            [a], partition_key="2020-01-02", resources={"io_manager": io_manager_def}
        )
        assert result2.success
        assert result2.output_for_node("a") == 2


def test_fs_io_manager_none():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        @asset
        def asset1() -> None:
            pass

        @asset(deps=[asset1])
        def asset2() -> None:
            pass

        result = materialize(
            with_resources([asset1, asset2], resource_defs={"io_manager": io_manager_def})
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "asset1"))
        assert not os.path.exists(os.path.join(tmpdir_path, "asset2"))
        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 2

        for event in handled_output_events:
            assert len(event.event_specific_data.metadata) == 0


def test_fs_io_manager_ops_none():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        @op
        def op1() -> None:
            pass

        @op(ins={"abc": In(Nothing)})
        def op2() -> None:
            pass

        @job(resource_defs={"io_manager": io_manager_def})
        def job1():
            op2(op1())

        result = job1.execute_in_process()

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 2

        for event in handled_output_events:
            assert len(event.event_specific_data.metadata) == 0


def test_multipartitions_fs_io_manager():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})
        multipartitions_def = MultiPartitionsDefinition(
            {
                "a": StaticPartitionsDefinition(["a", "b"]),
                "1": StaticPartitionsDefinition(["1", "2"]),
            }
        )

        @asset(
            partitions_def=multipartitions_def,
            io_manager_def=io_manager_def,
        )
        def asset1():
            return 1

        @asset(io_manager_def=io_manager_def, partitions_def=multipartitions_def)
        def asset2(asset1):
            return asset1

        my_job = define_asset_job("my_job", [asset1, asset2]).resolve([asset1, asset2], [])

        result = my_job.execute_in_process(partition_key=MultiPartitionKey({"a": "a", "1": "1"}))

        handled_output_events = list(
            filter(lambda evt: evt.is_handled_output, result.all_node_events)
        )
        assert len(handled_output_events) == 2


def test_backcompat_multipartitions_fs_io_manager():
    src_dir = file_relative_path(
        __file__, "backcompat_multipartitions_fs_io_manager/backcompat_materialization"
    )
    with tempfile.TemporaryDirectory() as test_dir:
        os.mkdir(os.path.join(test_dir, "multipartitioned"))

        io_manager_def = fs_io_manager.configured({"base_dir": test_dir})
        dest_file_path = os.path.join(test_dir, "multipartitioned", "c|2020-04-22")
        shutil.copyfile(src_dir, dest_file_path)

        composite = MultiPartitionsDefinition(
            {
                "abc": StaticPartitionsDefinition(["a", "b", "c", "d", "e", "f"]),
                "date": DailyPartitionsDefinition(start_date="2020-01-01"),
            }
        )

        @asset(
            partitions_def=composite,
            io_manager_def=io_manager_def,
        )
        def multipartitioned(context):
            return 1

        @asset(
            partitions_def=composite,
            io_manager_def=io_manager_def,
        )
        def downstream_of_multipartitioned(multipartitioned):
            return 1

        # Upstream partition was never materialized, so this run should error
        with pytest.raises(FileNotFoundError, match="c/2020-04-21"):
            my_job = define_asset_job(
                "my_job", [multipartitioned, downstream_of_multipartitioned]
            ).resolve([multipartitioned, downstream_of_multipartitioned], [])
            result = my_job.execute_in_process(
                partition_key=MultiPartitionKey({"abc": "c", "date": "2020-04-21"}),
                asset_selection=[AssetKey("downstream_of_multipartitioned")],
            )

        my_job = define_asset_job(
            "my_job", [multipartitioned, downstream_of_multipartitioned]
        ).resolve([multipartitioned, downstream_of_multipartitioned], [])
        result = my_job.execute_in_process(
            partition_key=MultiPartitionKey({"abc": "c", "date": "2020-04-22"}),
            asset_selection=[AssetKey("downstream_of_multipartitioned")],
        )
        assert result.success

        result = my_job.execute_in_process(
            partition_key=MultiPartitionKey({"abc": "c", "date": "2020-04-22"}),
        )
        assert result.success
        materializations = result.asset_materializations_for_node("multipartitioned")
        assert len(materializations) == 1

        get_path_metadata_entry = lambda materialization: materialization.metadata["path"]
        assert "c/2020-04-22" in get_path_metadata_entry(materializations[0]).path

        materializations = result.asset_materializations_for_node("downstream_of_multipartitioned")
        assert len(materializations) == 1
        assert "c/2020-04-22" in get_path_metadata_entry(materializations[0]).path
