import re

import dagster as dg
import pytest

from dagster_tests.definitions_tests.decorators_tests.test_asset_check_decorator import (
    execute_assets_and_checks,
)


@dg.asset
def asset1() -> int:
    return 4


@dg.asset
def asset2() -> int:
    return 5


@dg.asset
def asset3() -> int:
    return 6


def test_additional_deps():
    @dg.asset_check(asset=asset1, additional_deps=[asset2])
    def check1():
        return dg.AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [dg.AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_deps_with_managed_input():
    @dg.asset_check(asset=asset1, additional_deps=[asset2])
    def check1(asset_1):
        assert asset_1 == 4
        return dg.AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [dg.AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_deps_overlap():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check1', asset 'asset1' was passed to `asset` and "
            "`additional_deps`. It can only be passed to one of these parameters."
        ),
    ):

        @dg.asset_check(asset=asset1, additional_deps=[asset1])  # pyright: ignore[reportArgumentType]
        def check1(asset_1):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check2', asset 'asset1' was passed to `asset` and "
            "`additional_deps`. It can only be passed to one of these parameters."
        ),
    ):

        @dg.asset_check(asset=asset1, additional_deps=[asset1])  # pyright: ignore[reportArgumentType]
        def check2():
            pass


def test_additional_ins_overlap():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "When defining check 'check1', asset 'asset1' was passed to `asset` and "
            "`additional_ins`. It can only be passed to one of these parameters."
        ),
    ):

        @dg.asset_check(asset=asset1, additional_ins={"asset_1": dg.AssetIn("asset1")})  # pyright: ignore[reportArgumentType]
        def check1(asset_1):
            pass


def test_additional_ins_and_deps_overlap():
    @dg.asset_check(
        asset=asset1,
        additional_ins={"asset_2": dg.AssetIn("asset2")},
        additional_deps=[asset2],
    )
    def check1(asset_2) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=asset_2 == 5)

    result = execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])
    assert result.success
    assert len(result.get_asset_check_evaluations()) == 1
    assert all(e.passed for e in result.get_asset_check_evaluations())


def test_additional_ins_must_correspond_to_params():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset_check(asset=asset1, additional_ins={"foo": dg.AssetIn("asset2")})
        def check1():
            return dg.AssetCheckResult(passed=True)


def test_additional_ins():
    @dg.asset_check(asset=asset1, additional_ins={"foo": dg.AssetIn("asset2")})
    def check1(asset1, foo):
        assert asset1 == 4
        assert foo == 5
        return dg.AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [dg.AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_ins_primary_asset_not_a_param():
    @dg.asset_check(asset=asset1, additional_ins={"foo": dg.AssetIn("asset2")})
    def check1(foo):
        assert foo == 5
        return dg.AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 2
    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert spec.additional_deps == [dg.AssetDep(asset2.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_additional_ins_and_deps():
    @dg.asset_check(
        asset=asset1, additional_ins={"foo": dg.AssetIn("asset2")}, additional_deps=[asset3]
    )
    def check1(asset1, foo):
        assert asset1 == 4
        assert foo == 5
        return dg.AssetCheckResult(passed=True)

    assert len(check1.node_def.input_defs) == 3
    spec = check1.get_spec_for_check_key(dg.AssetCheckKey(dg.AssetKey(["asset1"]), "check1"))
    assert sorted(spec.additional_deps) == [dg.AssetDep(asset2.key), dg.AssetDep(asset3.key)]

    execute_assets_and_checks(assets=[asset1, asset2], asset_checks=[check1])


def test_check_waits_for_additional_deps():
    @dg.asset
    def my_asset():
        pass

    @dg.asset
    def my_fail_asset():
        raise Exception("foobar")

    @dg.asset_check(asset=my_asset, additional_deps=[my_fail_asset])
    def check_with_dep():
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=my_asset)
    def check_without_dep():
        return dg.AssetCheckResult(passed=True)

    result = execute_assets_and_checks(
        assets=[my_asset, my_fail_asset],
        asset_checks=[check_with_dep, check_without_dep],
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].check_name == "check_without_dep"
