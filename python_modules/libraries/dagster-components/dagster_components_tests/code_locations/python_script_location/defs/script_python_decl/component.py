from dagster_components import ComponentLoadContext
from dagster_components.components.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionComponent,
    PipesSubprocessScriptCollectionModel,
    PipesSubprocessScriptModel,
)
from dagster_components.core.component import component
from dagster_components.resolved.core_models import AssetSpecModel


@component
def load(context: ComponentLoadContext) -> PipesSubprocessScriptCollectionComponent:
    attributes = PipesSubprocessScriptCollectionModel(
        scripts=[
            PipesSubprocessScriptModel(
                path="cool_script.py",
                assets=[
                    AssetSpecModel(
                        key="cool_script",
                        automation_condition="{{ automation_condition.eager() }}",
                    ),
                ],
            ),
        ]
    )
    return PipesSubprocessScriptCollectionComponent.load(attributes=attributes, context=context)
