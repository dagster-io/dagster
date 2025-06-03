from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent


def only_asset_check_execute_fn(context):
    return AssetCheckResult(passed=True)


def test_parse_asset_check_attributes() -> None:
    component = ExecutableComponent.from_attributes_dict(
        attributes={
            "name": "op_name",
            "execute_fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.only_asset_check_execute_fn",
            "checks": [
                {
                    "asset": "asset",
                    "name": "check_name",
                }
            ],
        }
    )
    assert len(component.checks or []) == 1
    assert component.checks
    assert component.checks[0].name == "check_name"
    assert component.checks[0].asset == "asset"

    assert component.execute_fn(None).passed is True


def asset_and_check_execute_fn(context):
    return MaterializeResult(
        check_results=[AssetCheckResult(passed=True, check_name="check_name")],
    )


def test_execute_asset_with_check() -> None:
    component = ExecutableComponent.from_attributes_dict(
        attributes={
            "name": "op_name",
            "execute_fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.asset_and_check_execute_fn",
            "assets": [
                {
                    "key": "asset",
                }
            ],
            "checks": [
                {
                    "asset": "asset",
                    "name": "check_name",
                }
            ],
        }
    )

    defs = component.build_defs(ComponentLoadContext.for_test())

    assets_def = defs.get_assets_def("asset")
    assert assets_def

    result = materialize([assets_def])
    assert result.success

    asset_check_evaluations = result.get_asset_check_evaluations()
    assert asset_check_evaluations
    assert len(asset_check_evaluations) == 1
    assert asset_check_evaluations[0].check_name == "check_name"
    assert asset_check_evaluations[0].passed is True
