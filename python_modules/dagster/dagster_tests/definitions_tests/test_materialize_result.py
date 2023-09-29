from typing import Tuple

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetSpec,
    DagsterInvariantViolationError,
    IOManager,
    MaterializeResult,
    asset,
    instance_for_test,
    materialize,
    multi_asset,
)
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus


def test_materialize_result_asset():
    @asset
    def ret_untyped(context: AssetExecutionContext):
        return MaterializeResult(
            metadata={"one": 1},
        )

    result = materialize([ret_untyped])
    assert result.success
    mats = result.asset_materializations_for_node(ret_untyped.node_def.name)
    assert len(mats) == 1, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags

    # key mismatch
    @asset
    def ret_mismatch(context: AssetExecutionContext):
        return MaterializeResult(
            asset_key="random",
            metadata={"one": 1},
        )

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        materialize(ret_mismatch)


def test_return_materialization_with_asset_checks():
    with instance_for_test() as instance:

        @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey("ret_checks"))])
        def ret_checks(context: AssetExecutionContext):
            return MaterializeResult(
                check_results=[
                    AssetCheckResult(check_name="foo_check", metadata={"one": 1}, passed=True)
                ]
            )

        materialize([ret_checks], instance=instance)
        asset_check_executions = instance.event_log_storage.get_asset_check_executions(
            asset_key=ret_checks.key,
            check_name="foo_check",
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED


def test_materialize_result_output_typing():
    # Test that the return annotation MaterializeResult is interpreted as a Nothing type, since we
    # coerce returned MaterializeResults to Output(None)

    class TestingIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.dagster_type.is_nothing
            return None

        def load_input(self, context):
            return 1

    @asset
    def asset_with_type_annotation() -> MaterializeResult:
        return MaterializeResult(metadata={"foo": "bar"})

    assert materialize(
        [asset_with_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def multi_asset_with_outs_and_type_annotation() -> Tuple[MaterializeResult, MaterializeResult]:
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    assert materialize(
        [multi_asset_with_outs_and_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs_and_type_annotation() -> Tuple[MaterializeResult, MaterializeResult]:
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    assert materialize(
        [multi_asset_with_specs_and_type_annotation], resources={"io_manager": TestingIOManager()}
    ).success

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def multi_asset_with_specs_and_no_type_annotation():
        return MaterializeResult(asset_key="one"), MaterializeResult(asset_key="two")

    assert materialize(
        [multi_asset_with_specs_and_no_type_annotation],
        resources={"io_manager": TestingIOManager()},
    ).success


def test_direct_invocation_materialize_result():
    @asset
    def my_asset() -> MaterializeResult:
        return MaterializeResult(metadata={"foo": "bar"})

    res = my_asset()
    assert res.metadata["foo"] == "bar"

    # @asset
    # def generator_asset() -> Generator[MaterializeResult, None, None]:
    #     yield MaterializeResult(metadata={"foo": "bar"})

    # res = list(generator_asset())
    # assert res[0].metadata["foo"] == "bar"

    @multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
    def specs_multi_asset():
        return MaterializeResult(asset_key="one", metadata={"foo": "bar"}), MaterializeResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    res = specs_multi_asset()
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    # @multi_asset(
    #     specs=[AssetSpec("one"), AssetSpec("two")]
    # )
    # def generator_specs_multi_asset():
    #     yield MaterializeResult(asset_key="one", metadata={"foo": "bar"})
    #     yield MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    # res = list(generator_specs_multi_asset())
    # assert res[0].metadata["foo"] == "bar"
    # assert res[1].metadata["baz"] == "qux"

    @multi_asset(outs={"one": AssetOut(), "two": AssetOut()})
    def outs_multi_asset():
        return MaterializeResult(asset_key="one", metadata={"foo": "bar"}), MaterializeResult(
            asset_key="two", metadata={"baz": "qux"}
        )

    res = outs_multi_asset()
    assert res[0].metadata["foo"] == "bar"
    assert res[1].metadata["baz"] == "qux"

    # @multi_asset(
    #     outs={"one": AssetOut(), "two": AssetOut()}
    # )
    # def generator_outs_multi_asset():
    #     yield MaterializeResult(asset_key="one", metadata={"foo": "bar"})
    #     yield MaterializeResult(asset_key="two", metadata={"baz": "qux"})

    # res = list(generator_outs_multi_asset())
    # assert res[0].metadata["foo"] == "bar"
    # assert res[1].metadata["baz"] == "qux"

    # need to test generator cases too see _type_check_output_wrapper for all cases
