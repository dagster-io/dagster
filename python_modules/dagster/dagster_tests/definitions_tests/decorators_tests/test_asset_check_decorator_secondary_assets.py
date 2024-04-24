import re

import pytest
from dagster import (
    AssetCheckResult,
    AssetDep,
    AssetIn,
    DagsterInvalidDefinitionError,
    asset,
    asset_check,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey

from .test_asset_check_decorator import execute_assets_and_checks


@asset
def asset1() -> int:
    return 4


@asset
def asset2() -> int:
    return 5


@asset
def asset3() -> int:
    return 6


def test_additional_deps():
    @asset_check(asset=asset1, additional_deps=[asset2])
    def check1():
        return AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(AssetCheckKey(AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_deps_with_managed_input():
    @asset_check(asset=asset1, additional_deps=[asset2])
    def check1(asset_1):
        assert asset_1 == 4
        return AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(AssetCheckKey(AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_deps_overlap():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check1', asset 'asset1' was passed to `asset` and "
            "`additional_deps`. It can only be passed to one of these parameters."
        ),
    ):

        @asset_check(asset=asset1, additional_deps=[asset1])
        def check1(asset_1):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check2', asset 'asset1' was passed to `asset` and "
            "`additional_deps`. It can only be passed to one of these parameters."
        ),
    ):

        @asset_check(asset=asset1, additional_deps=[asset1])
        def check2():
            pass


def test_additional_ins_overlap():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check1', asset 'asset1' was passed to `asset` and "
            "`additional_ins`. It can only be passed to one of these parameters."
        ),
    ):

        @asset_check(asset=asset1, additional_ins={"asset_1": AssetIn("asset1")})
        def check1(asset_1):
            pass


def test_additional_ins_and_deps_overlap():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("deps value AssetKey(['asset2']) also declared as input/AssetIn"),
    ):

        @asset_check(
            asset=asset1, additional_ins={"asset_2": AssetIn("asset2")}, additional_deps=[asset2]
        )
        def check1(asset_2):
            pass


def test_additional_ins_must_correspond_to_params():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset_check(asset=asset1, additional_ins={"foo": AssetIn("asset2")})
        def check1():
            return AssetCheckResult(passed=True)


def test_additional_ins():
    @asset_check(asset=asset1, additional_ins={"foo": AssetIn("asset2")})
    def check1(asset1, foo):
        assert asset1 == 4
        assert foo == 5
        return AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(AssetCheckKey(AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_ins_primary_asset_not_a_param():
    @asset_check(asset=asset1, additional_ins={"foo": AssetIn("asset2")})
    def check1(foo):
        assert foo == 5
        return AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(AssetCheckKey(AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_ins_and_deps():
    @asset_check(asset=asset1, additional_ins={"foo": AssetIn("asset2")}, additional_deps=[asset3])
    def check1(asset1, foo):
        assert asset1 == 4
        assert foo == 5
        return AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 3
    spec = check1.get_spec_for_check_key(AssetCheckKey(AssetKey(["asset1"]), "check1"))
    assert sorted(spec.additional_deps) == [AssetDep(asset2.key), AssetDep(asset3.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_check_waits_for_additional_deps():
    @asset
    def my_asset():
        pass

    @asset
    def my_fail_asset():
        raise Exception("foobar")

    @asset_check(asset=my_asset, additional_deps=[my_fail_asset])
    def check_with_dep():
        return AssetCheckResult(passed=True)

    @asset_check(asset=my_asset)
    def check_without_dep():
        return AssetCheckResult(passed=True)

    result = execute_assets_and_checks(
        assets=[my_asset, my_fail_asset],
        asset_checks=[check_with_dep, check_without_dep],
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].check_name == "check_without_dep"
