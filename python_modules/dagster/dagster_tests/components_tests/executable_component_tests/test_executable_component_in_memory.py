from collections.abc import Mapping
from typing import Any, Optional

from dagster._config.pythonic_config.config import Config
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import MaterializeResult
from dagster.components.core.tree import ComponentTree
from dagster.components.lib.executable_component.component import ExecutableComponent
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.testing import copy_code_to_file, scaffold_defs_sandbox


def asset_in_component(
    component: ExecutableComponent, key: CoercibleToAssetKey
) -> AssetsDefinition:
    defs = component.build_defs(ComponentTree.for_test().load_context)
    return defs.get_assets_def(key)


def test_include() -> None:
    assert FunctionComponent


def test_basic_singular_asset() -> None:
    def _execute_fn(context) -> MaterializeResult:
        return MaterializeResult(metadata={"foo": "bar"})

    component = FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=_execute_fn),
        assets=[AssetSpec(key="asset")],
    )

    assert isinstance(component, FunctionComponent)
    assert_singular_component(component)


def test_basic_singular_asset_with_callable() -> None:
    def op_name(context) -> MaterializeResult:
        return MaterializeResult(metadata={"foo": "bar"})

    component = FunctionComponent(execution=op_name, assets=[AssetSpec(key="asset")])

    assert isinstance(component, FunctionComponent)
    assert_singular_component(component)


def assert_singular_component(
    component: FunctionComponent,
    resources: Optional[Mapping[str, Any]] = None,
    run_config: Optional[Mapping[str, Any]] = None,
) -> None:
    defs = component.build_defs(ComponentTree.for_test().load_context)
    assets_def = defs.get_assets_def("asset")

    assert assets_def.op.name == "op_name"
    assert assets_def.key.to_user_string() == "asset"

    result = materialize([assets_def], resources=resources, run_config=run_config)
    assert result.success
    mats = result.asset_materializations_for_node("op_name")
    assert len(mats) == 1
    assert mats[0].metadata == {"foo": TextMetadataValue("bar")}


def execute_singular_asset(context) -> MaterializeResult:
    return MaterializeResult(metadata={"foo": "bar"})


def op_name(context) -> MaterializeResult:
    return MaterializeResult(metadata={"foo": "bar"})


def test_basic_singular_asset_from_yaml() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_executable_component_in_memory.execute_singular_asset",
            },
            "assets": [
                {
                    "key": "asset",
                }
            ],
        }
    )
    assert isinstance(component, FunctionComponent)
    assert_singular_component(component)


def execute_singular_asset_with_resource(
    context, a_resource: ResourceParam[str]
) -> MaterializeResult:
    return MaterializeResult(metadata={"foo": "bar"})


def test_basic_singular_asset_with_resource_from_yaml() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_executable_component_in_memory.execute_singular_asset_with_resource",
            },
            "assets": [
                {
                    "key": "asset",
                }
            ],
        }
    )
    assert isinstance(component, FunctionComponent)
    assert_singular_component(component, resources={"a_resource": "a_value"})


def test_basic_singular_asset_from_callable() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": "dagster_tests.components_tests.executable_component_tests.test_executable_component_in_memory.op_name",
            "assets": [
                {
                    "key": "asset",
                }
            ],
        }
    )
    assert isinstance(component, FunctionComponent)
    assert_singular_component(component)


class MyConfig(Config):
    config_value: str


def execute_fn_with_config(context, config: MyConfig):
    return MaterializeResult(metadata={"config_value": config.config_value})


def test_singular_asset_with_config() -> None:
    component = FunctionComponent.from_attributes_dict(
        attributes={
            "execution": {
                "name": "op_name",
                "fn": "dagster_tests.components_tests.executable_component_tests.test_executable_component_in_memory.execute_fn_with_config",
            },
            "assets": [
                {
                    "key": "asset",
                },
            ],
        }
    )

    assert isinstance(component, FunctionComponent)
    assets_def = asset_in_component(component, "asset")
    result = materialize(
        [assets_def], run_config={"ops": {"op_name": {"config": {"config_value": "bar"}}}}
    )
    assert result.success


def test_resource_usage() -> None:
    def _execute_fn(context, some_resource: ResourceParam[str]) -> MaterializeResult:
        return MaterializeResult(metadata={"foo": some_resource})

    component = FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=_execute_fn),
        assets=[AssetSpec(key="asset")],
    )

    assets_def = asset_in_component(component, "asset")

    result = materialize([assets_def], resources={"some_resource": "some_value"})
    assert result.success
    mats = result.asset_materializations_for_node("op_name")
    assert len(mats) == 1
    assert mats[0].metadata == {"foo": TextMetadataValue("some_value")}


def test_local_import() -> None:
    def code_to_copy():
        def execute_fn_to_copy(context):
            from dagster import MaterializeResult

            return MaterializeResult(metadata={"foo": "bar"})

    with scaffold_defs_sandbox(component_cls=FunctionComponent) as sandbox:
        execute_path = sandbox.defs_folder_path / "execute.py"
        copy_code_to_file(code_to_copy, execute_path)

        with sandbox.load(
            component_body={
                "type": "dagster.components.lib.executable_component.function_component.FunctionComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name",
                        "fn": ".execute.execute_fn_to_copy",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            }
        ) as (component, defs):
            assert isinstance(component, FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.fn.__name__ == "execute_fn_to_copy"
            assert isinstance(component.execution.fn(None), MaterializeResult)

            assets_def = defs.get_assets_def("asset")
            assert assets_def.op.name == "op_name"
            assert assets_def.key.to_user_string() == "asset"

            result = materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert mats[0].metadata == {"foo": TextMetadataValue("bar")}


def test_asset_with_config() -> None:
    class MyConfig(Config):
        foo: str

    def execute_fn(context, config: MyConfig) -> MaterializeResult:
        return MaterializeResult(metadata={"foo": config.foo})

    component = FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=execute_fn),
        assets=[AssetSpec(key="asset")],
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)
    assert defs.get_assets_def("asset").op.config_schema

    assert_singular_component(
        component, run_config={"ops": {"op_name": {"config": {"foo": "bar"}}}}
    )


def test_asset_check_with_config() -> None:
    class MyConfig(Config):
        foo: str

    def execute_fn(context, config: MyConfig) -> AssetCheckResult:
        return AssetCheckResult(
            passed=True,
            metadata={"foo": config.foo},
        )

    component = FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=execute_fn),
        checks=[AssetCheckSpec(name="asset_check", asset="asset")],
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)
    checks_def = defs.get_asset_checks_def(
        AssetCheckKey(asset_key=AssetKey("asset"), name="asset_check")
    )
    defs = Definitions(asset_checks=[checks_def])
    result = materialize(
        [checks_def],
        run_config={"ops": {"op_name": {"config": {"foo": "bar"}}}},
        selection=AssetSelection.all_asset_checks(),
    )
    assert result.success
    assert checks_def.op.config_schema

    aces = result.get_asset_check_evaluations()
    assert len(aces) == 1
    assert aces[0].check_name == "asset_check"
    assert aces[0].asset_key == AssetKey("asset")
    assert aces[0].passed
    assert aces[0].metadata == {"foo": TextMetadataValue("bar")}
