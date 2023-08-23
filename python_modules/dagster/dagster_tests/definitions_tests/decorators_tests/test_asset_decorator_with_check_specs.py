import re

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    AssetOut,
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    MetadataValue,
    Output,
    asset,
    materialize,
    multi_asset,
)
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
)


def test_asset_check_same_op():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key="asset1", description="desc")])
    def asset1():
        yield Output(None)
        yield AssetCheckResult(check_name="check1", success=True, metadata={"foo": "bar"})

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
    materialization_record = instance.get_event_records(
        EventRecordsFilter(event_type=DagsterEventType.ASSET_MATERIALIZATION)
    )[0]
    assert check_eval.target_materialization_data.storage_id == materialization_record.storage_id
    assert check_eval.target_materialization_data.timestamp == materialization_record.timestamp


def test_multiple_asset_checks_same_op():
    @asset(
        check_specs=[
            AssetCheckSpec("check1", asset_key="asset1", description="desc"),
            AssetCheckSpec("check2", asset_key="asset1", description="desc"),
        ]
    )
    def asset1():
        yield Output(None)
        yield AssetCheckResult(check_name="check1", success=True, metadata={"foo": "bar"})
        yield AssetCheckResult(check_name="check2", success=False, metadata={"baz": "bla"})

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


def test_check_targets_other_asset():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key="asset2", description="desc")])
    def asset1():
        yield Output(None)
        yield AssetCheckResult(
            asset_key="asset2", check_name="check1", success=True, metadata={"foo": "bar"}
        )

    result = materialize(assets=[asset1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset2")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_check_targets_other_asset_and_result_omits_key():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key="asset2", description="desc")])
    def asset1():
        yield Output(None)
        yield AssetCheckResult(check_name="check1", success=True, metadata={"foo": "bar"})

    result = materialize(assets=[asset1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset2")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_no_result_for_check():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key="asset1")])
    def asset1():
        yield Output(None)

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output'
            ' "asset1_check1"'
        ),
    ):
        materialize(assets=[asset1])


def test_check_result_but_no_output():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key="asset1")])
    def asset1():
        yield AssetCheckResult(success=True)

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset1" did not return an output for non-optional output "result"'
        ),
    ):
        materialize(assets=[asset1])


def test_unexpected_check_name():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key=AssetKey("asset1"), description="desc")])
    def asset1():
        return AssetCheckResult(check_name="check2", success=True, metadata={"foo": "bar"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "No checks currently being evaluated target asset 'asset1' and have name"
            " 'check2'. Checks being evaluated for this asset: {'check1'}"
        ),
    ):
        materialize(assets=[asset1])


def test_asset_decorator_unexpected_asset_key():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key=AssetKey("asset1"), description="desc")])
    def asset1():
        return AssetCheckResult(asset_key=AssetKey("asset2"), check_name="check1", success=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Received unexpected AssetCheckResult. It targets asset 'asset2' which is not targeted"
            " by any of the checks currently being evaluated. Targeted assets: ['asset1']."
        ),
    ):
        materialize(assets=[asset1])


def test_result_missing_check_name():
    @asset(
        check_specs=[
            AssetCheckSpec("check1", asset_key="asset1"),
            AssetCheckSpec("check2", asset_key="asset1"),
        ]
    )
    def asset1():
        yield Output(None)
        yield AssetCheckResult(success=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult result didn't specify a check name, but there are multiple checks to"
            " choose from for the this asset key:"
        ),
    ):
        materialize(assets=[asset1])


def test_asset_check_fails_downstream_still_executes():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key=AssetKey("asset1"))])
    def asset1():
        yield Output(None)
        yield AssetCheckResult(success=False)

    @asset(deps=[asset1])
    def asset2():
        ...

    result = materialize(assets=[asset1, asset2])
    assert result.success

    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert not check_eval.success


def test_duplicate_checks_same_asset():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("Duplicate check specs: {(AssetKey(['asset1']), 'check1'): 2}"),
    ):

        @asset(
            check_specs=[
                AssetCheckSpec("check1", asset_key="asset1", description="desc1"),
                AssetCheckSpec("check1", asset_key="asset1", description="desc2"),
            ]
        )
        def asset1():
            ...


def test_multi_asset_with_check():
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[AssetCheckSpec("check1", asset_key="asset1", description="desc")],
    )
    def asset_1_and_2():
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(check_name="check1", success=True, metadata={"foo": "bar"})

    result = materialize(assets=[asset_1_and_2])
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_multi_asset_no_result_for_check():
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[AssetCheckSpec("check1", asset_key="asset1", description="desc")],
    )
    def asset_1_and_2():
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "asset_1_and_2" did not return an output for non-optional output'
            ' "asset1_check1"'
        ),
    ):
        materialize(assets=[asset_1_and_2])


def test_result_missing_asset_key():
    @multi_asset(
        outs={"one": AssetOut("asset1"), "two": AssetOut("asset2")},
        check_specs=[
            AssetCheckSpec("check1", asset_key="asset1"),
            AssetCheckSpec("check2", asset_key="asset2"),
        ],
    )
    def asset_1_and_2():
        yield Output(None, output_name="one")
        yield Output(None, output_name="two")
        yield AssetCheckResult(success=True)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "AssetCheckResult didn't specify an asset key, but there are multiple assets to choose"
            " from: ['asset1', 'asset2']"
        ),
    ):
        materialize(assets=[asset_1_and_2])
