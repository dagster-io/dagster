from dagster import AssetSpec, AutomationCondition
from dagster.components import ComponentLoadContext, component_instance
from dagster.components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScript,
    PipesSubprocessScriptCollectionComponent,
)


@component_instance
def foo(context: ComponentLoadContext) -> PipesSubprocessScriptCollectionComponent:
    return PipesSubprocessScriptCollectionComponent(
        scripts=[
            PipesSubprocessScript(
                path="cool_script.py",
                assets=[
                    AssetSpec(
                        key="foo_def_py",
                        automation_condition=AutomationCondition.eager(),
                    )
                ],
            )
        ]
    )


@component_instance
def bar(context: ComponentLoadContext) -> PipesSubprocessScriptCollectionComponent:
    return PipesSubprocessScriptCollectionComponent(
        scripts=[
            PipesSubprocessScript(
                path="cool_script.py",
                assets=[
                    AssetSpec(
                        key="bar_def_py",
                        automation_condition=AutomationCondition.eager(),
                    )
                ],
            )
        ]
    )
