import dagster as dg
from dagster import AutomationCondition
from dagster.components import ComponentLoadContext
from dagster.components.lib.executable_component.script_utils import ScriptSpec


@dg.component_instance
def foo(context: ComponentLoadContext) -> dg.PythonScriptComponent:
    return dg.PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            dg.AssetSpec(
                key="foo_def_py",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )


@dg.component_instance
def bar(context: ComponentLoadContext) -> dg.PythonScriptComponent:
    return dg.PythonScriptComponent(
        execution=ScriptSpec(
            path="cool_script.py",
        ),
        assets=[
            dg.AssetSpec(
                key="bar_def_py",
                automation_condition=AutomationCondition.eager(),
            )
        ],
    )
