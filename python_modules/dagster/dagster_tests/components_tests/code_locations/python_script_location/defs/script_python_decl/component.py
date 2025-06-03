from dagster import AssetSpec, AutomationCondition, ComponentLoadContext, component_instance
from dagster.components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScript,
    PipesSubprocessScriptCollectionComponent,
)


@component_instance
def load(context: ComponentLoadContext) -> PipesSubprocessScriptCollectionComponent:
    return PipesSubprocessScriptCollectionComponent(
        scripts=[
            PipesSubprocessScript(
                path="cool_script.py",
                assets=[
                    AssetSpec(
                        key="cool_script",
                        automation_condition=AutomationCondition.eager(),
                    )
                ],
            )
        ]
    )
