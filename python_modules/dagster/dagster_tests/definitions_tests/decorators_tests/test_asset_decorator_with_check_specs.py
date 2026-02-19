import re
from collections.abc import Iterable
from typing import Any

import dagster as dg
import pytest
from dagster import (
    DagsterInstance,
    MetadataValue,
    _check as check,
)
from dagster._core.definitions.asset_selection import AssetCheckKeysSelection, AssetSelection
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus


def test_asset_check_same_op() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = dg.materialize(assets=[asset1], instance=instance)
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
    @dg.asset(
        key_prefix="my_prefix",
        check_specs=[
            dg.AssetCheckSpec(
                "check1", asset=dg.AssetKey(["my_prefix", "asset1"]), description="desc"
            )
        ],
    )
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = dg.materialize(assets=[asset1], instance=instance)
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
    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1", description="desc"),
            dg.AssetCheckSpec("check2", asset="asset1", description="desc"),
        ]
    )
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})
        yield dg.AssetCheckResult(check_name="check2", passed=False, metadata={"baz": "bla"})

    result = dg.materialize(assets=[asset1])
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
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield dg.Output(None)

    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output'
            ' "asset1_check1"'
        ),
    ):
        dg.materialize(assets=[asset1])


def test_check_result_but_no_output() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield dg.AssetCheckResult(passed=True)

    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output "result"'
        ),
    ):
        dg.materialize(assets=[asset1])


def test_unexpected_check_name() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(check_name="check2", passed=True, metadata={"foo": "bar"})

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            r"No checks currently being evaluated target asset 'asset1' and have name"
            " 'check2'. Checks being evaluated for this asset: {'check1'}"
        ),
    ):
        dg.materialize(assets=[asset1])


def test_asset_decorator_unexpected_asset_key() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            asset_key=dg.AssetKey("asset2"), check_name="check1", passed=True
        )

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "Received unexpected AssetCheckResult. It targets asset 'asset2' which is not targeted"
            " by any of the checks currently being evaluated. Targeted assets: ['asset1']."
        ),
    ):
        dg.materialize(assets=[asset1])


def test_result_missing_check_name() -> None:
    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset1"),
        ]
    )
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(passed=True)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult result didn't specify a check name, but there are multiple checks to"
            " choose from for the this asset key:"
        ),
    ):
        dg.materialize(assets=[asset1])


def test_unexpected_result() -> None:
    @dg.asset
    def my_asset() -> Iterable:
        yield dg.AssetCheckResult(passed=True)

    result = dg.materialize(assets=[my_asset], raise_on_error=False)
    assert not result.success
    assert (
        "Received unexpected AssetCheckResult. No AssetCheckSpecs were found for this step."
        "You may need to set `check_specs` on the asset decorator, or you may be emitting an "
        "AssetCheckResult that isn't in the subset passed in `context.selected_asset_check_keys`."
        in check.not_none(result.get_step_failure_events()[0].step_failure_data.error).message
    )


def test_asset_check_fails_downstream_still_executes() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1")])
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(passed=False)

    @dg.asset(deps=[asset1])
    def asset2() -> None: ...

    result = dg.materialize(assets=[asset1, asset2])
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed


def test_blocking_check_skips_downstream() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", blocking=True)])
    def asset1() -> Iterable:
        yield dg.Output(5)
        yield dg.AssetCheckResult(passed=False)

    @dg.asset
    def asset2(asset1: int) -> None:
        assert asset1 == 5

    result = dg.materialize(assets=[asset1, asset2], raise_on_error=False)
    assert not result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    error = check.not_none(result.failure_data_for_node("asset1")).error
    assert check.not_none(error).message.startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:\nasset1: check1"
    )


def test_duplicate_checks_same_asset() -> None:
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape("Duplicate check specs: {(AssetKey(['asset1']), 'check1'): 2}"),
    ):

        @dg.asset(
            check_specs=[
                dg.AssetCheckSpec("check1", asset="asset1", description="desc1"),
                dg.AssetCheckSpec("check1", asset="asset1", description="desc2"),
            ]
        )
        def asset1() -> None: ...


def test_check_wrong_asset() -> None:
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape("Invalid asset key"),
    ):

        @dg.asset(
            check_specs=[
                dg.AssetCheckSpec("check1", asset="other_asset", description="desc1"),
            ]
        )
        def asset1() -> None: ...


def test_multi_asset_with_check() -> None:
    @dg.multi_asset(
        outs={"one": dg.AssetOut("asset1"), "two": dg.AssetOut("asset2")},
        check_specs=[
            dg.AssetCheckSpec("check1", asset=dg.AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield dg.Output(None, output_name="one")
        yield dg.Output(None, output_name="two")
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    result = dg.materialize(assets=[asset_1_and_2])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_multi_asset_no_result_for_check() -> None:
    @dg.multi_asset(
        outs={"one": dg.AssetOut("asset1"), "two": dg.AssetOut("asset2")},
        check_specs=[
            dg.AssetCheckSpec("check1", asset=dg.AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield dg.Output(None, output_name="one")
        yield dg.Output(None, output_name="two")

    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset_1_and_2" did not return an output for non-optional output'
            ' "asset1__one_check1"'
        ),
    ):
        dg.materialize(assets=[asset_1_and_2])


def test_multi_asset_blocking_check_skips_downstream() -> None:
    @dg.multi_asset(
        outs={"one": dg.AssetOut("asset1"), "two": dg.AssetOut("asset2")},
        check_specs=[
            dg.AssetCheckSpec("check1", asset=dg.AssetKey(["asset1", "one"]), blocking=True),
            dg.AssetCheckSpec("check2", asset=dg.AssetKey(["asset1", "one"]), blocking=True),
            dg.AssetCheckSpec("check3", asset=dg.AssetKey(["asset1", "one"]), blocking=False),
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield dg.Output(None, output_name="one")
        yield dg.AssetCheckResult(check_name="check1", passed=False)
        yield dg.AssetCheckResult(check_name="check2", passed=False)
        yield dg.AssetCheckResult(check_name="check3", passed=False)
        yield dg.Output(None, output_name="two")

    @dg.asset(deps=[dg.AssetKey(["asset1", "one"])])
    def asset3() -> None:
        pass

    @dg.asset(deps=[dg.AssetKey(["asset2", "two"])])
    def asset4() -> None:
        pass

    result = dg.materialize(assets=[asset_1_and_2, asset3, asset4], raise_on_error=False)
    assert not result.success

    # note: currently asset4 won't run because asset_1_and_2 failed, but ideally it would run
    # because only the check on asset1 failed.
    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2
    assert materialization_events[0].asset_key == dg.AssetKey(["asset1", "one"])
    assert materialization_events[1].asset_key == dg.AssetKey(["asset2", "two"])

    check_evals = result.get_asset_check_evaluations()

    assert len(check_evals) == 3
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check1"
    assert not check_eval.passed

    check_eval = check_evals[1]
    assert check_eval.asset_key == dg.AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check2"
    assert not check_eval.passed

    check_eval = check_evals[2]
    assert check_eval.asset_key == dg.AssetKey(["asset1", "one"])
    assert check_eval.check_name == "check3"
    assert not check_eval.passed

    error = check.not_none(check.not_none(result.failure_data_for_node("asset_1_and_2")).error)

    assert check.not_none(error.message).startswith(
        "dagster._core.errors.DagsterAssetCheckFailedError: 2 blocking asset checks failed with ERROR severity:\nasset1/one: check1,check2"
    )


def test_result_missing_asset_key() -> None:
    @dg.multi_asset(
        outs={"one": dg.AssetOut(key="asset1"), "two": dg.AssetOut(key="asset2")},
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield dg.Output(None, output_name="one")
        yield dg.Output(None, output_name="two")
        yield dg.AssetCheckResult(passed=True)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult didn't specify an asset key, but there are multiple assets to choose"
            " from"
        ),
    ):
        dg.materialize(assets=[asset_1_and_2])


def test_asset_check_doesnt_store_output() -> None:
    handle_output_called = 0

    class DummyIOManager(dg.IOManager):
        def handle_output(self, context, obj) -> None:
            assert context
            assert obj == "the-only-allowed-output"

            nonlocal handle_output_called
            handle_output_called += 1

        def load_input(self, context) -> dict:
            assert context
            return {}

    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield dg.Output("the-only-allowed-output")
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    instance = DagsterInstance.ephemeral()
    result = dg.materialize(
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
    @dg.multi_asset(
        outs={
            "one": dg.AssetOut(key="asset1", is_required=False),
            "two": dg.AssetOut(key="asset2", is_required=False),
        },
        check_specs=[dg.AssetCheckSpec("check1", asset=dg.AssetKey(["asset1"]))],
        can_subset=True,
    )
    def asset_1_and_2(context: AssetExecutionContext) -> Iterable:
        if dg.AssetKey("asset1") in context.selected_asset_keys:
            yield dg.Output(None, output_name="one")
            yield dg.AssetCheckResult(check_name="check1", passed=True)
        if dg.AssetKey("asset2") in context.selected_asset_keys:
            yield dg.Output(None, output_name="two")

    # no selection
    with dg.instance_for_test() as instance:
        result = dg.materialize(assets=[asset_1_and_2], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 2
        check_evals = result.get_asset_check_evaluations()
        assert len(check_evals) == 1
        check_eval = check_evals[0]
        assert check_eval.asset_key == dg.AssetKey(["asset1"])
        assert check_eval.check_name == "check1"
        assert (
            instance.event_log_storage.get_asset_check_execution_history(
                dg.AssetCheckKey(dg.AssetKey(["asset1"]), name="check1"), limit=1
            )[0].status
            == AssetCheckExecutionRecordStatus.SUCCEEDED
        )

    # asset1
    with dg.instance_for_test() as instance:
        result = dg.materialize(assets=[asset_1_and_2], selection=["asset1"], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 1
        check_evals = result.get_asset_check_evaluations()
        assert len(check_evals) == 1
        check_eval = check_evals[0]
        assert check_eval.asset_key == dg.AssetKey(["asset1"])
        assert check_eval.check_name == "check1"
        assert (
            instance.event_log_storage.get_asset_check_execution_history(
                check_key=dg.AssetCheckKey(dg.AssetKey(["asset1"]), name="check1"), limit=1
            )[0].status
            == AssetCheckExecutionRecordStatus.SUCCEEDED
        )

    # asset2
    with dg.instance_for_test() as instance:
        result = dg.materialize(assets=[asset_1_and_2], selection=["asset2"], instance=instance)
        assert result.success
        assert len(result.get_asset_materialization_events()) == 1
        assert not result.get_asset_check_evaluations()
        assert not instance.event_log_storage.get_asset_check_execution_history(
            check_key=dg.AssetCheckKey(dg.AssetKey(["asset1"]), name="check1"), limit=1
        )


def test_graph_asset() -> None:
    @dg.op
    # must be Any to not skip i/o manager shenanigans
    def create_asset() -> Any:
        return None

    @dg.op
    # must be Any to avoid runtime error because internal machinery thinks we returned None
    def validate_asset(word) -> Any:
        return dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    @dg.op
    # must be Any to avoid runtime error because internal machinery thinks we returned None
    def non_blocking_validation(word) -> Any:
        return dg.AssetCheckResult(check_name="check2", passed=True, metadata={"biz": "buz"})

    @dg.op(ins={"staging_asset": dg.In(dg.Nothing), "check_result": dg.In(dg.Nothing)})
    # must be Any to not skip i/o manager shenanigans
    def promote_asset() -> Any:
        return None

    @dg.graph_asset(
        name="foo",
        check_specs=[
            dg.AssetCheckSpec("check1", asset="foo", description="desc"),
            dg.AssetCheckSpec("check2", asset="foo", description="desc"),
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

    result = dg.materialize(assets=[asset1])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    evals_by_name = {check_eval.check_name: check_eval for check_eval in check_evals}
    assert evals_by_name.keys() == {"check1", "check2"}
    assert evals_by_name["check1"].asset_key == dg.AssetKey("foo")
    assert evals_by_name["check1"].metadata == {"foo": MetadataValue.text("bar")}

    assert evals_by_name["check2"].asset_key == dg.AssetKey("foo")
    assert evals_by_name["check2"].metadata == {"biz": MetadataValue.text("buz")}


def test_graph_multi_asset() -> None:
    # typed to Any to skip various type-annotation-based bugs in framework
    # see test_graph_asset for more detailed comments

    @dg.op
    def create_asset() -> Any:
        return None

    @dg.op
    def validate_asset(word) -> Any:
        return dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    @dg.op(ins={"staging_asset": dg.In(dg.Nothing), "check_result": dg.In(dg.Nothing)})
    def promote_asset() -> Any:
        return None

    @dg.op
    def create_asset_2() -> Any:
        return None

    @dg.graph_multi_asset(
        outs={"asset_one": dg.AssetOut(), "asset_two": dg.AssetOut()},
        check_specs=[dg.AssetCheckSpec("check1", asset="asset_one", description="desc")],
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

    result = dg.materialize(assets=[asset1])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset_one")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_can_subset_no_selection() -> None:
    @dg.multi_asset(
        can_subset=True,
        specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext) -> Iterable:
        assert context.selected_asset_keys == {dg.AssetKey("asset1"), dg.AssetKey("asset2")}
        assert context.selected_asset_check_keys == {
            dg.AssetCheckKey(dg.AssetKey("asset1"), "check1"),
            dg.AssetCheckKey(dg.AssetKey("asset2"), "check2"),
        }

        yield dg.Output(value=None, output_name="asset1")
        yield dg.AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = dg.materialize([foo])

    assert len(result.get_asset_materialization_events()) == 1

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"


def test_can_subset() -> None:
    @dg.multi_asset(
        can_subset=True,
        specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {dg.AssetKey("asset1")}
        assert context.selected_asset_check_keys == {
            dg.AssetCheckKey(dg.AssetKey("asset1"), "check1")
        }

        yield dg.Output(value=None, output_name="asset1")
        yield dg.AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = dg.materialize([foo], selection=["asset1"])

    assert len(result.get_asset_materialization_events()) == 1

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"


def test_can_subset_result_for_unselected_check(capsys) -> None:
    @dg.multi_asset(
        can_subset=True,
        specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {dg.AssetKey("asset1")}
        assert context.selected_asset_check_keys == {
            dg.AssetCheckKey(dg.AssetKey("asset1"), "check1")
        }

        yield dg.Output(value=None, output_name="asset1")
        yield dg.AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)
        yield dg.AssetCheckResult(asset_key="asset2", check_name="check2", passed=True)

    result = dg.materialize([foo], selection=["asset1"])
    assert "not selected" in capsys.readouterr().err
    assert result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 2


def test_can_subset_select_only_asset() -> None:
    @dg.multi_asset(
        can_subset=True,
        specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == {dg.AssetKey("asset1")}
        assert context.selected_asset_check_keys == set()

        yield dg.Output(value=None, output_name="asset1")

    result = dg.materialize(
        [foo],
        selection=AssetSelection.assets(dg.AssetKey("asset1"))
        - AssetSelection.checks_for_assets(foo),
    )

    assert len(result.get_asset_materialization_events()) == 1

    check_evals = result.get_asset_check_evaluations()

    assert len(check_evals) == 0


def test_can_subset_select_only_check() -> None:
    @dg.multi_asset(
        can_subset=True,
        specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1"),
            dg.AssetCheckSpec("check2", asset="asset2"),
        ],
    )
    def foo(context: AssetExecutionContext):
        assert context.selected_asset_keys == set()
        assert context.selected_asset_check_keys == {
            dg.AssetCheckKey(dg.AssetKey("asset1"), "check1")
        }

        yield dg.AssetCheckResult(asset_key="asset1", check_name="check1", passed=True)

    result = dg.materialize(
        [foo],
        selection=AssetCheckKeysSelection(
            selected_asset_check_keys=[
                dg.AssetCheckKey(asset_key=dg.AssetKey("asset1"), name="check1")
            ]
        ),
    )

    assert len(result.get_asset_materialization_events()) == 0

    [check_eval] = result.get_asset_check_evaluations()

    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"


@dg.op
# typed as Any to avoid io-manager-based bugs
def create_asset() -> Any:
    return None


@dg.op
# typed as Any to avoid io-manager-based bugs
def validate_asset(word) -> Any:
    return dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})


@dg.graph_multi_asset(
    outs={"asset_one": dg.AssetOut(), "asset_two": dg.AssetOut()},
    check_specs=[dg.AssetCheckSpec("check1", asset="asset_one", description="desc")],
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
    result = dg.materialize(assets=[my_asset])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    assert len(result.get_asset_check_evaluations()) == 1


def test_graph_asset_subset_no_checks() -> None:
    result = dg.materialize(
        assets=[my_asset],
        selection=AssetSelection.assets(dg.AssetKey("asset_one")).without_checks(),
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert not result.get_asset_check_evaluations()


def test_graph_asset_subset_with_checks() -> None:
    result = dg.materialize(
        assets=[my_asset], selection=AssetSelection.assets(dg.AssetKey("asset_one"))
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


@dg.op
def validate_asset_1(word) -> Any:
    return dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})


@dg.op
def validate_asset_2(word) -> Any:
    return word


@dg.graph_multi_asset(
    outs={"asset_one": dg.AssetOut(), "asset_two": dg.AssetOut()},
    check_specs=[dg.AssetCheckSpec("check1", asset="asset_one", description="desc")],
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
    result = dg.materialize(assets=[nested_check_graph_asset])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    assert len(result.get_asset_check_evaluations()) == 1


def test_nested_graph_asset_subset_no_checks() -> None:
    result = dg.materialize(
        assets=[nested_check_graph_asset],
        selection=AssetSelection.assets(dg.AssetKey("asset_one")).without_checks(),
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert not result.get_asset_check_evaluations()


def test_nested_graph_asset_subset_with_checks() -> None:
    result = dg.materialize(
        assets=[nested_check_graph_asset], selection=AssetSelection.assets(dg.AssetKey("asset_one"))
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


@dg.op(ins={"staging_asset": dg.In(dg.Nothing), "check_result": dg.In(dg.Nothing)})
def promote_asset() -> Any:
    return None


@dg.graph_multi_asset(
    outs={"asset_one": dg.AssetOut(), "asset_two": dg.AssetOut()},
    check_specs=[dg.AssetCheckSpec("check1", asset="asset_one", description="desc")],
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
    result = dg.materialize(
        assets=[validate_promote_graph_asset],
        selection=AssetSelection.assets(dg.AssetKey("asset_one")),
    )
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1


def test_direct_invocation() -> None:
    @dg.asset(check_specs=[dg.AssetCheckSpec("check1", asset="asset1", description="desc")])
    def asset1() -> Iterable:
        yield dg.Output(None)
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    results = list(check.is_iterable(asset1()))
    assert len(results) == 2
    assert isinstance(results[0], dg.Output)
    assert isinstance(results[1], dg.AssetCheckResult)
    assert results[1].passed


def test_multi_asset_direct_invocation() -> None:
    @dg.multi_asset(
        outs={"one": dg.AssetOut("asset1"), "two": dg.AssetOut("asset2")},
        check_specs=[
            dg.AssetCheckSpec("check1", asset=dg.AssetKey(["asset1", "one"]), description="desc")
        ],
    )
    def asset_1_and_2() -> Iterable:
        yield dg.Output(None, output_name="one")
        yield dg.Output(None, output_name="two")
        yield dg.AssetCheckResult(check_name="check1", passed=True, metadata={"foo": "bar"})

    results = list(check.is_iterable(asset_1_and_2()))
    assert len(results) == 3
    assert isinstance(results[0], dg.Output)
    assert isinstance(results[1], dg.Output)
    assert isinstance(results[2], dg.AssetCheckResult)
    assert results[2].passed


def test_additional_deps_with_multi_asset_decorator() -> None:
    # Document that it's not possible to specify an asset in referencing an additional_dep of an asset check.
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.multi_asset(
            specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")],
            check_specs=[
                dg.AssetCheckSpec(
                    "check1", asset="asset1", additional_deps=[dg.AssetDep("asset3")]
                ),  # spec with a dep external to this asset
            ],
            ins={"asset3": dg.AssetIn()},
        )
        def foo(context: AssetExecutionContext, asset3) -> Iterable:
            yield dg.Output(value=None, output_name="asset1")
            yield dg.Output(value=None, output_name="asset2")


def test_arbitary_asset_check_specs() -> None:
    """Test hidden behavior where we allow arbitrary asset check specs to be passed in
    to the asset decorator. This is necessary to model things like dbt source checks.
    """

    @dg.multi_asset(
        check_specs=[
            dg.AssetCheckSpec("check1", asset="asset1", description="desc"),
            dg.AssetCheckSpec("check2", asset="asset2", description="desc"),
        ],
        specs=[dg.AssetSpec("asset1")],
        allow_arbitrary_check_specs=True,
        can_subset=True,
    )
    def _compute() -> Iterable:
        yield dg.AssetMaterialization("asset1")
        yield dg.AssetCheckResult(
            check_name="check1", asset_key="asset1", passed=True, metadata={"foo": "bar"}
        )
        yield dg.AssetCheckResult(
            check_name="check2", asset_key="asset2", passed=True, metadata={"baz": "bla"}
        )

    instance = DagsterInstance.ephemeral()
    result = dg.materialize(assets=[_compute], instance=instance)
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    check_eval = check_evals[0]
    assert check_eval.asset_key == dg.AssetKey("asset1")
    assert check_eval.check_name == "check1"
