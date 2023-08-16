"""Stuff to test: context methods.

Definitions

allow multiple checks for the same name if they have different assets, but not if they have the same
asset

this should happen even when the checks are defined within assets

name parameter on asset_check decorator

can you have a check for an asset that doesn't exist in the repo?

test uses context inside asset_check-decorated function

- Pythonic config and resources in the arguments of the decorated function
- Make sure that, when there's an asset selection, only the checks on selected assets are executed
- Internal asset deps
  - With subselection
- What happens if a multi-check targets multiple assets and only one of those assets is selected to
    run?
- With CachingRepositoryData
- Version tags
- AssetCheckSpec accepts string asset key as well as AssetsDefinition
- @multi_asset
"""

import pytest
from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    Definitions,
    MetadataValue,
    Output,
    asset,
    asset_check,
    execute_in_process,
)


def test_asset_check_decorator():
    @asset_check(asset="asset1", description="desc")
    def check1():
        ...

    assert check1.name == "check1"
    assert check1.description == "desc"
    assert check1.asset_key == AssetKey("asset1")


def test_asset_check_decorator_name():
    @asset_check(asset="asset1", description="desc", name="check1")
    def _check():
        ...

    assert _check.name == "check1"


def test_asset_check_separate_op():
    @asset
    def asset1():
        ...

    @asset_check(asset=asset1, description="desc")
    def check1(context):
        asset_check_spec = context.asset_check_spec
        return AssetCheckResult(
            asset_key=asset_check_spec.asset_key,
            check_name=asset_check_spec.name,
            success=True,
            metadata={"foo": "bar"},
        )

    result = execute_in_process(assets=[asset1], asset_checks=[check1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def execute_check_without_asset():
    @asset_check(asset="asset1", description="desc")
    def check1():
        return AssetCheckResult(success=True)

    result = execute_in_process(asset_checks=[check1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == AssetKey("asset1")
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_check_doesnt_execute_if_asset_fails():
    check_executed = [False]

    @asset
    def asset1():
        raise ValueError()

    @asset_check(asset=asset1)
    def asset1_check(context):
        check_executed[0] = True

    result = execute_in_process(assets=[asset1], asset_checks=[asset1_check], raise_on_error=False)
    assert not result.success

    assert not check_executed[0]


def test_asset_check_same_op():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key=AssetKey("asset1"), description="desc")])
    def asset1():
        yield Output(None)
        yield AssetCheckResult(check_name="check1", success=True, metadata={"foo": "bar"})

    result = execute_in_process(assets=[asset1])
    assert result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.asset_key == asset1.key
    assert check_eval.check_name == "check1"
    assert check_eval.metadata == {"foo": MetadataValue.text("bar")}


def test_unexpected_check_name():
    @asset(check_specs=[AssetCheckSpec("check1", asset_key=AssetKey("asset1"), description="desc")])
    def asset1():
        return AssetCheckResult(check_name="check2", success=True, metadata={"foo": "bar"})

    with pytest.raises(AssertionError):
        execute_in_process(assets=[asset1])


def test_asset_decorator_unexpected_asset_key():
    @asset(check_specs=[AssetCheckSpec("check1", description="desc")])
    def asset1():
        return AssetCheckResult(asset_key=AssetKey("asset2"), check_name="check1", success=True)

    with pytest.raises(AssertionError):
        execute_in_process(assets=[asset1])


def test_check_decorator_unexpected_asset_key():
    @asset_check(asset="asset1", description="desc")
    def asset1_check():
        return AssetCheckResult(asset_key=AssetKey("asset2"), success=True)

    with pytest.raises(AssertionError):
        execute_in_process([asset1_check])


def test_multi_asset_check():
    ...


def test_asset_check_separate_op_downstream_still_executes():
    @asset
    def asset1():
        ...

    @asset_check(asset=asset1)
    def asset1_check(context):
        return AssetCheckResult(success=False)

    @asset(deps=[asset1])
    def asset2():
        ...


def test_asset_check_separate_op_skip_downstream():
    @asset
    def asset1():
        ...

    @asset_check(asset=asset1, severity="AssetCheckSeverity.ERROR")
    def asset1_check(context):
        return context.build_check_result(success=True, metadata={"foo": "bar"})


def test_definitions_conflicting_checks():
    def make_check():
        @asset_check(asset="asset1")
        def check1(context):
            ...

        return check1

    with pytest.raises(AssertionError):
        Definitions(asset_checks=[make_check(), make_check()])


def test_definitions_conflicting_checks_inside_assets():
    @asset(check_specs=[AssetCheckSpec(asset="asset1", name="check1")])
    def asset1():
        ...

    @asset(check_specs=[AssetCheckSpec(asset="asset1", name="check1")])
    def asset2():
        ...

    with pytest.raises(AssertionError):
        Definitions(assets=[asset1, asset2])


def test_definitions_same_name_different_asset():
    def make_check_for_asset(asset_key: str):
        @asset_check(asset=asset_key)
        def check1(context):
            ...

        return check1

    Definitions(asset_checks=[make_check_for_asset("asset1"), make_check_for_asset("asset2")])


def test_definitions_same_asset_different_name():
    def make_check(check_name: str):
        @asset_check(asset="asset1", name=check_name)
        def _check(context):
            ...

        return _check

    Definitions(asset_checks=[make_check("check1"), make_check("check2")])
