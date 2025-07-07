import dagster as dg
from dagster import AutomationCondition, ComponentLoadContext
from dagster.components.lib.executable_component.script_utils import ScriptSpec


@dg.component_instance
def load(context: ComponentLoadContext) -> dg.PythonScriptComponent:
    return dg.PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            dg.AssetSpec(
                key="cool_script",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )
