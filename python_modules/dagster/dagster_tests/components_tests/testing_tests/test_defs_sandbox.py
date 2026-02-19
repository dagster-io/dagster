import dagster as dg
from dagster._core.definitions.asset_key import AssetKey
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.testing import (
    copy_code_to_file,
    create_defs_folder_sandbox,
    scaffold_defs_sandbox,
)


def test_temp_sandbox() -> None:
    with create_defs_folder_sandbox(
        project_name="nested_component_project",
    ) as sandbox:
        defs_path = sandbox.scaffold_component(
            defs_path="function_component",
            component_cls=FunctionComponent,
            defs_yaml_contents={
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

        copy_code_to_file(code_to_copy, defs_path / "execute.py")

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, dg.FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.name == "nested_component"
            assert defs.resolve_all_asset_keys() == [AssetKey("asset1")]


def test_defs_sandbox_legacy() -> None:
    with scaffold_defs_sandbox(
        component_cls=FunctionComponent,
        component_path="parent_folder/nested_component",
        project_name="nested_component_project",
    ) as sandbox:

        def code_to_copy() -> None:
            import dagster as dg

            def execute_fn(context) -> dg.MaterializeResult:
                return dg.MaterializeResult()

        copy_code_to_file(code_to_copy, sandbox.defs_folder_path / "execute.py")

        with sandbox.load(
            component_body={
                "type": "dagster.FunctionComponent",
                "attributes": {
                    "execution": {
                        "name": "nested_component",
                        "fn": ".execute.execute_fn",
                    },
                    "assets": [
                        {
                            "key": "asset1",
                        }
                    ],
                },
            },
        ) as (component, _defs):
            assert isinstance(component, dg.FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.name == "nested_component"
