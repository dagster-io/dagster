import tempfile

import dagster as dg
import dagster._check as check
import pytest
from dagster import (
    AssetCheckExecutionContext,
    AssetExecutionContext,
    AssetOut,
    DagsterInstance,
    OpExecutionContext,
    build_op_context,
)
from dagster._check import CheckError
from dagster._core.code_pointer import FileCodePointer
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.partitions.definition.static import StaticPartitionsDefinition
from dagster._core.origin import RemoteJobOrigin
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.fs_io_manager import FilesystemIOManager


def test_op_execution_context():
    @dg.op
    def ctx_op(context: OpExecutionContext):
        check.inst(context.run, dg.DagsterRun)
        assert context.job_name == "foo"
        assert context.job_def.name == "foo"
        check.inst(context.job_def, dg.JobDefinition)
        assert context.op_config is None
        check.inst(context.op_def, dg.OpDefinition)

    @dg.job
    def foo():
        ctx_op()

    assert foo.execute_in_process().success


@dg.op
def repo_context_op(context: OpExecutionContext):
    check.inst(context.repository_def, dg.RepositoryDefinition)


@dg.job
def foo_repo_context():
    repo_context_op()


def test_op_execution_repo_context():
    with pytest.raises(CheckError, match="No repository definition was set on the step context"):
        foo_repo_context.execute_in_process()

    recon_job = dg.reconstructable(foo_repo_context)

    with dg.instance_for_test() as instance:
        result = dg.execute_job(recon_job, instance)
        assert result.success


@dg.asset
def repo_context_asset(context: AssetExecutionContext):
    check.inst(context.repository_def, dg.RepositoryDefinition)


@dg.repository
def asset_context_repo():
    return [repo_context_asset, dg.define_asset_job("asset_selection_job", selection="*")]


def get_repo_context_asset_selection_job():
    return asset_context_repo.get_job("asset_selection_job")


def test_asset_execution_repo_context():
    with pytest.raises(CheckError, match="No repository definition was set on the step context"):
        dg.materialize([repo_context_asset])

    recon_job = dg.reconstructable(get_repo_context_asset_selection_job)

    with dg.instance_for_test() as instance:
        result = dg.execute_job(recon_job, instance)
        assert result.success


def test_context_provided_to_asset():
    @dg.asset
    def no_annotation(context):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([no_annotation])

    @dg.asset
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([asset_annotation])

    @dg.asset
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    dg.materialize([op_annotation])


def test_context_provided_to_op():
    @dg.op
    def no_annotation(context):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    @dg.job
    def no_annotation_job():
        no_annotation()

    assert no_annotation_job.execute_in_process().success

    @dg.op
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)

    @dg.job
    def asset_annotation_job():
        asset_annotation()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot annotate @op `context` parameter with type AssetExecutionContext",
    ):
        asset_annotation_job.execute_in_process()

    @dg.op
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    @dg.job
    def op_annotation_job():
        op_annotation()

    assert op_annotation_job.execute_in_process().success


def test_context_provided_to_multi_asset():
    @dg.multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def no_annotation(context):
        assert isinstance(context, dg.AssetExecutionContext)
        return None, None

    dg.materialize([no_annotation])

    @dg.multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)
        return None, None

    dg.materialize([asset_annotation])

    @dg.multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        return None, None

    dg.materialize([op_annotation])


def test_context_provided_to_graph_asset():
    # op so that the ops to check context type are layered deeper in the graph
    @dg.op
    def layered_op(context: AssetExecutionContext, x):
        assert isinstance(context, dg.AssetExecutionContext)
        return x + 1

    @dg.op
    def no_annotation_op(context):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_asset
    def no_annotation_asset():
        return no_annotation_op()

    dg.materialize([no_annotation_asset])

    @dg.op
    def asset_annotation_op(context: AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_asset
    def asset_annotation_asset():
        return layered_op(asset_annotation_op())

    dg.materialize([asset_annotation_asset])

    @dg.op
    def op_annotation_op(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_asset
    def op_annotation_asset():
        return layered_op(op_annotation_op())

    dg.materialize([op_annotation_asset])


def test_context_provided_to_graph_multi_asset():
    # op so that the ops to check context type are layered deeper in the graph
    @dg.op
    def layered_op(context: AssetExecutionContext, x):
        assert isinstance(context, dg.AssetExecutionContext)
        return x + 1

    @dg.op
    def no_annotation_op(context):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def no_annotation_asset():
        return layered_op(no_annotation_op()), layered_op(no_annotation_op())

    dg.materialize([no_annotation_asset])

    @dg.op
    def asset_annotation_op(context: AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def asset_annotation_asset():
        return layered_op(asset_annotation_op()), layered_op(asset_annotation_op())

    dg.materialize([asset_annotation_asset])

    @dg.op
    def op_annotation_op(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_multi_asset(
        outs={"out1": dg.AssetOut(dagster_type=None), "out2": dg.AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def op_annotation_asset():
        return layered_op(op_annotation_op()), layered_op(op_annotation_op())

    dg.materialize([op_annotation_asset])


def test_context_provided_to_plain_python():
    # tests a job created using Definitions classes, not decorators

    def no_annotation(context, *args):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        yield dg.Output(1)

    no_annotation_op = dg.OpDefinition(compute_fn=no_annotation, name="no_annotation_op")
    no_annotation_graph = dg.GraphDefinition(
        name="no_annotation_graph", node_defs=[no_annotation_op]
    )

    no_annotation_graph.to_job(name="no_annotation_job").execute_in_process()

    def asset_annotation(context: AssetExecutionContext, *args):
        assert False, "Test should error during context creation"

    asset_annotation_op = dg.OpDefinition(compute_fn=asset_annotation, name="asset_annotation_op")
    asset_annotation_graph = dg.GraphDefinition(
        name="asset_annotation_graph", node_defs=[asset_annotation_op]
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot annotate @op `context` parameter with type AssetExecutionContext",
    ):
        asset_annotation_graph.to_job(name="asset_annotation_job").execute_in_process()

    def op_annotation(context: OpExecutionContext, *args):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)
        yield dg.Output(1)

    op_annotation_op = dg.OpDefinition(compute_fn=op_annotation, name="op_annotation_op")
    op_annotation_graph = dg.GraphDefinition(
        name="op_annotation_graph", node_defs=[op_annotation_op]
    )

    op_annotation_graph.to_job(name="op_annotation_job").execute_in_process()


def test_context_provided_to_asset_check():
    instance = DagsterInstance.ephemeral()

    def execute_assets_and_checks(assets=None, asset_checks=None, raise_on_error: bool = True):
        defs = dg.Definitions(assets=assets, asset_checks=asset_checks)
        job_def = defs.resolve_implicit_global_asset_job_def()
        return job_def.execute_in_process(raise_on_error=raise_on_error, instance=instance)

    @dg.asset
    def to_check():
        return 1

    @dg.asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def no_annotation(context):
        assert isinstance(context, dg.AssetCheckExecutionContext)
        assert context.check_specs == [
            dg.AssetCheckSpec(
                "no_annotation",
                asset=to_check.key,
            )
        ]

    execute_assets_and_checks(assets=[to_check], asset_checks=[no_annotation])

    @dg.asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def asset_annotation(context: AssetExecutionContext):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot annotate @asset_check `context` parameter with type AssetExecutionContext",
    ):
        execute_assets_and_checks(assets=[to_check], asset_checks=[asset_annotation])

    @dg.asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[op_annotation])

    @dg.asset_check(asset=to_check)
    def check_annotation(context: AssetCheckExecutionContext):
        assert not isinstance(context, dg.AssetCheckExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[op_annotation])


def test_error_on_invalid_context_annotation():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @dg.op
        def the_op(context: int):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @dg.asset
        def the_asset(context: int):
            pass


def test_get_context():
    with pytest.raises(dg.DagsterInvariantViolationError):
        OpExecutionContext.get()

    @dg.op
    def o(context):
        assert context == OpExecutionContext.get()

    @dg.job
    def j():
        o()

    assert j.execute_in_process().success

    @dg.asset
    def a(context: AssetExecutionContext):
        assert context == AssetExecutionContext.get()

    assert dg.materialize([a]).success


def test_graph_multi_asset_out_from_spec() -> None:
    @dg.op
    def layered_op(x):
        return x + 1

    @dg.op
    def inner_op(context):
        return 1

    @dg.graph_multi_asset(
        outs={
            "out1": AssetOut.from_spec(dg.AssetSpec(key="my_key", kinds={"python", "s3"})),
            "out2": AssetOut.from_spec(
                dg.AssetSpec(key="my_other_key", kinds={"python", "snowflake"})
            ),
        }
    )
    def no_annotation_asset():
        return layered_op(inner_op()), layered_op(inner_op())

    assert len(no_annotation_asset.specs_by_key) == 2
    my_key_spec = no_annotation_asset.specs_by_key[dg.AssetKey("my_key")]
    assert my_key_spec.kinds == {"python", "s3"}
    my_other_key_spec = no_annotation_asset.specs_by_key[dg.AssetKey("my_other_key")]
    assert my_other_key_spec.kinds == {"python", "snowflake"}

    outs = dg.materialize([no_annotation_asset])
    assert outs.success


def test_graph_multi_asset_out_from_spec_deps() -> None:
    @dg.op
    def layered_op(x):
        return x + 1

    @dg.op
    def inner_op(context):
        return 1

    # Currently, cannot specify deps on AssetOut.from_spec
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.graph_multi_asset(
            outs={
                "out1": AssetOut.from_spec(dg.AssetSpec(key="my_key", deps={"my_upstream_asset"})),
                "out2": AssetOut.from_spec(
                    dg.AssetSpec(key="my_other_key", deps={"my_upstream_asset"})
                ),
            }
        )
        def no_annotation_asset():
            return layered_op(inner_op()), layered_op(inner_op())


def test_dynamically_loading_assets_from_context():
    @dg.asset(io_manager_key="fs_io_manager")
    def the_asset():
        return 5

    @dg.asset(io_manager_key="fs_io_manager", deps=[the_asset])
    def the_downstream_asset(context: AssetExecutionContext):
        return context.load_asset_value(the_asset.key) + 1

    defs = Definitions(
        assets=[the_asset, the_downstream_asset],
        resources={"fs_io_manager": FilesystemIOManager()},
    )
    global_asset_job = defs.get_implicit_global_asset_job_def()

    result = global_asset_job.execute_in_process()
    assert result.success
    assert result.output_for_node("the_downstream_asset") == 6


def test_dynamically_loading_assets_from_context_with_partition():
    static_partition = StaticPartitionsDefinition(["1", "2", "3"])

    @dg.asset(
        io_manager_key="fs_io_manager",
        partitions_def=static_partition,
    )
    def the_asset(context: AssetExecutionContext):
        return int(context.partition_key)

    @dg.asset(io_manager_key="fs_io_manager", deps=[the_asset], partitions_def=static_partition)
    def the_downstream_asset(context: AssetExecutionContext):
        return context.load_asset_value(the_asset.key, partition_key=context.partition_key) + 1

    defs = Definitions(
        assets=[the_asset, the_downstream_asset],
        resources={"fs_io_manager": FilesystemIOManager()},
    )
    global_asset_job = defs.get_implicit_global_asset_job_def()

    result = global_asset_job.execute_in_process(partition_key="1")
    assert result.success
    assert result.output_for_node("the_downstream_asset") == 2

    result = global_asset_job.execute_in_process(partition_key="3")
    assert result.success
    assert result.output_for_node("the_downstream_asset") == 4


def test_load_asset_value_with_python_type():
    @dg.asset(io_manager_key="fs_io_manager")
    def string_asset():
        return "hello"

    @dg.asset(io_manager_key="fs_io_manager")
    def int_asset():
        return 42

    @dg.asset(io_manager_key="fs_io_manager", deps=[string_asset, int_asset])
    def downstream_asset(context: AssetExecutionContext):
        # Test with explicit python_type
        string_value = context.load_asset_value(string_asset.key, python_type=str)
        int_value = context.load_asset_value(int_asset.key, python_type=int)

        assert isinstance(string_value, str)
        assert isinstance(int_value, int)
        return f"{string_value}_{int_value}"

    defs = Definitions(
        assets=[string_asset, int_asset, downstream_asset],
        resources={"fs_io_manager": FilesystemIOManager()},
    )
    global_asset_job = defs.get_implicit_global_asset_job_def()

    result = global_asset_job.execute_in_process()
    assert result.success
    assert result.output_for_node("downstream_asset") == "hello_42"


def test_load_asset_value_raises_key_error():
    @dg.asset(io_manager_key="fs_io_manager")
    def source_asset():
        return "data"

    @dg.asset(io_manager_key="fs_io_manager", deps=[source_asset])
    def downstream_asset(context: AssetExecutionContext):
        # Test loading non-existent asset
        with pytest.raises(KeyError) as exc_info:
            context.load_asset_value(dg.AssetKey("non_existent_asset"))
        assert "non_existent_asset" in str(exc_info.value)

    defs = Definitions(
        assets=[source_asset, downstream_asset],
        resources={"fs_io_manager": FilesystemIOManager()},
    )
    global_asset_job = defs.get_implicit_global_asset_job_def()

    result = global_asset_job.execute_in_process()
    assert result.success


def test_load_asset_value_with_complex_types():
    @dg.asset(io_manager_key="fs_io_manager")
    def list_asset():
        return [1, 2, 3, 4, 5]

    @dg.asset(io_manager_key="fs_io_manager")
    def dict_asset():
        return {"key1": "value1", "key2": "value2"}

    @dg.asset(io_manager_key="fs_io_manager", deps=[list_asset, dict_asset])
    def downstream_asset(context: AssetExecutionContext):
        # Test with complex python types
        list_value = context.load_asset_value(list_asset.key, python_type=list[int])
        dict_value = context.load_asset_value(dict_asset.key, python_type=dict[str, str])

        assert isinstance(list_value, list)
        assert isinstance(dict_value, dict)
        return len(list_value) + len(dict_value)

    defs = Definitions(
        assets=[list_asset, dict_asset, downstream_asset],
        resources={"fs_io_manager": FilesystemIOManager()},
    )
    global_asset_job = defs.get_implicit_global_asset_job_def()

    result = global_asset_job.execute_in_process()
    assert result.success
    assert result.output_for_node("downstream_asset") == 7  # 5 + 2


def test_load_asset_value_multiple_upstream_partition_keys():
    with tempfile.TemporaryDirectory() as temp_dir:
        io_manager = FilesystemIOManager(base_dir=temp_dir)
        partitions = StaticPartitionsDefinition(["2024-01-01", "2024-01-02", "2024-01-03"])

        @dg.asset(io_manager_key="partitioned_io_manager", partitions_def=partitions)
        def partitioned_source_asset(context: AssetExecutionContext):
            assert context.has_partition_key
            return int(context.partition_key.split("-")[-1])

        @dg.asset(io_manager_key="partitioned_io_manager", deps=[partitioned_source_asset])
        def downstream_asset(context: AssetExecutionContext):
            return (
                context.load_asset_value(partitioned_source_asset.key, partition_key="2024-01-01")
                + context.load_asset_value(partitioned_source_asset.key, partition_key="2024-01-02")
                + context.load_asset_value(partitioned_source_asset.key, partition_key="2024-01-03")
            )

        defs = Definitions(
            assets=[partitioned_source_asset, downstream_asset],
            resources={"partitioned_io_manager": io_manager},
        )
        global_asset_job = defs.get_implicit_global_asset_job_def()

        # Materialize each partition
        for partition_key in ["2024-01-01", "2024-01-02", "2024-01-03"]:
            result = global_asset_job.execute_in_process(
                partition_key=partition_key,
                asset_selection=[partitioned_source_asset.key],
            )
            assert result.success

        result = global_asset_job.execute_in_process(asset_selection=[downstream_asset.key])
        assert result.success
        assert result.output_for_node("downstream_asset") == 6


def test_location_name_property():
    """Test that location_name property correctly accesses remote_job_origin.location_name."""
    with dg.instance_for_test() as instance:
        # Test 1: When dagster_run is None, location_name should be None
        context_without_run = build_op_context()
        assert context_without_run.location_name is None

        # Test 2: When dagster_run exists but remote_job_origin is None, location_name should be None
        run_without_origin = DagsterRun(
            job_name="test_job",
            run_id="test_run_without_origin",
            remote_job_origin=None,
        )
        instance.add_run(run_without_origin)

        context_without_origin = build_op_context(
            dagster_run=run_without_origin,
            instance=instance,
        )
        assert context_without_origin.location_name is None

        # Test 3: When remote_job_origin exists with location_name, it should be returned
        remote_origin = RemoteJobOrigin(
            code_pointer=FileCodePointer(
                python_file="/fake/path/to/file.py",
                fn_name="fake_job",
            ),
            location_name="test_location_name",
        )

        run_with_origin = DagsterRun(
            job_name="test_job",
            run_id="test_run_with_origin",
            remote_job_origin=remote_origin,
        )
        instance.add_run(run_with_origin)

        context_with_origin = build_op_context(
            dagster_run=run_with_origin,
            instance=instance,
        )
        assert context_with_origin.location_name == "test_location_name"
