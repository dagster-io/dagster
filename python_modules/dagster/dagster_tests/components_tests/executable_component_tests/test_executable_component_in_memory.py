from collections.abc import Mapping
from typing import Any, Optional

import dagster as dg
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster.components.core.component_tree import ComponentTree
from dagster.components.lib.executable_component.component import ExecutableComponent
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.testing import copy_code_to_file, create_defs_folder_sandbox


def asset_in_component(
    component: ExecutableComponent, key: CoercibleToAssetKey
) -> dg.AssetsDefinition:
    defs = component.build_defs(ComponentTree.for_test().load_context)
    return defs.get_assets_def(key)


def test_include() -> None:
    assert dg.FunctionComponent


def test_basic_singular_asset() -> None:
    def _execute_fn(context) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": "bar"})

    component = dg.FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=_execute_fn),
        assets=[dg.AssetSpec(key="asset")],
    )

    assert isinstance(component, dg.FunctionComponent)
    assert_singular_component(component)


def test_basic_singular_asset_with_callable() -> None:
    def op_name(context) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": "bar"})

    component = dg.FunctionComponent(execution=op_name, assets=[dg.AssetSpec(key="asset")])

    assert isinstance(component, dg.FunctionComponent)
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

    result = dg.materialize([assets_def], resources=resources, run_config=run_config)
    assert result.success
    mats = result.asset_materializations_for_node("op_name")
    assert len(mats) == 1
    assert mats[0].metadata == {"foo": dg.TextMetadataValue("bar")}


def execute_singular_asset(context) -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata={"foo": "bar"})


def op_name(context) -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata={"foo": "bar"})


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
    assert isinstance(component, dg.FunctionComponent)
    assert_singular_component(component)


def execute_singular_asset_with_resource(
    context, a_resource: dg.ResourceParam[str]
) -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata={"foo": "bar"})


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
    assert isinstance(component, dg.FunctionComponent)
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
    assert isinstance(component, dg.FunctionComponent)
    assert_singular_component(component)


class MyConfig(dg.Config):
    config_value: str


def execute_fn_with_config(context, config: MyConfig):
    return dg.MaterializeResult(metadata={"config_value": config.config_value})


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

    assert isinstance(component, dg.FunctionComponent)
    assets_def = asset_in_component(component, "asset")
    result = dg.materialize(
        [assets_def], run_config={"ops": {"op_name": {"config": {"config_value": "bar"}}}}
    )
    assert result.success


def test_resource_usage() -> None:
    def _execute_fn(context, some_resource: dg.ResourceParam[str]) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": some_resource})

    component = dg.FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=_execute_fn),
        assets=[dg.AssetSpec(key="asset")],
    )

    assets_def = asset_in_component(component, "asset")

    result = dg.materialize([assets_def], resources={"some_resource": "some_value"})
    assert result.success
    mats = result.asset_materializations_for_node("op_name")
    assert len(mats) == 1
    assert mats[0].metadata == {"foo": dg.TextMetadataValue("some_value")}


def test_local_import() -> None:
    def code_to_copy():
        import dagster as dg

        def execute_fn_to_copy(context):
            return dg.MaterializeResult(metadata={"foo": "bar"})

    with create_defs_folder_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(
            component_cls=FunctionComponent,
            defs_path="function_component",
            defs_yaml_contents={
                "type": "dagster.FunctionComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name",
                        "fn": ".function_component.execute.execute_fn_to_copy",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            },
        )
        execute_path = component_path / "execute.py"
        copy_code_to_file(code_to_copy, execute_path)

        with sandbox.load_component_and_build_defs(defs_path=component_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.fn.__name__ == "execute_fn_to_copy"
            assert isinstance(component.execution.fn(None), dg.MaterializeResult)

            assets_def = defs.get_assets_def("asset")
            assert assets_def.op.name == "op_name"
            assert assets_def.key.to_user_string() == "asset"

            result = dg.materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
            assert mats[0].metadata == {"foo": dg.TextMetadataValue("bar")}


def test_asset_with_config() -> None:
    class MyConfig(dg.Config):
        foo: str

    def execute_fn(context, config: MyConfig) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": config.foo})

    component = dg.FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=execute_fn),
        assets=[dg.AssetSpec(key="asset")],
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)
    assert defs.get_assets_def("asset").op.config_schema

    assert_singular_component(
        component, run_config={"ops": {"op_name": {"config": {"foo": "bar"}}}}
    )


def test_asset_with_config_in_spec() -> None:
    class MyConfig(dg.Config):
        foo: str

    def execute_fn(context) -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"foo": context.op_execution_context.op_config["foo"]})

    component = dg.FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=execute_fn, config_schema=MyConfig),
        assets=[dg.AssetSpec(key="asset")],
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)
    assert defs.get_assets_def("asset").op.config_schema

    assert_singular_component(
        component, run_config={"ops": {"op_name": {"config": {"foo": "bar"}}}}
    )


def test_asset_check_with_config() -> None:
    class MyConfig(dg.Config):
        foo: str

    def execute_fn(context, config: MyConfig) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            passed=True,
            metadata={"foo": config.foo},
        )

    component = dg.FunctionComponent(
        execution=FunctionSpec(name="op_name", fn=execute_fn),
        checks=[dg.AssetCheckSpec(name="asset_check", asset="asset")],
    )

    defs = component.build_defs(ComponentTree.for_test().load_context)
    checks_def = defs.get_asset_checks_def(
        dg.AssetCheckKey(asset_key=dg.AssetKey("asset"), name="asset_check")
    )
    defs = dg.Definitions(asset_checks=[checks_def])
    result = dg.materialize(
        [checks_def],
        run_config={"ops": {"op_name": {"config": {"foo": "bar"}}}},
        selection=AssetSelection.all_asset_checks(),
    )
    assert result.success
    assert checks_def.op.config_schema

    aces = result.get_asset_check_evaluations()
    assert len(aces) == 1
    assert aces[0].check_name == "asset_check"
    assert aces[0].asset_key == dg.AssetKey("asset")
    assert aces[0].passed
    assert aces[0].metadata == {"foo": dg.TextMetadataValue("bar")}
