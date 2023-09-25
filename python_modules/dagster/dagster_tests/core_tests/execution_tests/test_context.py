import warnings

import dagster._check as check
import pytest
from dagster import AssetExecutionContext, OpExecutionContext, job, op
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
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
        asset_context = AssetExecutionContext(step_execution_context=step_context)
        op_context = OpExecutionContext(step_execution_context=step_context)
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
