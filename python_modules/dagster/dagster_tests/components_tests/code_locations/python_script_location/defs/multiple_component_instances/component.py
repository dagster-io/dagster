from dagster import AssetSpec, AutomationCondition
from dagster.components import ComponentLoadContext, component_instance
from dagster.components.lib.executable_component.python_script_component import (
    PythonScriptComponent,
)
from dagster.components.lib.executable_component.script_utils import ScriptSpec


@component_instance
def foo(context: ComponentLoadContext) -> PythonScriptComponent:
    return PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            AssetSpec(
                key="foo",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )


@component_instance
def bar(context: ComponentLoadContext) -> PythonScriptComponent:
    return PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            AssetSpec(
                key="bar",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )
