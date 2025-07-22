import dagster as dg
from dagster._core.definitions.asset_key import AssetKey
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.testing import copy_code_to_file, scaffold_defs_sandbox


def test_nested_component() -> None:
    with scaffold_defs_sandbox(
        project_name="nested_component_project",
    ) as sandbox:
        component_path = sandbox.scaffold_component_and_update_defs_file(
            component_path="function_component",
            component_cls=FunctionComponent,
            component_body={
                "type": "dagster.FunctionComponent",
                "attributes": {
                    "execution": {
                        "name": "nested_component",
                        "fn": ".function_component.execute.execute_fn",
                    },
                    "assets": [
                        {
                            "key": "asset1",
                        }
                    ],
                },
            },
        )

        def code_to_copy() -> None:
            import dagster as dg

            def execute_fn(context) -> dg.MaterializeResult:
                return dg.MaterializeResult()

        copy_code_to_file(code_to_copy, component_path / "execute.py")

        with sandbox.load_component_and_build_defs_at_path(component_path=component_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.name == "nested_component"
            assert defs.resolve_all_asset_keys() == [AssetKey("asset1")]
