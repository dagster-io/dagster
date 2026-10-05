from __future__ import annotations  # noqa: TID251

import dagster as dg
import pytest


def test_context_provided_to_asset():
    @dg.asset
    def no_annotation(context):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([no_annotation])

    @dg.asset
    def asset_annotation(context: dg.AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([asset_annotation])

    @dg.asset
    def op_annotation(context: dg.OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    dg.materialize([op_annotation])


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
