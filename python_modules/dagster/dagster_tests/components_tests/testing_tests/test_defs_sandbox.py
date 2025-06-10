from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.testing import copy_code_to_file, scaffold_defs_sandbox


def test_nested_component() -> None:
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
                "type": "dagster.components.lib.executable_component.function_component.FunctionComponent",
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
        ) as (component, defs):
            assert isinstance(component, FunctionComponent)
            assert isinstance(component.execution, FunctionSpec)
            assert component.execution.name == "nested_component"
