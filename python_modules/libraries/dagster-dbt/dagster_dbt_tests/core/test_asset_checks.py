import os
from typing import Any, Callable, Dict, List, Optional

import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    ExecuteInProcessResult,
    materialize,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings

from ..dbt_projects import test_asset_checks_path

dagster_dbt_translator_with_checks = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
)


@pytest.fixture(params=[[["build"]], [["seed"], ["run"], ["test"]]], ids=["build", "seed-run-test"])
def dbt_commands(request):
    return request.param


def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@pytest.mark.parametrize(
    "assets_def_fn",
    [
        lambda manifest: load_assets_from_dbt_manifest(manifest=manifest)[0],
        lambda manifest: dbt_assets(manifest=manifest)(my_dbt_assets),
    ],
    ids=["load_assets_from_dbt_manifest", "@dbt_assets"],
)
def test_without_asset_checks(
    test_asset_checks_manifest: Dict[str, Any],
    assets_def_fn: Callable[[Dict[str, Any]], AssetsDefinition],
) -> None:
    assets_def = assets_def_fn(test_asset_checks_manifest)

    # dbt tests are present, but are not modeled as Dagster asset checks
    assert any(
        unique_id.startswith("test") for unique_id in test_asset_checks_manifest["nodes"].keys()
    )
    assert not assets_def.check_specs_by_output_name

    result = materialize(
        [assets_def],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_asset_checks_path))},
        raise_on_error=False,
    )

    assert result.get_asset_observation_events()
    assert not result.get_asset_check_evaluations()


@pytest.mark.parametrize(
    "assets_def_fn",
    [
        pytest.param(
            lambda manifest: load_assets_from_dbt_manifest(
                manifest=manifest,
                dagster_dbt_translator=dagster_dbt_translator_with_checks,
            )[0],
            marks=pytest.mark.xfail(
                reason="load_assets_from_dbt_manifest is not passing down the translator properly."
            ),
        ),
        lambda manifest: dbt_assets(
            manifest=manifest, dagster_dbt_translator=dagster_dbt_translator_with_checks
        )(my_dbt_assets),
    ],
    ids=["load_assets_from_dbt_manifest", "@dbt_assets"],
)
def test_with_asset_checks(
    test_asset_checks_manifest: Dict[str, Any],
    assets_def_fn: Callable[[Dict[str, Any]], AssetsDefinition],
) -> None:
    # dbt tests are present, and are modeled as Dagster asset checks
    assets_def = assets_def_fn(test_asset_checks_manifest)

    assert any(
        unique_id.startswith("test") for unique_id in test_asset_checks_manifest["nodes"].keys()
    )
    assert assets_def.check_specs_by_output_name

    assert assets_def.check_specs_by_output_name == {
        "customers_not_null_customers_customer_id": AssetCheckSpec(
            name="not_null_customers_customer_id",
            asset=AssetKey(["customers"]),
        ),
        "customers_unique_customers_customer_id": AssetCheckSpec(
            name="unique_customers_customer_id",
            asset=AssetKey(["customers"]),
        ),
        "orders_accepted_values_orders_status__placed__shipped__completed__return_pending__returned": AssetCheckSpec(
            name="accepted_values_orders_status__placed__shipped__completed__return_pending__returned",
            asset=AssetKey(["orders"]),
            description="Status must be one of ['placed', 'shipped', 'completed', 'return_pending', or 'returned']",
        ),
        "orders_not_null_orders_amount": AssetCheckSpec(
            name="not_null_orders_amount",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_bank_transfer_amount": AssetCheckSpec(
            name="not_null_orders_bank_transfer_amount",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_coupon_amount": AssetCheckSpec(
            name="not_null_orders_coupon_amount",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_credit_card_amount": AssetCheckSpec(
            name="not_null_orders_credit_card_amount",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_customer_id": AssetCheckSpec(
            name="not_null_orders_customer_id",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_gift_card_amount": AssetCheckSpec(
            name="not_null_orders_gift_card_amount",
            asset=AssetKey(["orders"]),
        ),
        "orders_not_null_orders_order_id": AssetCheckSpec(
            name="not_null_orders_order_id",
            asset=AssetKey(["orders"]),
        ),
        "orders_relationships_orders_customer_id__customer_id__ref_customers_": AssetCheckSpec(
            name="relationships_orders_customer_id__customer_id__ref_customers_",
            asset=AssetKey(["orders"]),
            additional_deps=[
                AssetKey(["customers"]),
            ],
        ),
        "orders_relationships_orders_customer_id__customer_id__source_jaffle_shop_raw_customers_": AssetCheckSpec(
            name="relationships_orders_customer_id__customer_id__source_jaffle_shop_raw_customers_",
            asset=AssetKey(["orders"]),
            additional_deps=[
                AssetKey(["jaffle_shop", "raw_customers"]),
            ],
        ),
        "orders_relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_": AssetCheckSpec(
            name="relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_",
            asset=AssetKey(["orders"]),
            additional_deps=[
                AssetKey(["customers"]),
            ],
        ),
        "orders_unique_orders_order_id": AssetCheckSpec(
            name="unique_orders_order_id",
            asset=AssetKey(["orders"]),
        ),
        "stg_customers_not_null_stg_customers_customer_id": AssetCheckSpec(
            name="not_null_stg_customers_customer_id",
            asset=AssetKey(["stg_customers"]),
        ),
        "stg_customers_unique_stg_customers_customer_id": AssetCheckSpec(
            name="unique_stg_customers_customer_id",
            asset=AssetKey(["stg_customers"]),
        ),
        "stg_orders_accepted_values_stg_orders_status__placed__shipped__completed__return_pending__returned": AssetCheckSpec(
            name="accepted_values_stg_orders_status__placed__shipped__completed__return_pending__returned",
            asset=AssetKey(["stg_orders"]),
        ),
        "stg_orders_not_null_stg_orders_order_id": AssetCheckSpec(
            name="not_null_stg_orders_order_id",
            asset=AssetKey(["stg_orders"]),
        ),
        "stg_orders_unique_stg_orders_order_id": AssetCheckSpec(
            name="unique_stg_orders_order_id",
            asset=AssetKey(["stg_orders"]),
        ),
        "stg_payments_accepted_values_stg_payments_payment_method__credit_card__coupon__bank_transfer__gift_card": AssetCheckSpec(
            name="accepted_values_stg_payments_payment_method__credit_card__coupon__bank_transfer__gift_card",
            asset=AssetKey(["stg_payments"]),
        ),
        "stg_payments_not_null_stg_payments_payment_id": AssetCheckSpec(
            name="not_null_stg_payments_payment_id",
            asset=AssetKey(["stg_payments"]),
        ),
        "stg_payments_unique_stg_payments_payment_id": AssetCheckSpec(
            name="unique_stg_payments_payment_id",
            asset=AssetKey(["stg_payments"]),
        ),
        "fail_tests_model_accepted_values_fail_tests_model_first_name__foo__bar__baz": AssetCheckSpec(
            name="accepted_values_fail_tests_model_first_name__foo__bar__baz",
            asset=AssetKey(["fail_tests_model"]),
        ),
        "fail_tests_model_unique_fail_tests_model_id": AssetCheckSpec(
            name="unique_fail_tests_model_id",
            asset=AssetKey(["fail_tests_model"]),
        ),
        "customers_singular_test_with_single_dependency": AssetCheckSpec(
            name="singular_test_with_single_dependency",
            asset=AssetKey(["customers"]),
        ),
        "customers_singular_test_with_meta_and_multiple_dependencies": AssetCheckSpec(
            name="singular_test_with_meta_and_multiple_dependencies",
            asset=AssetKey(["customers"]),
            additional_deps=[
                AssetKey(["orders"]),
            ],
        ),
    }

    result = materialize(
        [assets_def],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_asset_checks_path))},
        raise_on_error=False,
    )

    assert result.get_asset_observation_events()
    assert result.get_asset_check_evaluations()


def test_enable_asset_checks_with_custom_translator() -> None:
    class CustomDagsterDbtTranslatorWithInitNoSuper(DagsterDbtTranslator):
        def __init__(self, test_arg: str):
            self.test_arg = test_arg

    class CustomDagsterDbtTranslatorWithInitWithSuper(DagsterDbtTranslator):
        def __init__(self, test_arg: str):
            self.test_arg = test_arg

            super().__init__()

    class CustomDagsterDbtTranslator(DagsterDbtTranslator): ...

    class CustomDagsterDbtTranslatorWithPassThrough(DagsterDbtTranslator):
        def __init__(self, test_arg: str, *args, **kwargs):
            self.test_arg = test_arg

            super().__init__(*args, **kwargs)

    no_pass_through_no_super_translator = CustomDagsterDbtTranslatorWithInitNoSuper("test")
    assert not no_pass_through_no_super_translator.settings.enable_asset_checks

    no_pass_through_with_super_translator = CustomDagsterDbtTranslatorWithInitWithSuper("test")
    assert not no_pass_through_with_super_translator.settings.enable_asset_checks

    custom_translator = CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
    )
    assert custom_translator.settings.enable_asset_checks

    pass_through_translator = CustomDagsterDbtTranslatorWithPassThrough(
        "test",
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=True),
    )
    assert pass_through_translator.settings.enable_asset_checks


def _materialize_dbt_assets(
    manifest: Dict[str, Any],
    dbt_commands: List[List[str]],
    selection: Optional[AssetSelection],
) -> ExecuteInProcessResult:
    @dbt_assets(manifest=manifest, dagster_dbt_translator=dagster_dbt_translator_with_checks)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        for dbt_command in dbt_commands:
            yield from dbt.cli(dbt_command, context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_asset_checks_path))},
        selection=selection,
        raise_on_error=False,
    )

    return result


def test_materialize_no_selection(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]]
) -> None:
    result = _materialize_dbt_assets(
        test_asset_checks_manifest,
        dbt_commands,
        selection=None,
    )
    assert not result.success  # fail_tests_model fails
    assert len(result.get_asset_materialization_events()) == 10
    assert len(result.get_asset_check_evaluations()) == 26
    assert len(result.get_asset_observation_events()) == 2


def test_materialize_asset_and_checks(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]]
) -> None:
    result = _materialize_dbt_assets(
        test_asset_checks_manifest,
        dbt_commands,
        selection=AssetSelection.keys(AssetKey(["customers"])),
    )
    assert result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 4
    assert len(result.get_asset_observation_events()) == 6
    # no tests were excluded, so we include singular and relationship tests
    assert {
        (e.asset_key, e.asset_observation_data.asset_observation.metadata.get("unique_id").value)  # type: ignore[attr-defined]
        for e in result.get_asset_observation_events()
    } == {
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_.d9e47ca78e",
        ),
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.relationships_orders_customer_id__customer_id__ref_customers_.c6ec7f58f2",
        ),
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.singular_test_with_no_meta_and_multiple_dependencies",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_.d9e47ca78e",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.relationships_orders_customer_id__customer_id__ref_customers_.c6ec7f58f2",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.singular_test_with_no_meta_and_multiple_dependencies",
        ),
    }


def test_materialize_asset_no_checks(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]]
) -> None:
    result = _materialize_dbt_assets(
        test_asset_checks_manifest,
        dbt_commands,
        selection=AssetSelection.keys(AssetKey(["customers"])).without_checks(),
    )
    assert result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 0
    # since checks are exclued, we don't run the singular or relationship tests
    assert len(result.get_asset_observation_events()) == 0


def test_materialize_checks_no_asset(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]]
) -> None:
    result = _materialize_dbt_assets(
        test_asset_checks_manifest,
        dbt_commands,
        selection=(
            AssetSelection.keys(AssetKey(["customers"]))
            - AssetSelection.keys(AssetKey(["customers"])).without_checks()
        ),
    )
    assert result.success
    assert len(result.get_asset_materialization_events()) == 0
    assert len(result.get_asset_check_evaluations()) == 4
    # since we're not materializing the asset, we can't use indirect selection and therefore
    # don't run the singular or relationship tests
    assert len(result.get_asset_observation_events()) == 0


def test_asset_checks_results(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]]
):
    @dbt_assets(
        manifest=test_asset_checks_manifest,
        dagster_dbt_translator=dagster_dbt_translator_with_checks,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        events = []
        invocation_id = ""
        for dbt_command in dbt_commands:
            dbt_invocation = dbt.cli(dbt_command, context=context, raise_on_error=False)
            events += list(dbt_invocation.stream())
            invocation_id = dbt_invocation.get_artifact("run_results.json")["metadata"][
                "invocation_id"
            ]

        expected_results = [
            AssetCheckResult(
                passed=True,
                asset_key=AssetKey(["customers"]),
                check_name="unique_customers_customer_id",
                metadata={
                    "unique_id": (
                        "test.test_dagster_asset_checks.unique_customers_customer_id.c5af1ff4b1"
                    ),
                    "invocation_id": invocation_id,
                    "status": "pass",
                },
            ),
            AssetCheckResult(
                passed=True,
                asset_key=AssetKey(["customers"]),
                check_name="not_null_customers_customer_id",
                metadata={
                    "unique_id": (
                        "test.test_dagster_asset_checks.not_null_customers_customer_id.5c9bf9911d"
                    ),
                    "invocation_id": invocation_id,
                    "status": "pass",
                },
            ),
            AssetCheckResult(
                passed=False,
                asset_key=AssetKey(["fail_tests_model"]),
                check_name="unique_fail_tests_model_id",
                severity=AssetCheckSeverity.WARN,
                metadata={
                    "unique_id": (
                        "test.test_dagster_asset_checks.unique_fail_tests_model_id.1619308eb1"
                    ),
                    "invocation_id": invocation_id,
                    "status": "warn",
                },
            ),
            AssetCheckResult(
                passed=False,
                asset_key=AssetKey(["fail_tests_model"]),
                check_name="accepted_values_fail_tests_model_first_name__foo__bar__baz",
                severity=AssetCheckSeverity.ERROR,
                metadata={
                    "unique_id": (
                        "test.test_dagster_asset_checks.accepted_values_fail_tests_model_first_name__foo__bar__baz.5f958cf018"
                    ),
                    "invocation_id": invocation_id,
                    "status": "fail",
                },
            ),
        ]

        for expected_asset_check_result in expected_results:
            assert expected_asset_check_result in events

        yield from events

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_asset_checks_path))},
    )
    assert result.success


@pytest.mark.parametrize(
    "selection",
    ["customers", "tag:customer_info"],
)
def test_select_model_with_tests(
    test_asset_checks_manifest: Dict[str, Any], dbt_commands: List[List[str]], selection: str
):
    @dbt_assets(
        manifest=test_asset_checks_manifest,
        dagster_dbt_translator=dagster_dbt_translator_with_checks,
        select=selection,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        for dbt_command in dbt_commands:
            yield from dbt.cli(dbt_command, context=context).stream()

    assert my_dbt_assets.keys == {AssetKey(["customers"])}
    assert my_dbt_assets.check_keys == {
        AssetCheckKey(asset_key=AssetKey(["customers"]), name="unique_customers_customer_id"),
        AssetCheckKey(asset_key=AssetKey(["customers"]), name="not_null_customers_customer_id"),
        AssetCheckKey(
            asset_key=AssetKey(["customers"]), name="singular_test_with_single_dependency"
        ),
        AssetCheckKey(
            asset_key=AssetKey(["customers"]),
            name="singular_test_with_meta_and_multiple_dependencies",
        ),
    }

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_asset_checks_path))},
    )

    assert result.success
    assert len(result.get_asset_materialization_events()) == 1
    assert len(result.get_asset_check_evaluations()) == 4
    # no tests were excluded, so we include singular and relationship tests
    assert len(result.get_asset_observation_events()) == 6
    assert {
        (e.asset_key, e.asset_observation_data.asset_observation.metadata.get("unique_id").value)  # type: ignore[attr-defined]
        for e in result.get_asset_observation_events()
    } == {
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_.d9e47ca78e",
        ),
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.relationships_orders_customer_id__customer_id__ref_customers_.c6ec7f58f2",
        ),
        (
            AssetKey(["customers"]),
            "test.test_dagster_asset_checks.singular_test_with_no_meta_and_multiple_dependencies",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.relationships_with_duplicate_orders_ref_customers___customer_id__customer_id__ref_customers_.d9e47ca78e",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.relationships_orders_customer_id__customer_id__ref_customers_.c6ec7f58f2",
        ),
        (
            AssetKey(["orders"]),
            "test.test_dagster_asset_checks.singular_test_with_no_meta_and_multiple_dependencies",
        ),
    }
