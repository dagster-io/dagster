import warnings

import dagster._check as check
import pytest
from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetOut,
    DagsterInstance,
    Definitions,
    GraphDefinition,
    MaterializeResult,
    OpExecutionContext,
    Output,
    asset,
    asset_check,
    graph_asset,
    graph_multi_asset,
    job,
    materialize,
    multi_asset,
    op,
)
from dagster._core.definitions.asset_checks import build_asset_with_blocking_check
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.storage.dagster_run import DagsterRun


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


def test_instance_check():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    warnings.filterwarnings("error")

    class AssetExecutionContextSubclass(AssetExecutionContext):
        # allows us to confirm isinstance(context, AssetExecutionContext)
        # does not throw deprecation warnings
        def __init__(self):
            pass

    @op
    def test_op_context_instance_check(context: OpExecutionContext):
        step_context = context._step_execution_context  # noqa: SLF001
        op_context = OpExecutionContext(step_execution_context=step_context)
        asset_context = AssetExecutionContext(op_execution_context=op_context)
        with pytest.raises(DeprecationWarning):
            isinstance(asset_context, OpExecutionContext)
        assert not isinstance(op_context, AssetExecutionContext)

        # the instance checks below will not hit the metaclass __instancecheck__ method because
        # python returns early if the type is the same
        # https://github.com/python/cpython/blob/b57b4ac042b977e0b42a2f5ddb30ca7edffacfa9/Objects/abstract.c#L2404
        # but still test for completeness
        assert isinstance(asset_context, AssetExecutionContext)
        assert isinstance(op_context, OpExecutionContext)

        # since python short circuits when context is AssetExecutionContext and you call
        # isinstance(context, AssetExecutionContext), make a subclass of AssetExecutionContext
        # so that we can ensure isinstance(context, AssetExecutionContext) doesn't throw a
        # deprecation warning

        asset_subclass_context = AssetExecutionContextSubclass()
        assert isinstance(asset_subclass_context, AssetExecutionContext)

    @job
    def test_isinstance():
        test_op_context_instance_check()

    test_isinstance.execute_in_process()


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
    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})
    def no_annotation(context):
        assert isinstance(context, AssetExecutionContext)
        return None, None

    materialize([no_annotation])

    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return None, None

    materialize([asset_annotation])

    @multi_asset(outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)})
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
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}
    )
    def no_annotation_asset():
        return layered_op(no_annotation_op()), layered_op(no_annotation_op())

    materialize([no_annotation_asset])

    @op
    def asset_annotation_op(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return 1

    @graph_multi_asset(
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}
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
        outs={"out1": AssetOut(dagster_type=None), "out2": AssetOut(dagster_type=None)}
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

    @asset_check(asset=to_check)
    def no_annotation(context):
        assert isinstance(context, AssetExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[no_annotation])

    @asset_check(asset=to_check)
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[asset_annotation])

    @asset_check(asset=to_check)
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)

    execute_assets_and_checks(assets=[to_check], asset_checks=[op_annotation])


def test_context_provided_to_blocking_asset_check():
    instance = DagsterInstance.ephemeral()

    def execute_assets_and_checks(assets=None, asset_checks=None, raise_on_error: bool = True):
        defs = Definitions(assets=assets, asset_checks=asset_checks)
        job_def = defs.get_implicit_global_asset_job_def()
        return job_def.execute_in_process(raise_on_error=raise_on_error, instance=instance)

    @asset
    def to_check():
        return 1

    @asset_check(asset=to_check)
    def no_annotation(context):
        assert isinstance(context, OpExecutionContext)
        return AssetCheckResult(passed=True, check_name="no_annotation")

    no_annotation_blocking_asset = build_asset_with_blocking_check(
        asset_def=to_check, checks=[no_annotation]
    )
    execute_assets_and_checks(assets=[no_annotation_blocking_asset])

    @asset_check(asset=to_check)
    def asset_annotation(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        return AssetCheckResult(passed=True, check_name="asset_annotation")

    asset_annotation_blocking_asset = build_asset_with_blocking_check(
        asset_def=to_check, checks=[asset_annotation]
    )
    execute_assets_and_checks(assets=[asset_annotation_blocking_asset])

    @asset_check(asset=to_check)
    def op_annotation(context: OpExecutionContext):
        assert isinstance(context, OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, AssetExecutionContext)
        return AssetCheckResult(passed=True, check_name="op_annotation")

    op_annotation_blocking_asset = build_asset_with_blocking_check(
        asset_def=to_check, checks=[op_annotation]
    )
    execute_assets_and_checks(assets=[op_annotation_blocking_asset])


def test_error_on_invalid_context_annotation():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, OpExecutionContext, or left blank",
    ):

        @op
        def the_op(context: int):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, OpExecutionContext, or left blank",
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


def test_upstream_metadata():
    # with output metadata
    @asset
    def upstream(context: AssetExecutionContext):
        context.add_output_metadata({"foo": "bar"})

    @asset
    def downstream(context: AssetExecutionContext, upstream):
        mat = context.latest_materialization_for_upstream_asset("upstream")
        assert mat is not None
        assert mat.metadata["foo"].value == "bar"

    materialize([upstream, downstream])


def test_upstream_metadata_materialize_result():
    # with asset materialization
    @asset
    def upstream():
        return MaterializeResult(metadata={"foo": "bar"})

    @asset
    def downstream(context: AssetExecutionContext, upstream):
        mat = context.latest_materialization_for_upstream_asset("upstream")
        assert mat is not None
        assert mat.metadata["foo"].value == "bar"

    materialize([upstream, downstream])
