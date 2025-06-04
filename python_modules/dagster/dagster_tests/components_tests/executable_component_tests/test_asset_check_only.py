from collections.abc import Mapping
from typing import Any, Optional

from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import MaterializeResult
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster.components.core.tree import ComponentTree
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster_shared import check


def only_asset_execute_fn(context):
    return MaterializeResult()


def only_asset_check_execute_fn(context):
    return AssetCheckResult(passed=True)


def test_parse_asset_check_attributes() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.only_asset_check_execute_fn",
            },
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
    assert component.checks[0].asset_key.to_user_string() == "asset"

    assert isinstance(component.execution, FunctionSpec)
    assert component.execution.fn(None).passed is True


def asset_and_check_execute_fn(context):
    return MaterializeResult(
        check_results=[AssetCheckResult(passed=True, check_name="check_name")],
    )


def test_execute_asset_with_check() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.asset_and_check_execute_fn",
            },
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

    defs = component.build_defs(ComponentTree.for_test().load_context)

    assets_def = defs.get_assets_def("asset")
    assert assets_def

    result = materialize([assets_def])
    assert result.success

    asset_check_evaluations = result.get_asset_check_evaluations()
    assert asset_check_evaluations
    assert len(asset_check_evaluations) == 1
    assert asset_check_evaluations[0].check_name == "check_name"
    assert asset_check_evaluations[0].passed is True


def asset_check_job(
    asset_checks_def: AssetChecksDefinition, resources: Optional[Mapping[str, Any]] = None
) -> JobDefinition:
    job = define_asset_job("job_name", selection=AssetSelection.checks(asset_checks_def))
    return check.inst(
        Definitions(
            asset_checks=[asset_checks_def], jobs=[job], resources=resources
        ).resolve_job_def("job_name"),
        JobDefinition,
    )


def test_standalone_asset_check() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.only_asset_check_execute_fn",
            },
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
    assert isinstance(component.execution, FunctionSpec)
    assert isinstance(component.execution.fn(None), AssetCheckResult)

    defs = component.build_defs(ComponentTree.for_test().load_context)
    assert defs.asset_checks
    asset_checks_def = next(iter(defs.asset_checks))
    assert isinstance(asset_checks_def, AssetChecksDefinition)

    job_def = asset_check_job(asset_checks_def)
    assert isinstance(job_def, JobDefinition)
    result = job_def.execute_in_process()
    assert result.success

    asset_check_evaluations = result.get_asset_check_evaluations()
    assert asset_check_evaluations
    assert len(asset_check_evaluations) == 1
    assert asset_check_evaluations[0].check_name == "check_name"
    assert asset_check_evaluations[0].passed is True


def asset_check_execute_fn_with_resources(context, resource_one: ResourceParam[str]):
    return AssetCheckResult(passed=True, metadata={"resource_one": resource_one})


def test_standalone_asset_check_with_resources() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.asset_check_execute_fn_with_resources",
            },
            "checks": [
                {
                    "asset": "asset",
                    "name": "check_name",
                }
            ],
        }
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)

    asset_checks_def = next(iter(defs.asset_checks or []))
    assert isinstance(asset_checks_def, AssetChecksDefinition)

    job_def = asset_check_job(asset_checks_def, resources={"resource_one": "resource_value"})
    assert isinstance(job_def, JobDefinition)

    result = job_def.execute_in_process()
    assert result.success

    asset_check_evaluations = result.get_asset_check_evaluations()
    assert asset_check_evaluations
    assert len(asset_check_evaluations) == 1
    assert asset_check_evaluations[0].check_name == "check_name"
    assert asset_check_evaluations[0].passed is True
    assert asset_check_evaluations[0].metadata == {
        "resource_one": TextMetadataValue("resource_value")
    }


def test_trivial_properties() -> None:
    component_only_assets = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "description": "op_description",
                "tags": {"op_tag": "op_tag_value"},
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.only_asset_execute_fn",
                "pool": "op_pool",
            },
            "assets": [
                {
                    "key": "asset",
                }
            ],
        }
    )

    assert component_only_assets.build_underlying_assets_def(
        ComponentTree.for_test().load_context
    ).op.tags == {"op_tag": "op_tag_value"}

    component_only_asset_checks = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "description": "op_description",
                "tags": {"op_tag": "op_tag_value"},
                "fn": "dagster_tests.components_tests.executable_component_tests.test_asset_check_only.only_asset_check_execute_fn",
                "pool": "op_pool",
            },
            "checks": [
                {
                    "asset": "asset",
                    "name": "check_name",
                }
            ],
        }
    )

    for component in [component_only_assets, component_only_asset_checks]:
        assert component.build_underlying_assets_def(
            ComponentTree.for_test().load_context
        ).op.tags == {"op_tag": "op_tag_value"}
        assert (
            component.build_underlying_assets_def(
                ComponentTree.for_test().load_context
            ).op.description
            == "op_description"
        )
        assert (
            component.build_underlying_assets_def(ComponentTree.for_test().load_context).op.pool
            == "op_pool"
        )
