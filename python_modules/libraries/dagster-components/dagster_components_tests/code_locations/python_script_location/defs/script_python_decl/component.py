from dagster import AssetSpec, AutomationCondition
from dagster_components import ComponentLoadContext
from dagster_components.components.pipes_subprocess_script_collection import (
    PipesSubprocessScript,
    PipesSubprocessScriptCollectionComponent,
)
from dagster_components.core.component import component


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
