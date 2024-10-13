from typing import cast

import pytest
from dagster import (
    AssetExecutionContext,
    AssetSelection,
    MaterializeResult,
    asset,
    build_metadata_bounds_checks,
    materialize,
)
from dagster._core.errors import DagsterInvalidDefinitionError


@asset
def my_asset(context: AssetExecutionContext):
    if context.has_tag("my_value"):
        return MaterializeResult(
            metadata={"my_metadata": int(cast(str, context.get_tag("my_value")))}
        )


def test_range():
    checks = build_metadata_bounds_checks(
        assets=[my_asset], metadata_key="my_metadata", min_value=1, max_value=10
    )
    assert len(checks) == 1
    assert len(list(checks[0].check_specs)) == 1
    assert (
        next(iter(checks[0].check_specs)).description
        == "Checks that the latest materialization has metadata value `my_metadata` greater than or equal to 1 and less than or equal to 10"
    )

    for value in [1, 5, 10]:
        result = materialize([my_asset, *checks], tags={"my_value": str(value)})

        check_evals = result.get_asset_check_evaluations()
        assert len(check_evals) == 1
        check_eval = check_evals[0]
        assert check_eval.passed
        assert check_eval.description == f"Value `{value}` is within range"

    result = materialize([my_asset, *checks], tags={"my_value": "0"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `0` is less than 1"

    result = materialize([my_asset, *checks], tags={"my_value": "11"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `11` is greater than 10"


def test_exclusive():
    checks = build_metadata_bounds_checks(
        assets=[my_asset],
        metadata_key="my_metadata",
        min_value=1,
        max_value=10,
        exclusive_min=True,
        exclusive_max=True,
    )
    assert len(checks) == 1
    assert len(list(checks[0].check_specs)) == 1
    assert (
        next(iter(checks[0].check_specs)).description
        == "Checks that the latest materialization has metadata value `my_metadata` greater than 1 and less than 10"
    )

    result = materialize([my_asset, *checks], tags={"my_value": "5"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.passed
    assert check_eval.description == "Value `5` is within range"

    result = materialize([my_asset, *checks], tags={"my_value": "1"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `1` is less than or equal to 1"

    result = materialize([my_asset, *checks], tags={"my_value": "10"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `10` is greater than or equal to 10"


def test_no_metadata():
    checks = build_metadata_bounds_checks(
        assets=[my_asset], metadata_key="my_metadata", min_value=1, max_value=10
    )

    result = materialize(checks, selection=AssetSelection.all_asset_checks())
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Asset has not been materialized"

    result = materialize([my_asset, *checks])
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Metadata key `my_metadata` not found"


def test_not_a_number():
    @asset
    def nan_asset():
        return MaterializeResult(metadata={"my_metadata": "foo"})

    checks = build_metadata_bounds_checks(
        assets=[nan_asset], metadata_key="my_metadata", min_value=1, max_value=10
    )

    result = materialize([nan_asset, *checks])
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `foo` is not a number"


def test_float():
    @asset
    def float_asset():
        return MaterializeResult(metadata={"my_metadata": 1.5})

    checks = build_metadata_bounds_checks(
        assets=[float_asset], metadata_key="my_metadata", min_value=1.0, max_value=10.0
    )

    result = materialize([float_asset, *checks])
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert check_eval.passed
    assert check_eval.description == "Value `1.5` is within range"

    checks = build_metadata_bounds_checks(
        assets=[float_asset], metadata_key="my_metadata", min_value=5.0, max_value=10
    )

    result = materialize([float_asset, *checks])
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 1
    check_eval = check_evals[0]
    assert not check_eval.passed
    assert check_eval.description == "Value `1.5` is less than 5.0"


def test_invalid():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="`min_value` may not be greater than `max_value`"
    ):
        build_metadata_bounds_checks(
            assets=[my_asset], metadata_key="my_metadata", min_value=10, max_value=1
        )


def test_two_assets():
    @asset
    def my_other_asset():
        return MaterializeResult(metadata={"my_metadata": -5})

    checks = build_metadata_bounds_checks(
        assets=[my_asset, my_other_asset], metadata_key="my_metadata", min_value=1, max_value=10
    )
    assert len(checks) == 1
    assert len(list(checks[0].check_specs)) == 2

    result = materialize([my_asset, my_other_asset, *checks], tags={"my_value": "5"})
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    check_evals_by_key = {check_eval.asset_key: check_eval for check_eval in check_evals}
    check_eval = check_evals_by_key[my_asset.key]
    assert check_eval.passed
    assert check_eval.description == "Value `5` is within range"
    check_eval = check_evals_by_key[my_other_asset.key]
    assert not check_eval.passed
    assert check_eval.description == "Value `-5` is less than 1"


def test_name_special_chars() -> None:
    checks = build_metadata_bounds_checks(
        assets=[my_asset], metadata_key="dagster/row_count", min_value=1, max_value=10
    )
    assert len(checks) == 1
    assert len(list(checks[0].check_specs)) == 1
    assert next(iter(checks[0].check_specs)).name == "dagster_row_count_bounds_check"

    checks = build_metadata_bounds_checks(
        assets=[my_asset], metadata_key="my key with spaces", min_value=1, max_value=10
    )
    assert len(checks) == 1
    assert len(list(checks[0].check_specs)) == 1
    assert next(iter(checks[0].check_specs)).name == "my_key_with_spaces_bounds_check"
