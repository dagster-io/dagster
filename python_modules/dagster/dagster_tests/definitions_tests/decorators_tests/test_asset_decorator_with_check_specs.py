import re
from collections.abc import Iterable
from typing import Any

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    AssetOut,
    DagsterInstance,
    In,
    MetadataValue,
    Output,
    _check as check,
    asset,
    graph_asset,
    graph_multi_asset,
    materialize,
    multi_asset,
    op,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_selection import AssetCheckKeysSelection, AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
)
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.io_manager import IOManager
from dagster._core.test_utils import instance_for_test
from dagster._core.types.dagster_type import Nothing


def test_asset_check_same_op() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = materialize(assets=[asset1], instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == result.run_id
    materialization_record = instance.fetch_materializations(asset1.key, limit=1).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_asset_check_same_op_with_key_prefix() -> None:
    @asset(
        key_prefix="my_prefix",
        check_specs=[
            AssetCheckSpec("check1", asset=AssetKey(["my_prefix", "asset1"]), description="desc")
        ],
    )
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = materialize(assets=[asset1], instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == result.run_id
    materialization_record = instance.fetch_materializations(asset1.key, limit=1).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_multiple_asset_checks_same_op() -> None:
    @asset(
        check_specs=[
            AssetCheckSpec("check1", asset="asset1", description="desc"),
            AssetCheckSpec("check2", asset="asset1", description="desc"),
        ]
    )
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})
        yield AssetCheckResult(check_name="check2", passed=False, metadata={"baz": "bla"})

    result = materialize(assets=[asset1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    assert check_evals[0].asset_key == asset1.key
    assert check_evals[0].check_name == "check1"
    assert check_evals[0].metadata == {"foo": MetadataValue.text("bar")}

    assert check_evals[1].asset_key == asset1.key
    assert check_evals[1].check_name == "check2"
    assert check_evals[1].metadata == {"baz": MetadataValue.text("bla")}


def test_no_result_for_check() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield Output(None)

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output'
            ' "asset1_check1"'
        ),
    ):
        materialize(assets=[asset1])


def test_check_result_but_no_output() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield AssetCheckResult(passed=True)

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output "result"'
        ),
    ):
        materialize(assets=[asset1])


def test_unexpected_check_name() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> AssetCheckResult:
        return AssetCheckResult(check_name="check2", passed=True, metadata={"foo": "bar"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "No checks currently being evaluated target asset 'asset1' and have name"
            " 'check2'. Checks being evaluated for this asset: {'check1'}"
        ),
    ):
        materialize(assets=[asset1])


def test_asset_decorator_unexpected_asset_key() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> AssetCheckResult:
        return AssetCheckResult(asset_key=AssetKey("asset2"), check_name="check1", passed=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Received unexpected AssetCheckResult. It targets asset 'asset2' which is not targeted"
            " by any of the checks currently being evaluated. Targeted assets: ['asset1']."
        ),
    ):
        materialize(assets=[asset1])


def test_result_missing_check_name() -> None:
    @asset(
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset1"),
        ]
    )
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(passed=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult result didn't specify a check name, but there are multiple checks to"
            " choose from for the this asset key:"
        ),
    ):
        materialize(assets=[asset1])


def test_unexpected_result() -> None:
    @asset
    def my_asset() -> Iterable:
        yield AssetCheckResult(passed=True)

    result = materialize(assets=[my_asset], raise_on_error=False)
    assert not result.success
    assert (
        "Received unexpected AssetCheckResult. No AssetCheckSpecs were found for this step."
        "You may need to set `check_specs` on the asset decorator, or you may be emitting an "
        "AssetCheckResult that isn't in the subset passed in `context.selected_asset_check_keys`."
        in check.not_none(result.get_step_failure_events()[0].step_failure_data.error).message
    )


def test_asset_check_fails_downstream_still_executes() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(passed=False)

    @asset(deps=[asset1])
    def asset2() -> None: ...

    result = materialize(assets=[asset1, asset2])
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed


def test_blocking_check_skips_downstream() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", blocking=True)])
    def asset1() -> Iterable:
        yield Output(5)
        yield AssetCheckResult(passed=False)

    @asset
    def asset2(asset1: int) -> None:
        assert asset1 == 5

    result = materialize(assets=[asset1, asset2], raise_on_error=False)
    assert not result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    error = check.not_none(result.failure_data_for_node("asset1")).error
    assert check.not_none(error).message.startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: Blocking check 'check1' for asset 'asset1'"
        " failed with ERROR severity."
    )


def test_duplicate_checks_same_asset() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("Duplicate check specs: {(AssetKey(['asset1']), 'check1'): 2}"),
    ):

        @asset(
            check_specs=[
                AssetCheckSpec("check1", asset="asset1", description="desc1"),
                AssetCheckSpec("check1", asset="asset1", description="desc2"),
            ]
        )
        def asset1() -> None: ...


def test_check_wrong_asset() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("Invalid asset key"),
    ):

        @asset(
            check_specs=[
                AssetCheckSpec("check1", asset="other_asset", description="desc1"),
            ]
        )
        def asset1() -> None: ...


def test_multi_asset_with_check() -> None:
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[
            AssetCheckSpec("check1", asset=AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    result = materialize(assets=[asset_1_and_2])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_multi_asset_no_result_for_check() -> None:
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[
            AssetCheckSpec("check1", asset=AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset_1_and_2" did not return an output for non-optional output'
            ' "asset1__one_check1"'
        ),
    ):
        materialize(assets=[asset_1_and_2])


def test_multi_asset_blocking_check_skips_downstream() -> None:
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[AssetCheckSpec("check1", asset=AssetKey(["asset1", "one"]), blocking=True)],
    )
    def asset_1_and_2() -> Iterable:
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(check_name="check1", passed=False)

    @asset(deps=[AssetKey(["asset1", "one"])])
    def asset3() -> None:
        pass

    @asset(deps=[AssetKey(["asset2", "two"])])
    def asset4() -> None:
        pass

    result = materialize(assets=[asset_1_and_2, asset3, asset4], raise_on_error=False)
    assert not result.success

    # note: currently asset4 won't run because asset_1_and_2 failed, but ideally it would run
    # because only the check on asset1 failed.
    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2
    assert materialization_events[0].asset_key == AssetKey(["asset1", "one"])
    assert materialization_events[1].asset_key == AssetKey(["asset2", "two"])

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    error = check.not_none(check.not_none(result.failure_data_for_node("asset_1_and_2")).error)
    assert check.not_none(error.message).startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: Blocking check 'check1' for asset 'asset1/one'"
        " failed with ERROR severity."
    )


def test_result_missing_asset_key() -> None:
    @multi_asset(
        outs={"one": AssetOut(key="asset1"), "two": AssetOut(key="asset2")},
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(passed=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult didn't specify an asset key, but there are multiple assets to choose"
            " from: ['asset1', 'asset2']"
        ),
    ):
        materialize(assets=[asset_1_and_2])


def test_asset_check_doesnt_store_output() -> None:
    handle_output_called = 0

    class DummyIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            assert context
            assert obj == "the-only-allowed-output"

            nonlocal handle_output_called
            handle_output_called += 1

        def load_input(self, context) -> dict:
            assert context
            return {}

    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield Output("the-only-allowed-output")
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = materialize(
        assets=[asset1], instance=instance, resources={"io_manager": DummyIOManager()}
    )
    assert result.success
    assert handle_output_called == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}

    assert check_eval.target_materialization_data is not None
    assert check_eval.target_materialization_data.run_id == result.run_id
    materialization_record = instance.fetch_materializations(asset1.key, limit=1).records[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_multi_asset_with_check_subset() -> None:
    @multi_asset(
        outs={
            "one": AssetOut(key="asset1", is_required=False),
            "two": AssetOut(key="asset2", is_required=False),
        },
        check_specs=[AssetCheckSpec("check1", asset=AssetKey(["asset1"]))],
        can_subset=True,
    )
    def asset_1_and_2(context: AssetExecutionContext) -> Iterable:
        if AssetKey("asset1") in context.selected_asset_keys:
            yield Output(None, output_name="one")
            yield AssetCheckResult(check_name="check1", passed=True)
        if AssetKey("asset2") in context.selected_asset_keys:
            yield Output(None, output_name="two")

    # no selection
    with instance_for_test() as instance:
        result = materialize(assets=[asset_1_and_2], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 2
        check_evals = result.get_asset_check_evaluations()
        assert len(check_evals) == 1
        check_eval = check_evals[0]
        assert check_eval.asset_key == AssetKey(["asset1"])
        assert check_eval.check_name == "check1"
        assert (
            instance.event_log_storage.get_asset_check_execution_history(
                AssetCheckKey(AssetKey(["asset1"]), name="check1"), limit=1
            )[0].status
            == AssetCheckExecutionRecordStatus.SUCCEEDED
        )

    # asset1
    with instance_for_test() as instance:
        result = materialize(assets=[asset_1_and_2], selection=["asset1"], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 1
        check_evals = result.get_asset_check_evaluations()
        assert len(check_evals) == 1
        check_eval = check_evals[0]
        assert check_eval.asset_key == AssetKey(["asset1"])
        assert check_eval.check_name == "check1"
        assert (
            instance.event_log_storage.get_asset_check_execution_history(
                check_key=AssetCheckKey(AssetKey(["asset1"]), name="check1"), limit=1
            )[0].status
            == AssetCheckExecutionRecordStatus.SUCCEEDED
        )

    # asset2
    with instance_for_test() as instance:
        result = materialize(assets=[asset_1_and_2], selection=["asset2"], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 1
        assert not result.get_asset_check_evaluations()
        assert not instance.event_log_storage.get_asset_check_execution_history(
            check_key=AssetCheckKey(AssetKey(["asset1"]), name="check1"), limit=1
        )


def test_graph_asset() -> None:
    @op
    # must be Any to not skip i/o manager shenanigans
    def create_asset() -> Any:
        return None

    @op
    # must be Any to avoid runtime error because internal machinery thinks we returned None
    def validate_asset(word) -> Any:
        return AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    @op
    # must be Any to avoid runtime error because internal machinery thinks we returned None
    def non_blocking_validation(word) -> Any:
        return AssetCheckResult(check_name="check2", passed=True, metadata={"biz": "buz"})

    @op(ins={"staging_asset": In(Nothing), "check_result": In(Nothing)})
    # must be Any to not skip i/o manager shenanigans
    def promote_asset() -> Any:
        return None

    @graph_asset(
        name="foo",
        check_specs=[
            AssetCheckSpec("check1", asset="foo", description="desc"),
            AssetCheckSpec("check2", asset="foo", description="desc"),
        ],
    )
    def asset1() -> dict:
        staging_asset = create_asset()
        check_result = validate_asset(staging_asset)
        promoted_asset = promote_asset(staging_asset=staging_asset, check_result=check_result)
        return {
            "result": promoted_asset,
            "foo_check1": check_result,
            "foo_check2": non_blocking_validation(staging_asset),
        }

    result = materialize(assets=[asset1])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    evals_by_name = {check_eval.check_name: check_eval for check_eval in check_evals}
    assert evals_by_name.keys() == {"check1", "check2"}
    assert evals_by_name["check1"].asset_key == AssetKey("foo")
    assert evals_by_name["check1"].metadata == {"foo": MetadataValue.text("bar")}

    assert evals_by_name["check2"].asset_key == AssetKey("foo")
    assert evals_by_name["check2"].metadata == {"biz": MetadataValue.text("buz")}


def test_graph_multi_asset() -> None:
    # typed to Any to skip various type-annotation-based bugs in framework
    # see test_graph_asset for more detailed comments

    @op
    def create_asset() -> Any:
        return None

    @op
    def validate_asset(word) -> Any:
        return AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    @op(ins={"staging_asset": In(Nothing), "check_result": In(Nothing)})
    def promote_asset() -> Any:
        return None

    @op
    def create_asset_2() -> Any:
        return None

    @graph_multi_asset(
        outs={"asset_one": AssetOut(), "asset_two": AssetOut()},
        check_specs=[AssetCheckSpec("check1", asset="asset_one", description="desc")],
    )
    def asset1() -> dict:
        staging_asset = create_asset()
        check_result = validate_asset(staging_asset)
        promoted_asset = promote_asset(staging_asset=staging_asset, check_result=check_result)
        return {
            "asset_one": promoted_asset,
            "asset_one_check1": check_result,
            "asset_two": create_asset_2(),
        }

    result = materialize(assets=[asset1])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset_one")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_can_subset_no_selection() -> None:
    @multi_asset(
        can_subset=True,
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext) -> Iterable:
        assert context.selected_asset_keys == {AssetKey("asset1"), AssetKey("asset2")}
        assert context.selected_asset_check_keys == {
            AssetCheckKey(AssetKey("asset1"), "check1"),
            AssetCheckKey(AssetKey("asset2"), "check2"),
        }

        yield Output(value=None, output_name="asset1")
        yield AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = materialize([foo])

    assert len(result.get_asset_materialization_events()) == 1

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"


def test_can_subset() -> None:
    @multi_asset(
        can_subset=True,
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {AssetKey("asset1")}
        assert context.selected_asset_check_keys == {AssetCheckKey(AssetKey("asset1"), "check1")}

        yield Output(value=None, output_name="asset1")
        yield AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = materialize([foo], selection=["asset1"])

    assert len(result.get_asset_materialization_events()) == 1

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"


def test_can_subset_result_for_unselected_check() -> None:
    @multi_asset(
        can_subset=True,
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {AssetKey("asset1")}
        assert context.selected_asset_check_keys == {AssetCheckKey(AssetKey("asset1"), "check1")}

        yield Output(value=None, output_name="asset1")
        yield AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)
        yield AssetCheckResult(asset_key="asset2", check_name="check2", passed=True)

    with pytest.raises(DagsterInvariantViolationError):
        materialize([foo], selection=["asset1"])


def test_can_subset_select_only_asset() -> None:
    @multi_asset(
        can_subset=True,
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {AssetKey("asset1")}
        assert context.selected_asset_check_keys == set()

        yield Output(value=None, output_name="asset1")

    result = materialize(
        [foo],
        selection=AssetSelection.assets(AssetKey("asset1")) - AssetSelection.checks_for_assets(foo),
    )

    assert len(result.get_asset_materialization_events()) == 1

    check_evals = result.get_asset_check_evaluations()

    assert len(check_evals) == 0


def test_can_subset_select_only_check() -> None:
    @multi_asset(
        can_subset=True,
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        check_specs=[
            AssetCheckSpec("check1", asset="asset1"),
            AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == set()
        assert context.selected_asset_check_keys == {AssetCheckKey(AssetKey("asset1"), "check1")}

        yield AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = materialize(
        [foo],
        selection=AssetCheckKeysSelection(
            selected_asset_check_keys=[AssetCheckKey(asset_key=AssetKey("asset1"), name="check1")]
        ),
    )

    assert len(result.get_asset_materialization_events()) == 0

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"


@op
# typed as Any to avoid io-manager-based bugs
def create_asset() -> Any:
    return None


@op
# typed as Any to avoid io-manager-based bugs
def validate_asset(word) -> Any:
    return AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})


@graph_multi_asset(
    outs={"asset_one": AssetOut(), "asset_two": AssetOut()},
    check_specs=[AssetCheckSpec("check1", asset="asset_one", description="desc")],
    can_subset=True,
)
def my_asset() -> dict:
    asset_one = create_asset()
    return {
        "asset_one": asset_one,
        "asset_one_check1": validate_asset(asset_one),
        "asset_two": create_asset(),
    }


def test_graph_asset_all() -> None:
    result = materialize(assets=[my_asset])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    assert len(result.get_asset_check_evaluations()) == 1


def test_graph_asset_subset_no_checks() -> None:
    result = materialize(
        assets=[my_asset], selection=AssetSelection.assets(AssetKey("asset_one")).without_checks()
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert not result.get_asset_check_evaluations()


def test_graph_asset_subset_with_checks() -> None:
    result = materialize(assets=[my_asset], selection=AssetSelection.assets(AssetKey("asset_one")))
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


@op
def validate_asset_1(word) -> Any:
    return AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})


@op
def validate_asset_2(word) -> Any:
    return word


@graph_multi_asset(
    outs={"asset_one": AssetOut(), "asset_two": AssetOut()},
    check_specs=[AssetCheckSpec("check1", asset="asset_one", description="desc")],
    can_subset=True,
)
def nested_check_graph_asset() -> dict:
    asset_one = create_asset()
    return {
        "asset_one": asset_one,
        "asset_one_check1": validate_asset_2(validate_asset_1(asset_one)),
        "asset_two": create_asset(),
    }


def test_nested_graph_asset_all() -> None:
    result = materialize(assets=[nested_check_graph_asset])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    assert len(result.get_asset_check_evaluations()) == 1


def test_nested_graph_asset_subset_no_checks() -> None:
    result = materialize(
        assets=[nested_check_graph_asset],
        selection=AssetSelection.assets(AssetKey("asset_one")).without_checks(),
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert not result.get_asset_check_evaluations()


def test_nested_graph_asset_subset_with_checks() -> None:
    result = materialize(
        assets=[nested_check_graph_asset], selection=AssetSelection.assets(AssetKey("asset_one"))
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


@op(ins={"staging_asset": In(Nothing), "check_result": In(Nothing)})
def promote_asset() -> Any:
    return None


@graph_multi_asset(
    outs={"asset_one": AssetOut(), "asset_two": AssetOut()},
    check_specs=[AssetCheckSpec("check1", asset="asset_one", description="desc")],
    can_subset=True,
)
def validate_promote_graph_asset() -> dict:
    staging_asset = create_asset()
    check_result = validate_asset(staging_asset)
    promoted_asset = promote_asset(staging_asset=staging_asset, check_result=check_result)
    return {
        "asset_one": promoted_asset,
        "asset_one_check1": check_result,
        "asset_two": create_asset(),
    }


def test_validate_promote_graph_asset_subset_checks_and_asset() -> None:
    result = materialize(
        assets=[validate_promote_graph_asset],
        selection=AssetSelection.assets(AssetKey("asset_one")),
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


def test_direct_invocation() -> None:
    @asset(check_specs=[AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield Output(None)
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    results = list(check.is_iterable(asset1()))
    assert len(results) == 2
    assert isinstance(results[0], Output)
    assert isinstance(results[1], AssetCheckResult)
    assert results[1].passed


def test_multi_asset_direct_invocation() -> None:
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[
            AssetCheckSpec("check1", asset=AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    results = list(check.is_iterable(asset_1_and_2()))
    assert len(results) == 3
    assert isinstance(results[0], Output)
    assert isinstance(results[1], Output)
    assert isinstance(results[2], AssetCheckResult)
    assert results[2].passed


def test_additional_deps_with_multi_asset_decorator() -> None:
    # Document that it's not possible to specify an asset in referencing an additional_dep of an asset check.
    with pytest.raises(DagsterInvalidDefinitionError):

        @multi_asset(
            specs=[AssetSpec("asset1"), AssetSpec("asset2")],
            check_specs=[
                AssetCheckSpec(
                    "check1", asset="asset1", additional_deps=[AssetDep("asset3")]
                ),  # spec with a dep external to this asset
            ],
            ins={"asset3": AssetIn()},
        )
        def foo(context: AssetExecutionContext, asset3) -> Iterable:
            yield Output(value=None, output_name="asset1")
            yield Output(value=None, output_name="asset2")
