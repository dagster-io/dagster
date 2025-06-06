from dagster import AssetSpec, AutomationCondition, ComponentLoadContext, component_instance
from dagster.components.lib.executable_component.python_script_component import (
    PythonScriptComponent,
)
from dagster.components.lib.executable_component.script_utils import ScriptSpec


@component_instance
def load(context: ComponentLoadContext) -> PythonScriptComponent:
    return PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            AssetSpec(
                key="cool_script",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )
