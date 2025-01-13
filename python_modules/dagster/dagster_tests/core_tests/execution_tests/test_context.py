import dagster._check as check
import pytest
from dagster import (
    AssetCheckExecutionContext,
    AssetExecutionContext,
    AssetOut,
    DagsterInstance,
    Definitions,
    GraphDefinition,
    OpExecutionContext,
    Output,
    asset,
    asset_check,
    define_asset_job,
    execute_job,
    graph_asset,
    graph_multi_asset,
    job,
    materialize,
    multi_asset,
    op,
    reconstructable,
    repository,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import instance_for_test


def test_op_execution_context():
    @op
    def ctx_op(context: OpExecutionContext):
        check.inst(context.run, DagsterRun)
        assert context.job_name == "foo"
        assert context.job_def.name == "foo"
        check.inst(context.job_def, JobDefinition)
        assert context.op_config is None
        check.inst(context.op_def, OpDefinition)

    @job
    def foo():
        ctx_op()

    assert foo.execute_in_process().success


@op
def repo_context_op(context: OpExecutionContext):
    check.inst(context.repository_def, RepositoryDefinition)


@job
def foo_repo_context():
    repo_context_op()


def test_op_execution_repo_context():
    with pytest.raises(CheckError, match="No repository definition was set on the step context"):
        foo_repo_context.execute_in_process()

    recon_job = reconstructable(foo_repo_context)

    with instance_for_test() as instance:
        result = execute_job(recon_job, instance)
        assert result.success


@asset
def repo_context_asset(context: AssetExecutionContext):
    check.inst(context.repository_def, RepositoryDefinition)


@repository
def asset_context_repo():
    return [repo_context_asset, define_asset_job("asset_selection_job", selection="*")]


def get_repo_context_asset_selection_job():
    return asset_context_repo.get_job("asset_selection_job")


def test_asset_execution_repo_context():
    with pytest.raises(CheckError, match="No repository definition was set on the step context"):
        materialize([repo_context_asset])

    recon_job = reconstructable(get_repo_context_asset_selection_job)

    with instance_for_test() as instance:
        result = execute_job(recon_job, instance)
        assert result.success


def test_context_provided_to_asset():
    @asset
    def no_annotation(context):
        assert isinstance(context, AssetExecutionContext)

    materialize([no_annotation])

    @asset
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)

    materialize([asset_annotation])

    @asset
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)

    materialize([op_annotation])


def test_context_provided_to_op():
    @op
    def no_annotation(context):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)

    @job
    def no_annotation_job():
        no_annotation()

    assert no_annotation_job.execute_in_process().success

    @op
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)

    @job
    def asset_annotation_job():
        asset_annotation()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot annotate @op `context` parameter with type AssetExecutionContext",
    ):
        asset_annotation_job.execute_in_process()

    @op
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)

    @job
    def op_annotation_job():
        op_annotation()

    assert op_annotation_job.execute_in_process().success


def test_context_provided_to_multi_asset():
    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})  # pyright: ignore[reportArgumentType]
    def no_annotation(context):
        assert isinstance(context, AssetExecutionContext)
        return None, None

    materialize([no_annotation])

    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})  # pyright: ignore[reportArgumentType]
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return None, None

    materialize([asset_annotation])

    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})  # pyright: ignore[reportArgumentType]
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return None, None

    materialize([op_annotation])


def test_context_provided_to_graph_asset():
    # op so that the ops to check context type are layered deeper in the graph
    @op
    def layered_op(context: AssetExecutionContext, x):
        assert isinstance(context, AssetExecutionContext)
        return x + 1

    @op
    def no_annotation_op(context):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return 1

    @graph_asset
    def no_annotation_asset():
        return no_annotation_op()

    materialize([no_annotation_asset])

    @op
    def asset_annotation_op(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return 1

    @graph_asset
    def asset_annotation_asset():
        return layered_op(asset_annotation_op())

    materialize([asset_annotation_asset])

    @op
    def op_annotation_op(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return 1

    @graph_asset
    def op_annotation_asset():
        return layered_op(op_annotation_op())

    materialize([op_annotation_asset])


def test_context_provided_to_graph_multi_asset():
    # op so that the ops to check context type are layered deeper in the graph
    @op
    def layered_op(context: AssetExecutionContext, x):
        assert isinstance(context, AssetExecutionContext)
        return x + 1

    @op
    def no_annotation_op(context):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return 1

    @graph_multi_asset(
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def no_annotation_asset():
        return layered_op(no_annotation_op()), layered_op(no_annotation_op())

    materialize([no_annotation_asset])

    @op
    def asset_annotation_op(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return 1

    @graph_multi_asset(
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def asset_annotation_asset():
        return layered_op(asset_annotation_op()), layered_op(asset_annotation_op())

    materialize([asset_annotation_asset])

    @op
    def op_annotation_op(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return 1

    @graph_multi_asset(
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}  # pyright: ignore[reportArgumentType]
    )
    def op_annotation_asset():
        return layered_op(op_annotation_op()), layered_op(op_annotation_op())

    materialize([op_annotation_asset])


def test_context_provided_to_plain_python():
    # tests a job created using Definitions classes, not decorators

    def no_annotation(context, *args):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        yield Output(1)

    no_annotation_op = OpDefinition(compute_fn=no_annotation, name="no_annotation_op")
    no_annotation_graph = GraphDefinition(name="no_annotation_graph", node_defs=[no_annotation_op])

    no_annotation_graph.to_job(name="no_annotation_job").execute_in_process()

    def asset_annotation(context: AssetExecutionContext, *args):
        assert False, "Test should error during context creation"

    asset_annotation_op = OpDefinition(compute_fn=asset_annotation, name="asset_annotation_op")
    asset_annotation_graph = GraphDefinition(
        name="asset_annotation_graph", node_defs=[asset_annotation_op]
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot annotate @op `context` parameter with type AssetExecutionContext",
    ):
        asset_annotation_graph.to_job(name="asset_annotation_job").execute_in_process()

    def op_annotation(context: OpExecutionContext, *args):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        yield Output(1)

    op_annotation_op = OpDefinition(compute_fn=op_annotation, name="op_annotation_op")
    op_annotation_graph = GraphDefinition(name="op_annotation_graph", node_defs=[op_annotation_op])

    op_annotation_graph.to_job(name="op_annotation_job").execute_in_process()


def test_context_provided_to_asset_check():
    instance = DagsterInstance.ephemeral()

    def execute_assets_and_checks(assets=None, asset_checks=None, raise_on_error: bool = True):
        defs = Definitions(assets=assets, asset_checks=asset_checks)
        job_def = defs.get_implicit_global_asset_job_def()
        return job_def.execute_in_process(raise_on_error=raise_on_error, instance=instance)

    @asset
    def to_check():
        return 1

    @asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def no_annotation(context):
        assert isinstance(context, AssetCheckExecutionContext)
        assert context.check_specs == [
            AssetCheckSpec(
                "no_annotation",
                asset=to_check.key,
            )
        ]

    execute_assets_and_checks(assets=[to_check], asset_checks=[no_annotation])

    @asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def asset_annotation(context: AssetExecutionContext):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot annotate @asset_check `context` parameter with type AssetExecutionContext",
    ):
        execute_assets_and_checks(assets=[to_check], asset_checks=[asset_annotation])

    @asset_check(asset=to_check)  # pyright: ignore[reportArgumentType]
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[op_annotation])

    @asset_check(asset=to_check)
    def check_annotation(context: AssetCheckExecutionContext):
        assert not isinstance(context, AssetCheckExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[op_annotation])


def test_error_on_invalid_context_annotation():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @op
        def the_op(context: int):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @asset
        def the_asset(context: int):
            pass


def test_get_context():
    with pytest.raises(DagsterInvariantViolationError):
        OpExecutionContext.get()

    @op
    def o(context):
        assert context == OpExecutionContext.get()

    @job
    def j():
        o()

    assert j.execute_in_process().success

    @asset
    def a(context: AssetExecutionContext):
        assert context == AssetExecutionContext.get()

    assert materialize([a]).success


def test_graph_multi_asset_out_from_spec() -> None:
    @op
    def layered_op(x):
        return x + 1

    @op
    def inner_op(context):
        return 1

    @graph_multi_asset(
        outs={
            "out1": AssetOut.from_spec(AssetSpec(key="my_key", kinds={"python", "s3"})),
            "out2": AssetOut.from_spec(
                AssetSpec(key="my_other_key", kinds={"python", "snowflake"})
            ),
        }
    )
    def no_annotation_asset():
        return layered_op(inner_op()), layered_op(inner_op())

    assert len(no_annotation_asset.specs_by_key) == 2
    my_key_spec = no_annotation_asset.specs_by_key[AssetKey("my_key")]
    assert my_key_spec.kinds == {"python", "s3"}
    my_other_key_spec = no_annotation_asset.specs_by_key[AssetKey("my_other_key")]
    assert my_other_key_spec.kinds == {"python", "snowflake"}

    outs = materialize([no_annotation_asset])
    assert outs.success


def test_graph_multi_asset_out_from_spec_deps() -> None:
    @op
    def layered_op(x):
        return x + 1

    @op
    def inner_op(context):
        return 1

    # Currently, cannot specify deps on AssetOut.from_spec
    with pytest.raises(DagsterInvalidDefinitionError):

        @graph_multi_asset(
            outs={
                "out1": AssetOut.from_spec(AssetSpec(key="my_key", deps={"my_upstream_asset"})),
                "out2": AssetOut.from_spec(
                    AssetSpec(key="my_other_key", deps={"my_upstream_asset"})
                ),
            }
        )
        def no_annotation_asset():
            return layered_op(inner_op()), layered_op(inner_op())
