from dagster import AssetSpec, AutomationCondition
from dagster.components import ComponentLoadContext, component
from dagster.components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScript,
    PipesSubprocessScriptCollectionComponent,
)


@component
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
